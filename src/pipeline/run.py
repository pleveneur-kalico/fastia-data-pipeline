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
from src.pipeline.augment import Augmentor
from src.storage.load import load_to_mysql
from src.storage.dump import dump_from_mysql
from src.sources.integrate import ingest
from sklearn.model_selection import train_test_split

def run_pipeline(input_path: str, output_path: str, full: bool = False):
    """
    Orchestration complète : load -> clean -> anonymize -> augment -> validate -> SQL -> split.
    """
    start_time = datetime.now()
    logger.info(f"Debut pipeline at {start_time} (Mode Full: {full})")

    # 1. Chargement & Nettoyage initial
    df = load_jsonl(input_path)
    df = drop_duplicates(df)
    df = normalize_text(df)
    df = handle_missing(df)
    df = flag_length_outliers(df)

    # 2. Anonymisation (PII)
    df = anonymize_text(df)

    if full:
        # 3. Augmentation (Brief 3)
        logger.info("Etape d'augmentation en cours...")
        augmentor = Augmentor(df)
        df = augmentor.run(target_per_cat=100) # Cible 500 total

    # 4. Validation
    df = validate(df)

    # 5. Stockage SQL (Brief 3)
    version = f"v2.{datetime.now().strftime('%Y%m%d')}"
    if full:
        load_to_mysql(df, version)
        # On redumpe depuis SQL pour garantir l'intégrité
        df = dump_from_mysql(output_path, version)
    else:
        # Sauvegarde JSONL standard
        df.to_json(output_path, orient='records', lines=True, force_ascii=False)

    # 6. Génération des jeux train/test (si mode full)
    if full:
        logger.info("Génération des splits train/test...")
        df_valid = df.copy()

        train_df, test_df = train_test_split(
            df_valid,
            test_size=0.2,
            stratify=df_valid["categorie"],
            random_state=42
        )

        def to_ft_format(row):
            return {"text": f"<s>[INST] {row['input']} [/INST] {row['reponse_suggeree']} </s>"}

        train_ft = train_df.apply(to_ft_format, axis=1).tolist()
        test_ft = test_df.apply(to_ft_format, axis=1).tolist()

        train_path = Path("data/processed/train_v2.jsonl")
        test_path = Path("data/processed/test_v2.jsonl")

        with open(train_path, "w", encoding="utf-8") as f:
            for item in train_ft:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        with open(test_path, "w", encoding="utf-8") as f:
            for item in test_ft:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info(f"Splits sauvegardés : {train_path}, {test_path}")

    # 7. Metadata
    output_path_obj = Path(output_path)
    meta_path = output_path_obj.with_suffix('.meta.json')
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_path,
        "output_file": output_path,
        "total_rows": len(df),
        "valid_rows": int(len(df)), # On suppose tout valide après dump SQL
        "duration_seconds": (datetime.now() - start_time).total_seconds(),
        "version": version
    }

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    logger.info(f"Pipeline termine avec success {metadata['duration_seconds']:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastIA Data Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Commande 'run' (historique)
    run_parser = subparsers.add_parser("run", help="Exécuter la pipeline complète")
    run_parser.add_argument("--input", type=str, required=True, help="Path to input JSONL file")
    run_parser.add_argument("--output", type=str, required=True, help="Path to output JSONL file")
    run_parser.add_argument("--full", action="store_true", help="Run full pipeline with augmentation and SQL")

    # Commande 'ingest' (unifiée)
    ingest_parser = subparsers.add_parser("ingest", help="Ingérer une nouvelle source")
    ingest_parser.add_argument("--source", type=str, choices=["email", "web", "chat"], required=True, help="Type de source")
    ingest_parser.add_argument("--input", type=str, required=True, help="Chemin vers le fichier source")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(args.input, args.output, args.full)
    elif args.command == "ingest":
        ingest(args.source, args.input)
    else:
        parser.print_help()
