"""
Collecte rapide des emails support FastIA depuis un fichier mbox.
Version corrigée (Brief 1 Module 3).
"""

import mailbox
import os
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from email.header import decode_header
import pymysql
from loguru import logger

# Configuration DB mise à jour pour MySQL
DB_URL = os.environ.get(
    "FASTIA_DB_URL",
    "mysql+pymysql://fastia:fastia@localhost/fastia_db",
)

def get_db_connection():
    # Parsing simple de l'URL pour pymysql
    # mysql+pymysql://user:pass@host/db
    import re
    match = re.match(r"mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/(.+)", DB_URL)
    if not match:
        # Fallback pour les tests ou config simple
        return pymysql.connect(host="localhost", user="fastia", password="fastia", database="fastia_db")

    user, password, host, db = match.groups()
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def decode_mime_header(header_value):
    """Décode les en-têtes email (RFC 2047)."""
    if not header_value:
        return ""
    try:
        decoded_parts = decode_header(str(header_value))
        header_text = ""
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                header_text += content.decode(encoding or "utf-8", errors="replace")
            else:
                header_text += str(content)
        return header_text
    except Exception:
        return str(header_value)

def extract_body(msg):
    """Recupere le corps texte d'un message avec gestion robuste des encodages."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return ""

    payload = msg.get_payload(decode=True)
    if payload:
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return ""

def collect(mbox_path):
    if not os.path.exists(mbox_path):
        logger.error(f"Fichier mbox non trouvé : {mbox_path}")
        return

    box = mailbox.mbox(mbox_path)
    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    for msg in box:
        try:
            message_id = (msg.get("Message-ID") or "").strip()
            if not message_id:
                skipped += 1
                continue

            sender = decode_mime_header(msg.get("From", ""))
            subject = decode_mime_header(msg.get("Subject", ""))
            date_raw = msg.get("Date", "")

            try:
                # Correction BUG 3: Conservation de la Timezone
                received_at = parsedate_to_datetime(date_raw)
            except Exception:
                received_at = datetime.now()

            # Correction BUG 1: Gestion des encodages (via errors="replace" dans extract_body)
            body = extract_body(msg)
            if not body.strip():
                skipped += 1
                continue

            # Correction BUG 2: Idempotence via ON DUPLICATE KEY UPDATE
            # On ajoute aussi canal_metadata et dataset_version pour match le schéma M2/M3
            sql = """
                INSERT INTO demandes
                    (canal, external_id, received_at, input_text, input_raw, source, categorie, priorite, dataset_version)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    input_text = VALUES(input_text),
                    received_at = VALUES(received_at)
            """
            cur.execute(
                sql,
                ("email", message_id, received_at, body, body, "original", "A définir", "A définir", "v2-legacy")
            )
            inserted += 1
        except Exception as e:
            logger.error(f"Erreur sur un message : {e}")
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Processed: {inserted}, skipped: {skipped}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python legacy_collect.py <path/to/file.mbox>")
        sys.exit(1)
    collect(sys.argv[1])
