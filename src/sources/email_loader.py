import mailbox
import re
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterator, Literal, Optional

from bs4 import BeautifulSoup
from loguru import logger
from pydantic import BaseModel, Field


class RawDemande(BaseModel):
    """Modèle Pydantic pour une demande brute extraite d'un email."""
    canal: Literal["email", "web", "chat"] = "email"
    external_id: str
    received_at: datetime
    sender: Optional[str] = None
    subject: Optional[str] = None
    body: str
    canal_metadata: dict = Field(default_factory=dict)
    dedup_status: str = "original"


def decode_mime_header(header_value) -> Optional[str]:
    """Décode les en-têtes email (RFC 2047)."""
    if not header_value:
        return None
    # If it's already a string (and not a Header object), return it
    if isinstance(header_value, str):
        # Even if it's a string, it might contain encoded parts
        try:
            decoded_parts = decode_header(header_value)
            header_text = ""
            for content, encoding in decoded_parts:
                if isinstance(content, bytes):
                    header_text += content.decode(encoding or "utf-8", errors="replace")
                else:
                    header_text += str(content)
            return header_text
        except Exception:
            return header_value

    # Handle Header objects
    try:
        return str(header_value)
    except Exception as e:
        logger.warning(f"Erreur lors de la conversion de l'en-tête en string : {e}")
        return str(header_value)


def strip_quoted_text(text: str) -> str:
    """
    Supprime les citations (lignes commençant par '>') et les blocs de signature.
    """
    # 1. Supprimer les lignes de citation (commençant par >)
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        if not line.strip().startswith(">"):
            clean_lines.append(line)

    content = "\n".join(clean_lines)

    # 2. Supprimer les blocs de signature standards (-- \n)
    # On cherche le dernier séparateur de signature
    sig_pattern = re.compile(r"\n-- \s*\n.*", re.DOTALL)
    content = sig_pattern.sub("", content)

    # 3. Supprimer les "Sent from my..." ou "Envoyé de mon..."
    content = re.sub(r"\n?(?:Sent from|Envoyé de) mon (?:iPhone|Android|Samsung|iPad).*", "", content, flags=re.IGNORECASE)

    return content.strip()


def get_email_body(message: mailbox.mboxMessage) -> Optional[str]:
    """Extrait le corps de l'email (préfère text/plain, fallback HTML)."""
    body = None

    if message.is_multipart():
        # Parcourir les parties pour trouver du texte brut
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break

        # Fallback HTML si pas de text/plain
        if not body:
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        body = BeautifulSoup(html, "html.parser").get_text(separator="\n")
                        break
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            if message.get_content_type() == "text/html":
                html = payload.decode(charset, errors="replace")
                body = BeautifulSoup(html, "html.parser").get_text(separator="\n")
            else:
                body = payload.decode(charset, errors="replace")

    return body


def load_mbox(path: Path) -> Iterator[RawDemande]:
    """Itère sur les messages d'un fichier mbox et yield un RawDemande par mail."""
    if not path.exists():
        logger.error(f"Fichier non trouvé : {path}")
        return

    mbox = mailbox.mbox(str(path))

    for message in mbox:
        try:
            external_id = message.get("Message-ID")
            if not external_id:
                logger.warning("Message ignoré : Message-ID manquant")
                continue

            # Date
            date_str = message.get("Date")
            try:
                received_at = parsedate_to_datetime(date_str)
                # Ensure naive datetimes are handled if necessary,
                # but parsedate_to_datetime usually returns aware ones
                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=None)
            except (TypeError, ValueError, AttributeError):
                received_at = datetime.now()
                logger.warning(f"Date invalide pour {external_id}, utilisation de 'now'")

            # Headers
            sender = decode_mime_header(message.get("From"))
            subject = decode_mime_header(message.get("Subject"))

            # Body
            raw_body = get_email_body(message)
            if not raw_body or not raw_body.strip():
                logger.warning(f"Message {external_id} ignoré : corps vide")
                continue

            clean_body = strip_quoted_text(raw_body)

            # Metadata
            canal_metadata = {
                "subject": subject,
                "in_reply_to": message.get("In-Reply-To"),
                "references": message.get("References"),
            }

            yield RawDemande(
                canal="email",
                external_id=external_id,
                received_at=received_at,
                sender=sender,
                subject=subject,
                body=clean_body,
                canal_metadata={k: v for k, v in canal_metadata.items() if v}
            )

        except Exception as e:
            logger.exception(f"Erreur lors du traitement d'un message : {e}")
