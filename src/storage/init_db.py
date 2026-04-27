import sqlalchemy
from src.storage.load import get_engine
from loguru import logger
from pathlib import Path

def init_db():
    engine = get_engine()
    schema_path = Path("src/storage/schema.sql")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        # On découpe par point-virgule pour exécuter chaque commande
        # (Attention : simpliste, mais suffisant pour ce schéma)
        sql_commands = f.read().split(";")
        
    with engine.connect() as conn:
        for cmd in sql_commands:
            cmd = cmd.strip()
            if cmd:
                try:
                    conn.execute(sqlalchemy.text(cmd))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Erreur sur commande SQL : {e}")
                    
    logger.info("Base de données initialisée avec succès.")

if __name__ == "__main__":
    init_db()
