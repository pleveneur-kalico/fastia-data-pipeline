# Brief 3 — Augmentation, stockage SQL et préparation de la suite

## Contexte du projet

Votre pipeline de nettoyage tourne et produit un dataset propre, versionné et documenté. Mais l'audit de biais du Brief 2 a confirmé ce qu'on pressentait : certaines catégories sont sous-représentées, et 100 exemples ne suffisent plus aux ambitions du produit. En parallèle, stocker les données en JSONL dans un dépôt Git atteint ses limites — les prochains briefs vont connecter de nouvelles sources (emails, formulaires web, chat) et le volume va grimper.

Votre manager vous demande donc deux choses : **enrichir le dataset par augmentation contrôlée, et migrer le stockage vers une base relationnelle** qui pourra accueillir les sources supplémentaires du Module 3. À la fin de ce brief, FastIA doit disposer d'un socle de données prêt à industrialiser.

---

## Objectif principal

Augmenter le dataset sur les catégories sous-représentées via des techniques de génération et d'augmentation, migrer le stockage final vers PostgreSQL ou MySQL, et produire des jeux d'entraînement/test rejouables depuis la base.

---

## Prérequis

- Brief 2 complété : pipeline de nettoyage fonctionnelle, dataset nettoyé v1 disponible
- PostgreSQL ou MySQL installé en local, ou via Docker
- Accès à un LLM pour génération synthétique (API FastIA de M1, ou autre)

---

## Étapes du projet

### 1. Stratégie d'augmentation

À partir de l'audit de biais du Brief 2, identifier précisément :

- Les catégories sous-représentées (en effectif ou en diversité stylistique)
- Les combinaisons catégorie × priorité manquantes ou rares
- Les registres de langue sous-couverts (formel / informel, court / long)

Rédiger `docs/plan_augmentation.md` qui liste les cibles, le volume visé par cible, et la technique retenue pour chacune.

### 2. Implémentation des techniques d'augmentation

Implémenter dans `src/pipeline/augment.py` au moins deux techniques parmi :

| Technique | Quand l'utiliser | À implémenter |
|---|---|---|
| **Paraphrase par LLM** | combler la diversité stylistique d'une catégorie | prompt contrôlé sur les exemples existants de la catégorie cible |
| **Génération à partir de gabarit** | compléter une combinaison catégorie × priorité rare | template + variables, validation manuelle d'un échantillon |
| **Back-translation** | augmenter la variance lexicale | traduction FR → EN → FR via un modèle léger |
| **Substitution contrôlée** | augmenter sans dériver sémantiquement | remplacement de synonymes via un lexique métier |

Contraintes :

- Chaque exemple généré passe **la validation de schéma** du Brief 2 (categorie, priorite, reponse_suggeree non vide)
- Un échantillon de 10% des générations fait l'objet d'une revue manuelle avant intégration
- Les exemples générés sont flagués (`source: "synthetic"` vs `"original"`) pour traçabilité

Documenter : combien d'exemples générés par technique, combien rejetés à la revue, combien retenus.

### 3. Migration vers SQL

Concevoir un schéma relationnel adapté au dataset et anticipant les sources futures (Module 3). Proposition minimale :

```sql
CREATE TABLE demandes (
  id              SERIAL PRIMARY KEY,
  input_text      TEXT NOT NULL,
  input_raw       TEXT,
  categorie       VARCHAR(50) NOT NULL,
  priorite        VARCHAR(20) NOT NULL,
  reponse_suggeree TEXT,
  source          VARCHAR(30) NOT NULL,      -- 'original' | 'synthetic' | futures
  canal           VARCHAR(30),                -- prévu pour M3 : 'email' | 'web' | 'chat' | ...
  langue          VARCHAR(10) DEFAULT 'fr',
  created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  dataset_version VARCHAR(20) NOT NULL
);

CREATE INDEX idx_demandes_categorie ON demandes(categorie);
CREATE INDEX idx_demandes_source ON demandes(source);
CREATE INDEX idx_demandes_version ON demandes(dataset_version);
```

Implémenter :

- `src/storage/schema.sql` — le DDL
- `src/storage/load.py` — chargement idempotent du JSONL nettoyé et augmenté vers la base
- `src/storage/dump.py` — export d'une version du dataset depuis la base vers JSONL pour fine-tuning

Le choix PostgreSQL vs MySQL est libre mais doit être justifié dans le README.

### 4. Génération des jeux train/test

Depuis la base, produire :

- Un split 80/20 stratifié sur `categorie`, avec seed fixée pour reproductibilité
- Export au format attendu par le pipeline de fine-tuning du Module 1 (`<s>[INST] ... [/INST] ... </s>`)
- Fichiers `data/processed/train_v2.jsonl` et `data/processed/test_v2.jsonl`
- Fichier `data/processed/dataset_v2.meta.json` avec version, date, hash, effectifs par split et par catégorie

### 5. Orchestration finale

Mettre à jour `src/pipeline/run.py` pour enchaîner :

```
brut → nettoyage (B2) → augmentation (B3) → validation → SQL → dump → split train/test
```

Une seule commande doit suffire pour rejouer toute la pipe :

```bash
python -m src.pipeline.run --full
```

Ajouter un Makefile ou un `pyproject.toml` [scripts] pour lister les commandes utiles.

### 6. Comparaison v1 vs v2

Produire un tableau comparatif dans le README :

| Indicateur | v1 (après B2) | v2 (après B3) |
|---|---|---|
| Nombre d'exemples | | |
| Répartition par catégorie | | |
| Répartition par priorité | | |
| % d'exemples synthétiques | | |
| Longueur moyenne input | | |

Commenter brièvement les évolutions et ce qu'elles devraient améliorer côté modèle.

---

## Livrables

- **Dépôt GitHub** finalisé avec :
  - Module d'augmentation `src/pipeline/augment.py` et ses tests
  - Schéma et scripts de stockage `src/storage/`
  - Datasets v2 versionnés dans `data/processed/`
  - `docs/plan_augmentation.md`
- **README.md** finalisé avec :
  - Architecture complète du projet de données FastIA
  - Procédure de lancement de la pipeline complète (brut → train/test)
  - Schéma de la base et justification du choix SGBD
  - Tableau comparatif v1 / v2
- **Base de données** peuplée et reproductible via un script ou un `docker-compose.yml`

---

## Charge de travail estimée

5 à 6 heures

---

## Ressources

- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/)
- [psycopg 3](https://www.psycopg.org/psycopg3/docs/) ou [PyMySQL](https://pymysql.readthedocs.io/)
- [NLTK — synonym substitution via WordNet](https://www.nltk.org/)
- [EDA — Easy Data Augmentation for NLP](https://arxiv.org/abs/1901.11196)

---

## Bonus

- Ajouter Alembic (ou équivalent MySQL) pour le versionnement du schéma — préparera l'ajout de colonnes au Module 3
- Mettre en place un `docker-compose.yml` qui démarre PostgreSQL + l'API FastIA du Module 1 — le tout rejouable en une commande
- Relancer un fine-tuning rapide sur le dataset v2 et comparer les métriques MLflow avec le Run 2 du Module 1
