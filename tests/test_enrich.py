import pytest
import pandas as pd
from src.pipeline.enrich import enrich_language, enrich_sentiment

def test_enrich_language_basic():
    """Test de base sur les 5 cas demandés."""
    data = {
        "input_text": [
            "Bonjour, j'ai un problème avec mon compte.", # FR
            "Hello, I have an issue with my order.",      # EN
            "Hola, tengo un problema con mi cuenta.",    # ES
            "Please call me back au plus vite.",          # Mix FR/EN
            ""                                            # Empty
        ]
    }
    df = pd.DataFrame(data)
    df_enriched = enrich_language(df, text_column="input_text")

    assert "langue" in df_enriched.columns
    assert df_enriched.iloc[0]["langue"] == "fr"
    assert df_enriched.iloc[1]["langue"] == "en"
    assert df_enriched.iloc[2]["langue"] == "es"
    # Mix FR/EN : langdetect choisit généralement une des deux, souvent EN si plus de mots EN
    assert df_enriched.iloc[3]["langue"] in ["fr", "en"]
    assert df_enriched.iloc[4]["langue"] == "unknown"

def test_enrich_language_missing():
    """Test avec des valeurs manquantes."""
    data = {
        "input_text": [None, "Ceci est du français"]
    }
    df = pd.DataFrame(data)
    df_enriched = enrich_language(df, text_column="input_text")

    assert df_enriched.iloc[0]["langue"] == "unknown"
    assert df_enriched.iloc[1]["langue"] == "fr"

def test_enrich_language_short_text():
    """Test avec des textes très courts."""
    data = {
        "input_text": ["Hi", "Ok"]
    }
    df = pd.DataFrame(data)
    df_enriched = enrich_language(df, text_column="input_text")
    # Sur des textes très courts, langdetect peut se tromper ou renvoyer unknown
    assert "langue" in df_enriched.columns

def test_enrich_sentiment_basic():
    """Test de l'analyse de sentiment."""
    data = {
        "input_text": [
            "C'est génial, j'adore !",
            "Nul, service client déplorable.",
            "Ok."
        ]
    }
    df = pd.DataFrame(data)
    df_enriched = enrich_sentiment(df, text_column="input_text")

    assert "sentiment" in df_enriched.columns
    assert any("star" in s or "neutral" in s for s in df_enriched["sentiment"])
