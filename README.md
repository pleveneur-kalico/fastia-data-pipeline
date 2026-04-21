# FastIA Data Pipeline

Ce projet contient le pipeline de nettoyage et de préparation des données pour le projet FastIA (Module 2).

## Structure du Projet
- `src/pipeline/` : Modules de traitement (load, clean, anonymize, validate).
- `data/` : Dossiers de données (raw, interim, processed).
- `tests/` : Tests unitaires.
- `docs/` : Documentation et rapports d'audit.

## Utilisation

### Installation
```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_sm
```

### Exécution de la Pipeline
```bash
python -m src.pipeline.run --input data/raw/dataset_fastia_module1.jsonl --output data/processed/dataset_fastia_clean_v1.jsonl
```

### Tests
```bash
pytest tests/
```

## Synthèse du Nettoyage

| Métrique | Avant (Raw) | Après (Clean) |
|----------|-------------|---------------|
| Nombre de lignes | 86 | 86 |
| Doublons | 0 | 0 |
| PII Masqués | Non | Oui |
| Schéma Validé | Non | Oui |

## Documentation
- [Note Réglementaire et Éthique](docs/risques_ethiques.md)
