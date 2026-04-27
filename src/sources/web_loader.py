import json
from datetime import datetime
from pathlib import Path
from typing import Iterator, Literal, Optional

from loguru import logger
from pydantic import BaseModel, Field


class RawDemande(BaseModel):
    """Modèle Pydantic pour une demande brute extraite d'une source."""
    canal: Literal["email", "web", "chat"]
    external_id: str
    received_at: datetime
    sender: Optional[str] = None
    subject: Optional[str] = None
    body: str
    canal_metadata: dict = Field(default_factory=dict)
    dedup_status: str = "original"


def load_web(path: Path) -> Iterator[RawDemande]:
    """Itère sur les soumissions d'un fichier JSONL web et yield un RawDemande par ligne."""
    if not path.exists():
        logger.error(f"Fichier non trouvé : {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)

                external_id = data.get("submission_id")
                received_at_str = data.get("submitted_at")
                form = data.get("form", {})

                if not external_id or not received_at_str:
                    logger.warning(f"Ligne {line_idx} ignorée : ID ou date manquante")
                    continue

                # Conversion date ISO (ex: 2026-04-06T10:14:22Z)
                # On retire le Z pour datetime.fromisoformat si besoin,
                # mais python 3.11+ le gère.
                received_at = datetime.fromisoformat(received_at_str.replace("Z", "+00:00"))

                sender = form.get("email")
                subject = form.get("subject")
                body = form.get("message", "")

                if not body.strip():
                    logger.warning(f"Ligne {line_idx} ignorée : message vide")
                    continue

                # Fallback Sujet : Si vide, extraire les 60 premiers caractères du message
                if not subject or not subject.strip():
                    subject = body[:60] + ("..." if len(body) > 60 else "")

                # Metadata
                canal_metadata = {
                    "ip_country": data.get("ip_country"),
                    "user_agent": data.get("user_agent"),
                }

                yield RawDemande(
                    canal="web",
                    external_id=external_id,
                    received_at=received_at,
                    sender=sender,
                    subject=subject,
                    body=body.strip(),
                    canal_metadata={k: v for k, v in canal_metadata.items() if v}
                )

            except json.JSONDecodeError:
                logger.error(f"Erreur de décodage JSON ligne {line_idx}")
            except Exception as e:
                logger.exception(f"Erreur lors du traitement ligne {line_idx} : {e}")
