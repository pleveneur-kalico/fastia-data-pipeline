import pandas as pd
import sqlalchemy
from loguru import logger
from pathlib import Path

from urllib.parse import quote_plus

def get_engine(user="fastia", password="fastia@pl", host="localhost", db="fastia_db"):
    encoded_password = quote_plus(password)
    url = f"mysql+pymysql://{user}:{encoded_password}@{host}/{db}"
    return sqlalchemy.create_engine(url)

from sqlalchemy.dialects.mysql import insert as mysql_insert
import json

def load_to_mysql(df: pd.DataFrame, version: str):
    """
    Charge un DataFrame dans la table 'demandes' de MySQL avec gestion d'idempotence.
    """
    engine = get_engine()
    metadata = sqlalchemy.MetaData()
    demandes = sqlalchemy.Table(
        "demandes", metadata,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column("input_text", sqlalchemy.Text),
        sqlalchemy.Column("input_raw", sqlalchemy.Text),
        sqlalchemy.Column("categorie", sqlalchemy.String(50)),
        sqlalchemy.Column("priorite", sqlalchemy.String(20)),
        sqlalchemy.Column("reponse_suggeree", sqlalchemy.Text),
        sqlalchemy.Column("source", sqlalchemy.String(30)),
        sqlalchemy.Column("canal", sqlalchemy.String(30)),
        sqlalchemy.Column("langue", sqlalchemy.String(10)),
        sqlalchemy.Column("received_at", sqlalchemy.DateTime),
        sqlalchemy.Column("sender", sqlalchemy.String(255)),
        sqlalchemy.Column("external_id", sqlalchemy.String(255)),
        sqlalchemy.Column("canal_metadata", sqlalchemy.JSON),
        sqlalchemy.Column("dedup_status", sqlalchemy.String(30)),
        sqlalchemy.Column("dataset_version", sqlalchemy.String(20)),
    )

    # Préparation du DataFrame
    db_df = df.copy()
    if "input" in db_df.columns:
        db_df = db_df.rename(columns={"input": "input_text"})

    if "source" not in db_df.columns:
        db_df["source"] = "original"

    db_df["dataset_version"] = version

    # Liste des colonnes cibles
    sql_columns = [
        "input_text", "input_raw", "categorie", "priorite",
        "reponse_suggeree", "source", "canal", "langue",
        "received_at", "sender", "external_id", "canal_metadata", "dedup_status", "dataset_version"
    ]

    for col in sql_columns:
        if col not in db_df.columns:
            db_df[col] = None

    # Conversion canal_metadata en dict si c'est une string JSON (cas rare)
    if "canal_metadata" in db_df.columns:
        db_df["canal_metadata"] = db_df["canal_metadata"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )

    records = db_df[sql_columns].to_dict(orient='records')

    try:
        logger.info(f"Chargement de {len(records)} lignes dans MySQL (version {version})...")

        with engine.begin() as conn:
            for record in records:
                stmt = mysql_insert(demandes).values(record)
                # Gestion de l'idempotence sur (canal, external_id)
                # Si le canal_metadata change, on met à jour
                update_dict = {
                    "input_text": stmt.inserted.input_text,
                    "received_at": stmt.inserted.received_at,
                    "dedup_status": stmt.inserted.dedup_status
                }
                if record.get("canal_metadata"):
                     update_dict["canal_metadata"] = stmt.inserted.canal_metadata

                on_dup = stmt.on_duplicate_key_update(**update_dict)
                conn.execute(on_dup)

        logger.info("Chargement terminé avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du chargement MySQL : {e}")
        raise

if __name__ == "__main__":
    # Test
    df_test = pd.DataFrame([
        {"input": "Test SQL", "categorie": "Support technique", "priorite": "normale", "source": "original"}
    ])
    load_to_mysql(df_test, "v1.test")
