# FastIA Data Pipeline

Ce projet contient le pipeline de nettoyage et de préparation des données pour le projet FastIA (Module 2).

## Architecture du Projet (v2)

Le pipeline a été enrichi pour supporter l'industrialisation des données :
`Brut -> Nettoyage -> Anonymisation -> Augmentation -> Validation -> Stockage SQL -> Export Splits`

### Composants Clés :
- **Augmentation (`src/pipeline/augment.py`)** : Utilise **Ollama** (`gemini-3-flash-preview:cloud`) pour la paraphrase stylistique et des gabarits pour combler les manques (ex: priorité haute en Information Générale).
- **Stockage SQL (`src/storage/`)** : Migration vers **MySQL**.
    - *Justification* : Choix de MySQL pour sa performance sur les lectures/écritures simples et sa compatibilité avec les outils de BI. La base `fastia_db` centralise désormais le dataset versionné.
- **Orchestration** : Une seule commande pour rejouer tout le flux.

## Comparaison v1 (Nettoyé) vs v2 (Augmenté)

| Indicateur | v1 (après B2) | v2 (après B3) |
|---|---|---|
| Nombre d'exemples | 96 | 500 |
| Répartition par catégorie | Équilibrée (~19/cat) | Homogène (100/cat) |
| Répartition par priorité | 29% haute | 39% haute |
| % d'exemples synthétiques | 0% | 80.8% |
| Longueur moyenne input | 100.7 chars | 155.5 chars |

*Note : L'augmentation a permis de combler les "zones blanches" identifiées lors de l'audit de biais et d'augmenter la richesse lexicale du dataset.*

## Utilisation

### Installation
```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_lg
```

### Exécution Complète (v2)
```bash
# Pipeline historique
python -m src.pipeline.run run --input data/raw/dataset_fastia_module1v2.jsonl --output data/processed/dataset_v2.jsonl --full

# Ingestion de nouvelles sources (Email)
python -m src.pipeline.run ingest --source email --input data/raw/emails_fastia.mbox
```

### Migrations
```bash
# Appliquer les évolutions de schéma
alembic upgrade head
```

### Tests
```bash
pytest tests/
```

## Module 3 Brief 1 — Ingestion multi-source (Emails)

Cette étape marque l'industrialisation du canal email dans la pipeline FastIA.

### Évolutions Techniques
- **Schéma SQL** : Enrichissement de la table `demandes` avec :
    - `received_at` : Date d'émission originale de l'email.
    - `external_id` : Identifiant unique du canal (ex: `Message-ID`).
    - `canal_metadata` : Stockage JSON des métadonnées (Sujet, Threads).
- **Idempotence** : Protection contre les doublons via un index unique sur `(canal, external_id)`.
- **Loader Email** : Nouveau module `src/sources/email_loader.py` capable de décoder le MIME, traiter le HTML, et nettoyer les signatures/citations.

### Utilisation de l'Ingestion
Pour intégrer de nouveaux emails dans la base :
```bash
python -m src.pipeline.run ingest --source email --input data/raw/emails_fastia.mbox
```

### Tests de non-régression
Pour vérifier la robustesse du chargement (encodages, timezones, doublons) :
```bash
python -m pytest tests/test_legacy_collect.py -v
```

## Documentation
- [Plan d'Augmentation](docs/plan_augmentation.md)
- [Note Réglementaire et Éthique](docs/risques_ethiques.md)
