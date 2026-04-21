import pandas as pd
from loguru import logger

ALLOWED_CATEGORIES = [
    "Support technique",
    "Information générale",
    "Demande commerciale",
    "Demande de transformation",
    "Réclamation"
]

ALLOWED_PRIORITIES = ["normale", "haute"]

def validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validation du schéma (catégories autorisées, priorités autorisées, champs obligatoires).
    Ajoute une colonne 'is_valid' et logue les erreurs.
    """
    logger.info("Validation du schema")
    
    df = df.copy()
    df['is_valid'] = True
    df['validation_errors'] = ""

    # Champs obligatoires
    required_fields = ['input', 'categorie', 'priorite', 'reponse_suggeree']
    for field in required_fields:
        if field not in df.columns:
            logger.error(f"Rubrique manquante : {field}")
            # On ne peut pas valider si le champ manque carrément dans le DF
            continue
        
        missing = df[field].isna()
        if missing.any():
            df.loc[missing, 'is_valid'] = False
            df.loc[missing, 'validation_errors'] += f"Missing {field};"

    # Validation des catégories
    if 'categorie' in df.columns:
        invalid_cat = ~df['categorie'].isin(ALLOWED_CATEGORIES)
        if invalid_cat.any():
            df.loc[invalid_cat, 'is_valid'] = False
            df.loc[invalid_cat, 'validation_errors'] += "Invalid category;"
            logger.warning(f"Trouve {invalid_cat.sum()} categories non valides")

    # Validation des priorités
    if 'priorite' in df.columns:
        invalid_prio = ~df['priorite'].isin(ALLOWED_PRIORITIES)
        if invalid_prio.any():
            df.loc[invalid_prio, 'is_valid'] = False
            df.loc[invalid_prio, 'validation_errors'] += "Invalid priority;"
            logger.warning(f"Trouve {invalid_prio.sum()} priorities invalides")

    valid_count = df['is_valid'].sum()
    logger.info(f"Validation Terminee : {valid_count}/{len(df)} lignes valides")
    
    return df
