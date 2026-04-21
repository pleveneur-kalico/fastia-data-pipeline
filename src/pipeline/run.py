import argparse
import json
import pandas as pd
from pathlib import Path
from loguru import logger
from datetime import datetime

from src.pipeline.load import load_jsonl
from src.pipeline.clean import drop_duplicates, normalize_text, handle_missing, flag_length_outliers
from src.pipeline.validate import validate
from src.pipeline.anonymize import anonymize_text

def run_pipeline(input_path: str, output_path: str):
    """
    Orchestration complète : load -> clean -> anonymize -> validate -> save.
    """
    start_time = datetime.now()
    logger.info(f"Debut pipeline at {start_time}")
    
    # 1. Chargement
    df = load_jsonl(input_path)
    
    # 2. Nettoyage
    df = drop_duplicates(df)
    df = normalize_text(df)
    df = handle_missing(df)
    df = flag_length_outliers(df)
    
    # 3. Anonymisation
    df = anonymize_text(df)
    
    # 4. Validation
    df = validate(df)
    
    # 5. Sauvegarde
    logger.info(f"Sauvegardes des donnees traitees dans {output_path}")
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarde en JSONL (orient records, lines=True)
    df.to_json(output_path, orient='records', lines=True, force_ascii=False)
    
    # 6. Metadata
    meta_path = output_path_obj.with_suffix('.meta.json')
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_path,
        "output_file": output_path,
        "total_rows": len(df),
        "valid_rows": int(df['is_valid'].sum()),
        "outliers_detected": int(df['is_outlier'].sum()),
        "duration_seconds": (datetime.now() - start_time).total_seconds()
    }
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Pipeline termine avec success {metadata['duration_seconds']:.2f}s")
    logger.info(f"Metadata sauvegardes dans {meta_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastIA Data Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSONL file")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSONL file")
    
    args = parser.parse_args()
    
    run_pipeline(args.input, args.output)
