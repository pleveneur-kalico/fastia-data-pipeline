import pytest
from pathlib import Path
import json
import csv
from datetime import datetime
from unittest.mock import MagicMock, patch
from src.sources.web_loader import load_web, RawDemande as WebRawDemande
from src.sources.chat_loader import load_chat, RawDemande as ChatRawDemande
from src.sources.dedup import calculate_semantic_hash, mark_cross_channel_duplicates

@pytest.fixture
def tmp_web_file(tmp_path):
    p = tmp_path / "web.jsonl"
    data = [
        {
            "submission_id": "WEB-001",
            "submitted_at": "2026-04-12T14:23:11Z",
            "form": {
                "email": "test@example.com",
                "subject": "Subject 1",
                "message": "Message 1",
                "consent_marketing": True
            },
            "ip_country": "FR"
        },
        {
            "submission_id": "WEB-002",
            "submitted_at": "2026-04-12T15:00:00Z",
            "form": {
                "email": "test2@example.com",
                "message": "This is a very long message that should be truncated for the subject line if it works correctly"
            }
        }
    ]
    with open(p, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return p

@pytest.fixture
def tmp_chat_file(tmp_path):
    p = tmp_path / "chat.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["session_id", "timestamp", "role", "message"])
        writer.writerow(["CHAT-001", "2026-04-12T09:00:00Z", "visitor", "Hello"])
        writer.writerow(["CHAT-001", "2026-04-12T09:01:00Z", "agent", "Hi"])
        writer.writerow(["CHAT-001", "2026-04-12T09:02:00Z", "visitor", "I need help"])
        writer.writerow(["CHAT-002", "2026-04-12T10:00:00Z", "agent", "How can I help?"])
    return p

def test_load_web(tmp_web_file):
    results = list(load_web(tmp_web_file))
    assert len(results) == 2

    # Check first entry
    assert results[0].external_id == "WEB-001"
    assert results[0].sender == "test@example.com"
    assert results[0].subject == "Subject 1"
    assert results[0].body == "Message 1"
    assert "consent_marketing" not in results[0].canal_metadata # RGPD
    assert results[0].canal_metadata["ip_country"] == "FR"

    # Check fallback subject
    assert results[1].external_id == "WEB-002"
    assert results[1].subject == "This is a very long message that should be truncated for the..."

def test_load_chat(tmp_chat_file):
    results = list(load_chat(tmp_chat_file))
    # CHAT-002 should be rejected as it has no visitor message
    assert len(results) == 1

    assert results[0].external_id == "CHAT-001"
    assert results[0].body == "Hello I need help"
    assert results[0].subject == "Hello"
    assert "agent" in results[0].canal_metadata["transcript_complet"]

def test_calculate_semantic_hash():
    h1 = calculate_semantic_hash("  Hello   World  ")
    h2 = calculate_semantic_hash("hello world")
    assert h1 == h2

    h3 = calculate_semantic_hash("A" * 500)
    h4 = calculate_semantic_hash("A" * 300)
    assert h3 == h4

@patch("src.sources.dedup.get_engine")
def test_mark_cross_channel_duplicates(mock_get_engine):
    # Setup mock
    mock_conn = MagicMock()
    mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

    # Mocking DB response:
    # For d1: return None (no duplicate found)
    # For d2: return a tuple (duplicate found)
    mock_conn.execute.return_value.fetchone.side_effect = [None, (1,)]

    d1 = WebRawDemande(
        canal="web", external_id="W1", sender="u@e.com",
        body="Duplicate content", received_at=datetime.now()
    )
    d2 = ChatRawDemande(
        canal="chat", external_id="C1", sender="u@e.com",
        body="Duplicate content", received_at=datetime.now()
    )

    mark_cross_channel_duplicates([d1, d2])

    assert d1.dedup_status == "original"
    assert d2.dedup_status == "cross_channel_duplicate"
