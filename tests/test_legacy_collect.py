import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from src.sources.legacy_collect import extract_body, collect

def test_extract_body_non_utf8():
    # Simulation d'un message avec un encodage latin-1
    msg = MagicMock()
    msg.is_multipart.return_value = False
    # Contenu en Latin-1: "C'est l'été"
    payload = "C'est l'été".encode('latin-1')
    msg.get_payload.return_value = payload
    msg.get_content_charset.return_value = 'latin-1'

    body = extract_body(msg)
    assert body == "C'est l'été"

@patch('os.path.exists')
@patch('pymysql.connect')
@patch('mailbox.mbox')
def test_collect_idempotence(mock_mbox, mock_connect, mock_exists):
    mock_exists.return_value = True
    # Simulation d'un mbox avec 2 messages identiques
    mock_box = MagicMock()
    msg = MagicMock()
    msg.get.side_effect = lambda k, default=None: {
        "Message-ID": "<test-123>",
        "From": "test@example.com",
        "Subject": "Test",
        "Date": "Mon, 06 Apr 2026 09:12:33 +0200"
    }.get(k, default)
    msg.is_multipart.return_value = False
    msg.get_payload.return_value = b"Hello"
    msg.get_content_charset.return_value = 'utf-8'

    mock_box.__iter__.return_value = [msg, msg]
    mock_mbox.return_value = mock_box

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    collect("fake.mbox")

    # On vérifie que la requête SQL contient ON DUPLICATE KEY UPDATE
    sql = mock_cur.execute.call_args[0][0]
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert mock_cur.execute.call_count == 2

@patch('os.path.exists')
@patch('pymysql.connect')
@patch('mailbox.mbox')
def test_collect_timezone_aware(mock_mbox, mock_connect, mock_exists):
    mock_exists.return_value = True
    mock_box = MagicMock()
    msg = MagicMock()
    # Date avec un offset +0200
    msg.get.side_effect = lambda k, default=None: {
        "Message-ID": "<test-123>",
        "Date": "Mon, 06 Apr 2026 09:12:33 +0200"
    }.get(k, default)
    msg.is_multipart.return_value = False
    msg.get_payload.return_value = b"Hello"
    msg.get_content_charset.return_value = 'utf-8'

    mock_box.__iter__.return_value = [msg]
    mock_mbox.return_value = mock_box

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    collect("fake.mbox")

    # On vérifie l'argument 'received_at' passé au execute
    args = mock_cur.execute.call_args[0][1]
    received_at = args[2]

    # La TZ doit être conservée
    assert received_at.tzinfo is not None
    assert received_at.utcoffset() == timedelta(hours=2)
