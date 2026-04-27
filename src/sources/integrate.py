from pathlib import Path
from datetime import datetime
from loguru import logger
import pandas as pd

from src.sources.email_loader import load_mbox
from src.sources.web_loader import load_web
from src.sources.chat_loader import load_chat
from src.sources.dedup import mark_cross_channel_duplicates
from src.pipeline.clean import drop_duplicates, normalize_text, handle_missing
from src.pipeline.anonymize import anonymize_text
from src.storage.load import load_to_mysql


def pydantic_to_df(items):
    """Convertit une liste de modèles Pydantic en DataFrame pandas."""
    data = []
    for item in items:
        d = item.model_dump()
        if hasattr(item, 'dedup_status'):
            d['dedup_status'] = item.dedup_status
        data.append(d)

    df = pd.DataFrame(data)
    if "body" in df.columns:
        df = df.rename(columns={"body": "input"})
    return df


def ingest(source: str, path: str):
    """
    Point d'entrée unique pour l'ingestion de toute source.
    """
    start_time = datetime.now()
    logger.info(f"Début ingestion {source} : {path}")

    path_obj = Path(path)
    if not path_obj.exists():
        logger.error(f"Fichier non trouvé : {path}")
        return

    # 1. Dispatch vers le loader adéquat
    if source == "email":
        items = list(load_mbox(path_obj))
    elif source == "web":
        items = list(load_web(path_obj))
    elif source == "chat":
        items = list(load_chat(path_obj))
    else:
        logger.error(f"Source inconnue : {source}")
        return

    if not items:
        logger.warning(f"Aucune donnée extraite de {path}")
        return

    initial_count = len(items)

    # 2. Déduplication Cross-Canal (avant conversion en DF pour garder les objets)
    items = mark_cross_channel_duplicates(items)

    # Conversion en DataFrame pour réutiliser la pipeline M2
    df = pydantic_to_df(items)

    # 3. Nettoyage (standard pipeline M2)
    df = drop_duplicates(df)
    df = normalize_text(df)
    df = handle_missing(df)

    # 4. Anonymisation
    df = anonymize_text(df)

    # Valeurs par défaut pour les colonnes obligatoires
    if "categorie" not in df.columns:
        df["categorie"] = "A définir"
    if "priorite" not in df.columns:
        df["priorite"] = "A définir"

    # 5. Stockage SQL avec idempotence
    version = f"ingest.{datetime.now().strftime('%Y%m%d')}"
    load_to_mysql(df, version)

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Ingestion {source} terminée : {len(df)}/{initial_count} traités en {duration:.2f}s")
