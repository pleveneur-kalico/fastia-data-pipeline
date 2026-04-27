# Spécifications et Plan d'Implémentation — Ingestion des Emails FastIA

Ce document détaille la stratégie pour l'industrialisation du canal "Email" dans la pipeline de données FastIA.

## 1. Objectif Principal
Passer d'une ingestion manuelle (Excel) à une ingestion automatisée, robuste et idempotente des demandes clients arrivant par email (format `.mbox`).

---

## 2. Architecture Technique

### 2.1. Évolution du Schéma SQL (Alembic)
La table `demandes` doit être enrichie pour supporter les métadonnées de source et garantir l'idempotence.

- **Nouvelles Colonnes** :
  - `received_at` (DateTime) : Date d'émission de l'email.
  - `external_id` (String) : Identifiant unique du canal (ex: `Message-ID`).
  - `canal_metadata` (JSON) : Stockage flexible pour le sujet, les threads, etc.
- **Contrainte d'Idempotence** : Index unique sur le couple `(canal, external_id)`.

### 2.2. Module Loader (`src/sources/email_loader.py`)
Un nouveau composant capable d'extraire proprement le texte des emails.

- **Parsing** : Utilisation de la bibliothèque standard `mailbox` pour itérer sur le fichier `.mbox`.
- **Décodage** : Gestion des encodages `quoted-printable`, `base64` et des headers encodés (RFC 2047).
- **Nettoyage (Critique)** :
    - Extraction du `text/plain` en priorité.
    - Fallback HTML vers Texte via `BeautifulSoup`.
    - Suppression des citations (historique des échanges) et des blocs de signature.
- **Validation** : Modèle Pydantic `RawDemande` pour garantir la structure des données extraites.

### 2.3. Correction du Script Legacy (`src/sources/legacy_collect.py`)
Remise à niveau du script existant pour stabiliser l'ingestion historique.

- **Bugs à corriger** :
    - Gestion des encodages (éviter les crashs sur non-UTF-8).
    - Ajout de l'idempotence (éviter les doublons).
    - Conservation de la Timezone sur les dates.

---

## 3. Plan d'Action (Roadmap)

### Phase 1 : Cadrage et Documentation (Terminé)
- [x] Analyse de l'échantillon `emails_fastia.mbox`.
- [x] Création de la fiche source `docs/source_email.md`.
- [x] Revue du document par Claude.

### Phase 2 : Évolution de la Base de Données (Terminé)
- [x] Initialisation d'Alembic.
- [x] Création du script de migration `add_canal_metadata`.
- [x] Correction de la configuration `alembic.ini` (problème d'échappement du `%`).
- [x] Exécution de la migration et test de réversibilité (`upgrade` / `downgrade`).

### Phase 3 : Développement du Loader Email (Terminé)
- [x] Création du dossier `src/sources/`.
- [x] Implémentation du modèle `RawDemande` (Pydantic).
- [x] Développement de la fonction `load_mbox`.
- [x] Développement de l'utilitaire `strip_quoted_text` (Regex).

### Phase 4 : Debug du Script Legacy (Terminé)
- [x] Intégration du fichier `legacy_collect.py`.
- [x] Identification des lignes buggées via tests unitaires.
- [x] Application des correctifs (encodage, idempotence, timezone, MySQL).
- [x] Validation via `tests/test_legacy_collect.py`.

### Phase 5 : Intégration Pipeline CLI (Terminé)
- [x] Ajout de la commande `ingest` dans `src/pipeline/run.py`.
- [x] Chaînage : Loader -> Cleaning -> Anonymisation -> Storage SQL.
- [x] Mise à jour du `README.md` avec les nouvelles commandes.
- [x] Mise à jour de `docs/datasheet.md` et `docs/data_lifecycle.md`.

---

## 4. Stratégie de Vérification

### Tests Automatisés
- **Unitaires** : Tests sur le décodage des emails complexes et le stripping des signatures.
- **Intégration** : Test de bout en bout (ingestion d'un lot mbox -> vérification en base).
- **Migrations** : Vérifier qu'Alembic peut revenir en arrière sans perte de données.

### Validation Manuelle
- Inspection de la table `demandes` après ingestion pour vérifier la qualité de l'anonymisation et du nettoyage du texte.
