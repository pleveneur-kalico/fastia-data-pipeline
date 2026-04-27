import csv
from datetime import datetime
from pathlib import Path
from typing import Iterator, Literal, Optional, Dict, List

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


def load_chat(path: Path) -> Iterator[RawDemande]:
    """Charge les sessions de chat depuis un CSV et yield un RawDemande par session."""
    if not path.exists():
        logger.error(f"Fichier non trouvé : {path}")
        return

    sessions: Dict[str, Dict] = {}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            session_id = row.get("session_id")
            if not session_id:
                continue

            if session_id not in sessions:
                sessions[session_id] = {
                    "messages": [],
                    "first_timestamp": row.get("timestamp"),
                }

            sessions[session_id]["messages"].append({
                "timestamp": row.get("timestamp"),
                "role": row.get("role"),
                "message": row.get("message")
            })

    for session_id, session_data in sessions.items():
        try:
            # Reconstruction du body (concaténation visitor)
            visitor_messages = [
                m["message"] for m in session_data["messages"]
                if m["role"] == "visitor" and m["message"]
            ]

            if not visitor_messages:
                logger.debug(f"Session {session_id} ignorée : aucun message visiteur")
                continue

            body = " ".join(visitor_messages)

            # Transcript complet pour metadata
            transcript = [
                f"[{m['role']}] {m['message']}" for m in session_data["messages"]
            ]

            # Date de début
            received_at_str = session_data["first_timestamp"]
            received_at = datetime.fromisoformat(received_at_str.replace("Z", "+00:00"))

            # Sujet : Extraire les 60 premiers caractères du premier message visiteur
            first_msg = visitor_messages[0]
            subject = first_msg[:60] + ("..." if len(first_msg) > 60 else "")

            yield RawDemande(
                canal="chat",
                external_id=session_id,
                received_at=received_at,
                sender="Anonyme (Chat)",
                subject=subject,
                body=body.strip(),
                canal_metadata={
                    "transcript_complet": "\n".join(transcript)
                }
            )

        except Exception as e:
            logger.exception(f"Erreur lors du traitement de la session {session_id} : {e}")
