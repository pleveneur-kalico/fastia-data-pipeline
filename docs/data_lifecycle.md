# Data Lifecycle - Flux de données FastIA

## 1. Schéma du flux (Pipeline)
1.  **Sources :** 
    - Historique : Fichier JSONL.
    - Continu : Emails (`.mbox`), Formulaires Web (`JSONL`), Chat (`CSV`).
2.  **Ingestion :** 
    - Mode `run` pour le dataset complet.
    - Mode `ingest` via `src/sources/integrate.py` pour les nouvelles sources.
3.  **Nettoyage/Normalisation :** 
    - Décodage MIME/HTML.
    - Agrégation des sessions de chat.
    - Suppression des citations et signatures (regex).
4.  **Déduplication Cross-Canal :** Marquage des doublons (colonne `dedup_status`) basés sur l'expéditeur et l'empreinte sémantique (fenêtre 48h).
5.  **Anonymisation :** Masquage des PII via `src/pipeline/anonymize.py`.
6.  **Stockage SQL :** Insertion dans MySQL avec idempotence sur `external_id`.

## 2. Points de rupture potentiels (Bottlenecks)
* **Format des emails :** Les emails multipart complexes peuvent altérer la qualité du texte extrait.
* **Qualité du nettoyage :** Les fils de discussion imbriqués ou les signatures atypiques peuvent polluer le corps.
* **Doublons cross-canal :** La détection repose sur l'email de l'expéditeur ; si un client utilise deux adresses différentes, le doublon ne sera pas détecté.

## 3. Maintenance
* **Fréquence de révision :** Après chaque itération de modèle (Module 2).
* **Propriétaire :** Équipe Data Engineering FastIA.
