import pandas as pd
import numpy as np
import hashlib
from loguru import logger

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Suppression des doublons exacts et quasi-doublons via un hash normalisé.
    """
    logger.info("Suppression des doublons")
    initial_len = len(df)
    
    # Doublons exacts
    df = df.drop_duplicates()
    
    # Quasi-doublons sur la colonne 'input'
    def normalize_for_hash(text):
        if not isinstance(text, str):
            return ""
        return " ".join(text.lower().split())
    
    df['temp_hash'] = df['input'].apply(lambda x: hashlib.md5(normalize_for_hash(x).encode()).hexdigest())
    df = df.drop_duplicates(subset=['temp_hash']).drop(columns=['temp_hash'])
    
    final_len = len(df)
    logger.info(f"Doublons supprimes : {initial_len - final_len}")
    return df

def normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoyage du texte (espaces, guillemets, casse) tout en préservant l'original dans input_raw.
    """
    logger.info("Normalisation du texte")
    
    if 'input_raw' not in df.columns:
        df['input_raw'] = df['input']
    
    def clean_text(text):
        if not isinstance(text, str):
            return text
        # Suppression des espaces superflus
        text = " ".join(text.split())
        # Normalisation des guillemets (optionnel, mais propre)
        text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        return text

    df['input'] = df['input'].apply(clean_text)
    return df

def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gestion des valeurs manquantes.
    - Suppression si 'input' est vide.
    - Imputation pour 'reponse_suggeree'.
    """
    logger.info("Traitement des valeurs manquantes")
    
    # Suppression si input est vide ou NaN
    df = df.dropna(subset=['input'])
    df = df[df['input'].str.strip() != ""]
    
    # Imputation pour reponse_suggeree
    if 'reponse_suggeree' in df.columns:
        df['reponse_suggeree'] = df['reponse_suggeree'].fillna("Réponse en attente de traitement.")
    
    return df

def flag_length_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détection des outliers de longueur via Z-score.
    Ajoute une colonne 'is_outlier'.
    """
    logger.info("Détection des longueurs outliers")
    
    lengths = df['input'].str.len()
    mean = lengths.mean()
    std = lengths.std()
    
    # Z-score > 3
    df['is_outlier'] = (np.abs(lengths - mean) > (3 * std))
    
    outlier_count = df['is_outlier'].sum()
    logger.info(f"Détectes : {outlier_count} outliers")
    
    return df
