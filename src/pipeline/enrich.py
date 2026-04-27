import pandas as pd
import time
import psutil
import os
from langdetect import detect, DetectorFactory
from loguru import logger
import argparse
from transformers import pipeline

# Fixer le seed pour la reproductibilité
DetectorFactory.seed = 42

_sentiment_pipeline = None

def get_sentiment_analyzer():
    """Lazy loading du pipeline de sentiment pour économiser de la RAM si non utilisé."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Chargement du modèle de sentiment (cmarkea/distilcamembert-base-sentiment)...")
        _sentiment_pipeline = pipeline("sentiment-analysis", model="cmarkea/distilcamembert-base-sentiment")
    return _sentiment_pipeline

def enrich_language(df: pd.DataFrame, text_column: str = "input_text") -> pd.DataFrame:
    """
    Enrichit le DataFrame avec la langue détectée.
    """
    logger.info(f"Déclenchement de la détection de langue sur la colonne '{text_column}'...")

    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)

    def _detect(text):
        try:
            if pd.isna(text) or len(str(text).strip()) < 3:
                return "unknown"
            return detect(str(text))
        except Exception:
            return "error"

    df["langue"] = df[text_column].apply(_detect)

    end_time = time.time()
    end_mem = process.memory_info().rss / (1024 * 1024)

    duration = end_time - start_time
    avg_time = (duration / len(df)) * 1000 if len(df) > 0 else 0

    logger.success(f"Détection terminée en {duration:.2f}s ({avg_time:.2f}ms/ligne)")
    logger.info(f"Consommation RAM : +{end_mem - start_mem:.2f} MB (Total: {end_mem:.2f} MB)")

    return df

def enrich_sentiment(df: pd.DataFrame, text_column: str = "input_text") -> pd.DataFrame:
    """
    Enrichit le DataFrame avec le sentiment détecté.
    """
    logger.info(f"Déclenchement de l'analyse de sentiment sur la colonne '{text_column}'...")

    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)

    analyzer = get_sentiment_analyzer()

    def _analyze(text):
        try:
            if pd.isna(text) or len(str(text).strip()) < 5:
                return "neutral"
            # On tronque à 512 tokens pour éviter les erreurs du modèle
            res = analyzer(str(text)[:512])[0]
            return res['label']
        except Exception as e:
            logger.warning(f"Erreur sur une ligne : {e}")
            return "error"

    df["sentiment"] = df[text_column].apply(_analyze)

    end_time = time.time()
    end_mem = process.memory_info().rss / (1024 * 1024)

    duration = end_time - start_time
    avg_time = (duration / len(df)) * 1000 if len(df) > 0 else 0

    logger.success(f"Analyse terminée en {duration:.2f}s ({avg_time:.2f}ms/ligne)")
    logger.info(f"Consommation RAM : +{end_mem - start_mem:.2f} MB (Total: {end_mem:.2f} MB)")

    return df

def main():
    parser = argparse.ArgumentParser(description="Module d'enrichissement de données FastIA")
    parser.add_argument("--field", choices=["language", "sentiment"], default="language", help="Champ à enrichir")
    parser.add_argument("--input", type=str, required=True, help="Fichier JSONL en entrée")
    parser.add_argument("--output", type=str, required=True, help="Fichier JSONL en sortie")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Fichier d'entrée introuvable : {args.input}")
        return

    logger.info(f"Chargement des données depuis {args.input}...")
    df = pd.read_json(args.input, lines=True)

    # Mapper 'input' vers 'input_text' si nécessaire (compatibilité v1/v2)
    text_col = "input" if "input" in df.columns else "input_text"

    if args.field == "language":
        df = enrich_language(df, text_column=text_col)
    elif args.field == "sentiment":
        df = enrich_sentiment(df, text_column=text_col)

    logger.info(f"Sauvegarde des données enrichies vers {args.output}...")
    df.to_json(args.output, orient="records", lines=True, force_ascii=False)
    logger.success("Traitement terminé.")

if __name__ == "__main__":
    main()
