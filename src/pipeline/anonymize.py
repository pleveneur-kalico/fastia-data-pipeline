import pandas as pd
import re
import spacy
from loguru import logger

# Chargement dictionnaire spacy français (large)
try:
    nlp = spacy.load("fr_core_news_lg")
except Exception as e:
    logger.warning(f"Impossible de charger le dictionnaire SpaCy : {e}. L'anonymisation sera limite.")
    nlp = None

def anonymize_text(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détection et masquage des emails, téléphones, URLs et noms.
    """
    logger.info("Anonymisation PII")
    
    # Regex patterns
    EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE_REGEX = r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
    URL_REGEX = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

    def mask_pii(text):
        if not isinstance(text, str):
            return text
        
        # Mask Emails
        text = re.sub(EMAIL_REGEX, "[EMAIL]", text)
        
        # Mask Phones
        text = re.sub(PHONE_REGEX, "[PHONE]", text)
        
        # Mask URLs
        text = re.sub(URL_REGEX, "[URL]", text)
        
        # Mask Noms propres avc utilisation de SpaCy
        if nlp:
            doc = nlp(text)
            # Ordre inverse pour éviter le décalage d'index
            for ent in reversed(doc.ents):
                if ent.label_ == "PER":
                    text = text[:ent.start_char] + "[NAME]" + text[ent.end_char:]
        
        return text

    df['input'] = df['input'].apply(mask_pii)
    return df
