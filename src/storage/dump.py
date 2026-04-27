import pandas as pd
from src.storage.load import get_engine
from loguru import logger

def dump_from_mysql(output_path: str, version: str = None):
    """
    Exporte une version spécifique du dataset (ou tout le dataset) depuis MySQL vers un fichier JSONL.
    """
    engine = get_engine()
    if version:
        query = f"SELECT * FROM demandes WHERE dataset_version = '{version}'"
        logger.info(f"Extraction de la version {version} depuis MySQL...")
    else:
        query = "SELECT * FROM demandes"
        logger.info("Extraction de toutes les demandes depuis MySQL...")

    try:
        df = pd.read_sql(query, con=engine)

        # Nettoyage pour export (retirer l'ID interne et created_at pour le fine-tuning)
        cols_to_export = [col for col in ["input_text", "categorie", "priorite", "reponse_suggeree", "source", "canal", "dedup_status"] if col in df.columns]
        df_export = df[cols_to_export]
        if "input_text" in df_export.columns:
            df_export = df_export.rename(columns={"input_text": "input"})

        logger.info(f"Sauvegarde de {len(df_export)} lignes dans {output_path}")
        df_export.to_json(output_path, orient='records', lines=True, force_ascii=False)
        return df_export
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction MySQL : {e}")
        raise

if __name__ == "__main__":
    dump_from_mysql("v1.test", "data/processed/dump_test.jsonl")
