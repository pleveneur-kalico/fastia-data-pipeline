# Spécifications et Plan d'Implémentation — Module 3 Brief 2
# Brancher Web & Chat, Harmoniser, Segmenter

Ce document détaille la stratégie pour l'intégration des canaux Web et Chat, ainsi que la mise en place d'une déduplication cross-canal intelligente.

---

## 1. Nouveaux Connecteurs (Loaders)

### 1.1. Loader Web (`src/sources/web_loader.py`)
- **Format** : JSONL (1 ligne par soumission).
- **Transformation** :
    - `submission_id` -> `external_id`.
    - `submitted_at` -> `received_at`.
    - `form.message` -> `body`.
- **Règles Spécifiques** :
    - **RGPD** : Ignorer le champ `consent_marketing`.
    - **Fallback Sujet** : Si `form.subject` est vide, extraire les 60 premiers caractères du message.
    - **Metadata** : Stocker `ip_country` et `user_agent` dans `canal_metadata`.

### 1.2. Loader Chat (`src/sources/chat_loader.py`)
- **Format** : CSV (format conversationnel).
- **Transformation** :
    - Aggrégation par `session_id`.
    - `body` = concaténation chronologique des messages du rôle `visitor`.
- **Règles Spécifiques** :
    - **Transcript** : Stocker l'intégralité de la conversation (visiteur + agent) dans `canal_metadata.transcript_complet`.
    - **Rejet** : Ignorer les sessions sans aucun message visiteur.

---

## 2. Intelligence et Harmonisation

### 2.1. Déduplication Cross-Canal (`src/sources/dedup.py`)
- **Stratégie** : Empreinte sémantique via `hash(normalize(body[:300]))`.
- **Logique** :
    - Fenêtre temporelle : 48 heures.
    - Identification : Même expéditeur (ou email anonymisé).
- **Persistance** : Ne pas supprimer les doublons. Ajouter une colonne `dedup_status` (valeurs : `original`, `cross_channel_duplicate`).

### 2.2. Couche d'Intégration Unifiée (`src/sources/integrate.py`)
- **Point d'entrée unique** : `ingest(source, path)`.
- **Orchestration** :
    1. Dispatch vers le loader adéquat.
    2. Nettoyage et Anonymisation (Pipeline M2).
    3. Marquage des doublons via `dedup.py`.
    4. Insertion idempotente en base.

---

## 3. Plan d'Action (Roadmap)

### Phase 1 : Loaders Web & Chat (Terminé)
- [x] Créer `src/sources/web_loader.py` + tests unitaires.
- [x] Créer `src/sources/chat_loader.py` + tests unitaires.
- [x] Créer les fiches sources `docs/source_web.md` et `docs/source_chat.md`.

### Phase 2 : Évolution SQL (Alembic) (Terminé)
- [x] Migration pour ajouter la colonne `dedup_status` à la table `demandes`.
- [x] Migration pour ajouter la colonne `sender`.
- [x] Indexation sur `received_at`.

### Phase 3 : Déduplication et Intégration (Terminé)
- [x] Implémenter la logique de hachage dans `dedup.py`.
- [x] Créer `integrate.py` pour unifier le flux.
- [x] Documenter la stratégie dans `docs/dedup_strategy.md`.

### Phase 4 : Pipeline et Documentation (Terminé)
- [x] Mettre à jour `src/pipeline/run.py` pour supporter `--source web` et `--source chat`.
- [x] Mettre à jour `docs/datasheet.md`, `docs/data_lifecycle.md`.

### Phase 5 : Analyse Segmentée (Terminé)
- [x] Créer le notebook `notebook_brief2_module3.ipynb`.
- [x] Analyser les biais, la volumétrie et la qualité par canal.

---

## 4. Livrables Attendus
- Code des loaders et tests associés.
- Script de migration Alembic.
- Documentation mise à jour (Datasheet, Lifecycle, Plan d'augmentation).
- Notebook d'analyse complet.
