import pandas as pd
import json
from loguru import logger
from pathlib import Path

def load_jsonl(path: str) -> pd.DataFrame:
    """
    Loads a JSONL file and flattens the 'output' column.
    
    Args:
        path: Path to the JSONL file.
        
    Returns:
        pd.DataFrame: Flattened DataFrame.
    """
    logger.info(f"Chargement des donnees {path}")
    
    try:
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        
        df = pd.DataFrame(data)
        
        if 'output' in df.columns:
            logger.info("Mise à plat de la colonne de sortie")
            output_df = pd.json_normalize(df['output'])
            df = pd.concat([df.drop(columns=['output']), output_df], axis=1)
        
        logger.info(f"Lignes chargees : {len(df)}.")
        return df
    
    except Exception as e:
        logger.error(f"Erreur chargement JSONL: {e}")
        raise

if __name__ == "__main__":
    # Test loading
    dataset_path = "data/raw/dataset_fastia_module1.jsonl"
    if Path(dataset_path).exists():
        df = load_jsonl(dataset_path)
        print(df.head())
    else:
        print(f"File {dataset_path} not found.")
