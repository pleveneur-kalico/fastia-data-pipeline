import json
import random
import httpx
import pandas as pd
from loguru import logger
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemini-3-flash-preview:cloud"

class Augmentor:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.original_df = df.copy()
        self.augmented_rows = []

    def call_llm(self, prompt: str) -> str:
        try:
            response = httpx.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }, timeout=30.0)
            
            if response.status_code == 200:
                return response.json().get("response", "").strip().strip('"')
            else:
                logger.error(f"Erreur Ollama: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception Ollama: {e}")
            return None

    def paraphrase_example(self, row: pd.Series) -> dict:
        prompt = f"""Tu es un assistant IA spécialisé dans la génération de données pour un service client.
        Voici une demande client originale : "{row['input']}"
        Elle appartient à la catégorie "{row['categorie']}" avec une priorité "{row['priorite']}".
        La réponse suggérée actuelle est : "{row['reponse_suggeree']}"

        Génère une variation (paraphrase) de cette demande et adapte légèrement la réponse si nécessaire.
        Contraintes :
        1. Garde la même intention, catégorie et priorité.
        2. Change le style (plus formel, plus court, ou plus détaillé).
        3. Réponds UNIQUEMENT au format JSON comme ceci : {{"input": "nouveau texte", "reponse_suggeree": "nouvelle réponse"}}
        """
        
        res_text = self.call_llm(prompt)
        if res_text:
            try:
                # Nettoyage sommaire si le LLM ajoute des balises ```json
                res_text = res_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(res_text)
                return {
                    "input": data.get("input", ""),
                    "categorie": row["categorie"],
                    "priorite": row["priorite"],
                    "reponse_suggeree": data.get("reponse_suggeree", ""),
                    "source": "synthetic"
                }
            except Exception as e:
                logger.warning(f"Erreur parsing JSON LLM: {e}")
        return None

    def generate_template_example(self, categorie: str, priorite: str) -> dict:
        templates = {
            "Information générale": [
                ("URGENT : Pouvez-vous me confirmer la conformité de vos serveurs avec la norme {norme} ?", 
                 "Nous vous confirmons que nos serveurs respectent la norme {norme}. Une attestation peut vous être envoyée par notre DPO."),
                ("ALERTE : Suite à l'incident sur {service}, quelles sont vos garanties de rétablissement ?",
                 "Nos équipes sont mobilisées pour rétablir {service}. Le délai de rétablissement garanti (GTR) est de 4 heures."),
                ("IMPORTANT : Je ne trouve pas votre politique de sécurité des données concernant {sujet}.",
                 "Notre politique de sécurité concernant {sujet} est disponible en annexe de votre contrat ou sur demande auprès de notre RSSI."),
                ("Bonjour, est-ce que FastIA est certifié {certification} pour ses opérations en Europe ?",
                 "Oui, FastIA détient la certification {certification}. Vous pouvez consulter nos certificats sur notre portail de confiance."),
                ("Question critique : Comment gérez-vous les accès privilégiés sur {plateforme} ?",
                 "La gestion des accès sur {plateforme} repose sur le principe du moindre privilège et une authentification forte (MFA).")
            ]
        }
        
        variables = {
            "norme": ["ISO 27001", "SOC2", "RGPD v2", "HIPAA"],
            "service": ["le stockage cloud", "l'API REST", "le portail client", "le moteur d'inférence"],
            "sujet": ["la rétention des logs", "le chiffrement au repos", "la sous-traitance", "l'IA générative"],
            "certification": ["HDS", "SecNumCloud", "ISO 22301", "ISO 9001"],
            "plateforme": ["la console d'administration", "les bases de données", "les clusters Kubernetes"]
        }
        
        if categorie in templates:
            t_input, t_output = random.choice(templates[categorie])
            
            # Remplissage
            input_text = t_input
            output_text = t_output
            for key, values in variables.items():
                val = random.choice(values)
                placeholder = "{" + key + "}"
                input_text = input_text.replace(placeholder, val)
                output_text = output_text.replace(placeholder, val)
                
            return {
                "input": input_text,
                "categorie": categorie,
                "priorite": priorite,
                "reponse_suggeree": output_text,
                "source": "synthetic"
            }
        return None

    def run(self, target_per_cat=100):
        logger.info(f"Démarrage de l'augmentation vers {target_per_cat} exemples par catégorie.")
        
        # S'assurer que le flag source existe
        if "source" not in self.df.columns:
            self.df["source"] = "original"
            
        categories = self.df["categorie"].unique()
        
        all_new_rows = []
        
        for cat in categories:
            cat_df = self.df[self.df["categorie"] == cat]
            current_count = len(cat_df)
            to_add = target_per_cat - current_count
            
            logger.info(f"Catégorie '{cat}': {current_count} existants, besoin de {to_add} nouveaux.")
            
            if to_add <= 0:
                continue
                
            # 1. Combler les manques critiques par gabarit (ex: Info Générale Haute)
            if cat == "Information générale":
                high_prio_count = len(cat_df[cat_df["priorite"] == "haute"])
                if high_prio_count < 40: # On vise au moins 40% de haute prio
                    for _ in range(40 - high_prio_count):
                        new_row = self.generate_template_example(cat, "haute")
                        if new_row:
                            all_new_rows.append(new_row)
                            to_add -= 1
            
            # 2. Le reste par paraphrase LLM
            # On cycle sur les exemples existants pour paraphraser
            idx = 0
            while to_add > 0:
                row = cat_df.iloc[idx % current_count]
                new_row = self.paraphrase_example(row)
                if new_row:
                    all_new_rows.append(new_row)
                    to_add -= 1
                    if len(all_new_rows) % 10 == 0:
                        logger.info(f"Progress: {len(all_new_rows)} exemples générés...")
                idx += 1
                
        new_df = pd.DataFrame(all_new_rows)
        final_df = pd.concat([self.df, new_df], ignore_index=True)
        
        logger.info(f"Augmentation terminée. Total: {len(final_df)} exemples.")
        return final_df

if __name__ == "__main__":
    # Test rapide
    df_test = pd.DataFrame([
        {"input": "Comment réinitialiser mon mot de passe ?", "categorie": "Support technique", "priorite": "normale", "reponse_suggeree": "Allez dans paramètres."},
        {"input": "Quelles sont vos certifs ?", "categorie": "Information générale", "priorite": "normale", "reponse_suggeree": "ISO 27001."}
    ])
    augmentor = Augmentor(df_test)
    # On teste avec un petit nombre pour ne pas consommer trop de temps/ressources
    df_result = augmentor.run(target_per_cat=5)
    print(df_result)
