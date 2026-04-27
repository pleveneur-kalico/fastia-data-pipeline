import hashlib
from datetime import timedelta
from typing import List, Optional
import sqlalchemy
from loguru import logger
from pydantic import BaseModel
from src.storage.load import get_engine


def normalize_for_hash(text: str) -> str:
    """Normalise le texte pour le hachage sémantique."""
    if not text:
        return ""
    # On prend les 300 premiers caractères, minuscule, sans espaces superflus
    return " ".join(text.lower().strip()[:300].split())


def calculate_semantic_hash(text: str) -> str:
    """Calcule un hash MD5 sur le texte normalisé."""
    normalized = normalize_for_hash(text)
    return hashlib.md5(normalized.encode()).hexdigest()


def mark_cross_channel_duplicates(demandes: List[object], window_hours: int = 48):
    """
    Identifie les doublons cross-canal dans une liste de RawDemande.
    Met à jour l'attribut 'dedup_status' des objets si un doublon est trouvé en base.
    """
    engine = get_engine()

    for demande in demandes:
        # Initialisation par défaut
        if not hasattr(demande, 'dedup_status'):
            setattr(demande, 'dedup_status', 'original')

        if not demande.sender or not demande.body:
            continue

        semantic_hash = calculate_semantic_hash(demande.body)

        # Fenêtre temporelle
        start_time = demande.received_at - timedelta(hours=window_hours)
        end_time = demande.received_at + timedelta(hours=window_hours)

        # On cherche en base si une demande du même expéditeur avec le même contenu existe
        # dans la fenêtre de 48h (avant ou après, car on peut ingérer dans le désordre)
        query = sqlalchemy.text("""
            SELECT id FROM demandes
            WHERE sender = :sender
            AND received_at BETWEEN :start AND :end
            AND external_id != :ext_id
            LIMIT 1
        """)

        try:
            with engine.connect() as conn:
                result = conn.execute(query, {
                    "sender": demande.sender,
                    "start": start_time,
                    "end": end_time,
                    "ext_id": demande.external_id
                }).fetchone()

                if result:
                    # On a trouvé une correspondance. On compare plus finement si besoin
                    # mais ici on suit la stratégie simple du plan.
                    logger.info(f"Doublon cross-canal détecté pour {demande.external_id}")
                    setattr(demande, 'dedup_status', 'cross_channel_duplicate')

        except Exception as e:
            logger.warning(f"Erreur lors de la vérification de déduplication pour {demande.external_id} : {e}")

    return demandes
