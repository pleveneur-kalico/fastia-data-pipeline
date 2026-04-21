import json
import re
import hashlib
from collections import Counter
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import spacy

sns.set_theme(style="whitegrid")
pd.set_option("display.max_colwidth", 120)

print("Imports OK")


DATASET_PATH = Path("data/raw/dataset_fastia_module1v2.jsonl")

CATEGORIES_ATTENDUES = [
    "Support technique",
    "Demande commerciale",
    "Demande de transformation",
    "Réclamation",
    "Information générale",
]

PRIORITES_ATTENDUES = ["haute", "normale"]



## 1 - CHARGEMENT ET APLATISSEMENT
print("========== 1 - CHARGEMENT ET APLATISSEMENT ==========")
def load_jsonl(path: Path) -> pd.DataFrame:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append({
                "input": obj.get("input", ""),
                "categorie": obj.get("output", {}).get("categorie", ""),
                "priorite": obj.get("output", {}).get("priorite", ""),
                "reponse_suggeree": obj.get("output", {}).get("reponse_suggeree", ""),
            })
    return pd.DataFrame(rows)


df = load_jsonl(DATASET_PATH)
print(f"Nombre d'exemples : {len(df)}")
df.head()



## 2 - AUDIT QUANTITATIF
print("")
print("")
print("========== 2 - AUDIT QUANTITATIF ==========")
cat_counts = df["categorie"].value_counts()
print(cat_counts)

fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(x=cat_counts.values, y=cat_counts.index, ax=ax, color="#2563a8")
ax.set_xlabel("Nombre d'exemples")
ax.set_ylabel("")
ax.set_title("Distribution des catégories")
plt.tight_layout()



## 2.2 - DISTRIBUTION DES PRIORITES (globale et par catégorie)

# 1. Distribution globale
prio_counts = df["priorite"].value_counts()
print("\nDistribution globale des priorités :")
print(prio_counts)

plt.figure(figsize=(6, 4))
sns.countplot(data=df, x="priorite", order=PRIORITES_ATTENDUES, palette="viridis")
plt.title("Distribution globale des priorités")
plt.xlabel("Priorité")
plt.ylabel("Nombre d'exemples")
plt.tight_layout()
plt.show()

# 2. Crosstab + heatmap
# On crée un tableau croisé (fréquences)
ct = pd.crosstab(df["categorie"], df["priorite"])

# On s'assure que toutes les colonnes attendues sont présentes (même si à 0)
for p in PRIORITES_ATTENDUES:
    if p not in ct.columns:
        ct[p] = 0

print("\nTableau croisé Catégorie x Priorité :")
print(ct)

plt.figure(figsize=(10, 6))
sns.heatmap(ct, annot=True, fmt="d", cmap="YlGnBu", cbar=True)
plt.title("Matrice de répartition : Catégorie vs Priorité")
plt.xlabel("Priorité")
plt.ylabel("Catégorie")
plt.tight_layout()
plt.show()

# Question à consigner : certaines combinaisons sont-elles absentes ou sous-représentées ?
# Réponse              : Priotié haute moins représentée, catégories "commercial, transformation, réclamation" sous représentées"



## 2.3 - DISTRIBUTION DES LONGUEURS
print("")
print("")
print("========== 2.3 - DISTRIBUTION DES LONGUEURS ==========")
df["len_input_chars"] = df["input"].str.len()
df["len_reponse_chars"] = df["reponse_suggeree"].str.len()
df["len_input_words"] = df["input"].str.split().map(len)

print(df[["len_input_chars", "len_input_words", "len_reponse_chars"]].describe().round(1))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(df["len_input_chars"], bins=20, ax=axes[0], color="#2563a8")
axes[0].set_title("Longueur des demandes (caractères)")
sns.histplot(df["len_reponse_chars"], bins=20, ax=axes[1], color="#6d28d9")
axes[1].set_title("Longueur des réponses (caractères)")
plt.tight_layout()

# Objectif : comparer les longueurs par catégorie

# 1. Boxplot de la longueur des demandes par catégorie
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x="len_input_chars", y="categorie", palette="viridis")
plt.title("Dispersion de la longueur des demandes par catégorie")
plt.xlabel("Nombre de caractères (input)")
plt.ylabel("")
plt.tight_layout()
plt.show()

# 2. Analyse de la dispersion
# On calcule l'écart-type ou l'étendue pour voir qui varie le plus
stats_dispersion = df.groupby("categorie")["len_input_chars"].agg(["mean", "std", "min", "max"])
print("\nStatistiques de longueur par catégorie :")
print(stats_dispersion.round(1))

# Question à consigner : y a-t-il une catégorie où la longueur prédit mieux que le contenu ?
# (C'est un indice de biais que le modèle pourrait apprendre.)
# Réponse : Oui : les informations générales car la longueur mini et maxi vont donner un indice
#           sur le fait que une question entre 68 et 92 caractères sont des informations générales



## 2.4 - DOUBLONS
print("")
print("")
print("========== 2.4 - DOUBLONS ==========")
def normalize_for_hash(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

df["input_hash"] = df["input"].map(lambda s: hashlib.md5(normalize_for_hash(s).encode()).hexdigest())

exact_dups = df.duplicated(subset=["input"], keep=False).sum()
normalized_dups = df.duplicated(subset=["input_hash"], keep=False).sum()

print(f"Doublons exacts sur input   : {exact_dups}")
print(f"Doublons après normalisation: {normalized_dups}")



## 2.5 - VALEURS MANQUANTES ET HORS SCHEMA
print("")
print("")
print("========== 2.5 - VALEURS MANQUANTITES ET HORS SCHEMA ==========")
# Objectif : vérifier le respect du schéma
# 1. Input vide ou trop court
mask_input_absent = df["input"].str.strip().isna() | (df["input"].str.strip() == "")
mask_input_court = df["input"].str.len() < 10
count_input_invalid = (mask_input_absent | mask_input_court).sum()

# 2. Catégories hors schéma
count_cat_hors_schema = (~df["categorie"].isin(CATEGORIES_ATTENDUES)).sum()

# 3. Priorités hors schéma
count_prio_hors_schema = (~df["priorite"].isin(PRIORITES_ATTENDUES)).sum()

# 4. Réponse suggérée vide
count_reponse_vide = (df["reponse_suggeree"].str.strip() == "").sum()

# Création du tableau récapitulatif
data_qualite = {
    "Anomalie": [
        "Input vide ou trop court (<10 chars)",
        "Catégorie hors nomenclature",
        "Priorité hors nomenclature",
        "Réponse suggérée absente"
    ],
    "Nombre de lignes": [
        count_input_invalid,
        count_cat_hors_schema,
        count_prio_hors_schema,
        count_reponse_vide
    ]
}

df_qualite = pd.DataFrame(data_qualite)
print("\nTableau récapitulatif de la qualité des données :")
print(df_qualite)

# Affichage des valeurs hors nomenclature pour investigation (si elles existent)
if count_cat_hors_schema > 0:
    print("\nCatégories inconnues détectées :", df.loc[~df["categorie"].isin(CATEGORIES_ATTENDUES), "categorie"].unique())

if count_prio_hors_schema > 0:
    print("Priorités inconnues détectées :", df.loc[~df["priorite"].isin(PRIORITES_ATTENDUES), "priorite"].unique())

# Consigner les résultats dans un tableau récapitulatif.
#                                Anomalie  Nombre de lignes
# 0  Input vide ou trop court (<10 chars)                 0
# 1           Catégorie hors nomenclature                 0
# 2            Priorité hors nomenclature                 0
# 3              Réponse suggérée absente                 0



## 3 - AUDIT QUALITATIF
print("")
print("")
print("========== 3 - AUDIT QUALITATIF ==========")
echantillon = (
    df.groupby("categorie", group_keys=False)
      .apply(lambda g: g.sample(min(4, len(g)), random_state=42))
      .reset_index(drop=True)
)

for _, row in echantillon.iterrows():
    print(f"[{row.categorie} | {row.priorite}]")
    print(f"  input  : {row.input}")
    print(f"  réponse: {row.reponse_suggeree}")
    print()

# Objectif : noter pour chacun des 20 exemples
# 1. Création de la structure du DataFrame de revue
# On utilise l'index de l'échantillon pour pouvoir s'y référer
revue_data = {
    "idx": echantillon.index,
    "categorie_actuelle": echantillon["categorie"],
    "priorite_actuelle": echantillon["priorite"],
    "categorie_ok": True,  # Valeur par défaut à modifier durant la revue
    "priorite_ok": True,   # Valeur par défaut à modifier durant la revue
    "reponse_ok": True,    # Valeur par défaut à modifier durant la revue
    "contient_pii": False, # PII = Personal Identifiable Information (Données persos)
    "commentaire": ""
}

df_revue = pd.DataFrame(revue_data)

# 2. Sauvegarde du fichier pour la revue manuelle
output_path = Path("docs/revue_qualitative.csv")
output_path.parent.mkdir(parents=True, exist_ok=True) # Crée le dossier docs s'il n'existe pas

df_revue.to_csv(output_path, index=False, encoding="utf-8-sig", sep=";")

print(f"Fichier de revue généré : {output_path}")
print("Action requise : Ouvrez ce fichier et validez chaque ligne par rapport aux prints ci-dessus.")



## 4 - REPERAGE DES DONNEES POTENTIELLEMENT SENSIBLES
print("")
print("")
print("========== 4 - REPARAGE DES DONNEES POTENTIELLEMENT SENSIBLES ==========")
PII_PATTERNS = {
    "email":     re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"),
    "telephone": re.compile(r"(?:(?:\+33|0)\s?[1-9])(?:[\s.-]?\d{2}){4}"),
    "url":       re.compile(r"https?://\S+"),
    "ip":        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

pii_counts = {k: df["input"].str.contains(p, regex=True).sum() for k, p in PII_PATTERNS.items()}
pii_counts["total_lignes"] = len(df)
print(pii_counts)

# Objectif : la regex ne détecte pas les noms propres. Noter dans la revue qualitative
# les exemples où des prénoms ou noms apparaissent dans input ou reponse_suggeree.
#
# Optionnel : tester spaCy (fr_core_news_sm) pour une détection NER plus fine.

# Chargement du modèle français (nécessite : python -m spacy download fr_core_news_sm)
try:
    #nlp = spacy.load("fr_core_news_sm")
    nlp = spacy.load("fr_core_news_lg")     # Ce dictionnaire est plus précis que le "sm"
    print("Modèle spaCy chargé avec succès.")

    def detect_names(text):
        doc = nlp(text)
        # On cherche les entités de type 'PER' (Personnes)
        names = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        return names

    # Test sur un petit échantillon
    df["noms_detectes"] = df["input"].apply(detect_names)
    count_with_names = df["noms_detectes"].map(len).gt(0).sum()
    
    print(f"Lignes avec noms propres potentiels (via NER) : {count_with_names}")
    if count_with_names > 0:
        print("Exemples de noms trouvés :", df[df["noms_detectes"].map(len) > 0]["noms_detectes"].iloc[0:5].tolist())

except Exception as e:
    print(f"spaCy non configuré ou erreur : {e}")
    print("Poursuivez avec la détection manuelle dans la revue qualitative.")
    
 
 
## 5 - Synthèse
print("")
print("")
print("=============== 5 - SYNTHESE ================")
# Objectif : produire un dictionnaire de synthèse qui sera cité dans docs/audit_v1.md
#
# Remplir audit_synthese avec les chiffres obtenus plus haut :
## 5 - Synthèse

# Objectif : produire un dictionnaire de synthèse qui sera cité dans docs/audit_v1.md
# Remplissage avec les chiffres obtenus lors de l'exécution :

audit_synthese = {
    "n_exemples": 86,
    "distribution_categories": {
        "Support technique": 20,
        "Information générale": 20,
        "Demande commerciale": 16,
        "Demande de transformation": 15,
        "Réclamation": 15
    },
    "distribution_priorites": {
        "normale": 62,
        "haute": 24
    },
    "doublons_exacts": 0,
    "doublons_normalises": 0,
    "len_input_moy": 96.3,
    "len_input_med": 94.0,
    "lignes_avec_pii": 0,  # Confirmé manuellement après analyse des faux positifs de spaCy
    "risques_prioritaires": [
        "Faible volume de données (86 exemples) : nécessite une approche par prompt engineering ou fine-tuning léger.",
        "Biais de longueur marqué : les 'Informations générales' sont significativement plus courtes (moy. 77) que les 'Réclamations' (moy. 107).",
        "Déséquilibre des priorités : la catégorie 'Information générale' ne contient aucun exemple en priorité 'haute' (risque de spécialisation excessive).",
        "Risque de 'Faux Positifs' NER : le modèle de détection de noms confond les verbes de début de phrase ('Pouvez') avec des PII."
    ],
}

import json as _json
from pathlib import Path

# Création du dossier et écriture du fichier
Path("docs").mkdir(exist_ok=True)
Path("docs/audit_synthese.json").write_text(
    _json.dumps(audit_synthese, ensure_ascii=False, indent=2), 
    encoding="utf-8"
)

print("")
print("Synthèse écrite dans docs/audit_synthese.json")


