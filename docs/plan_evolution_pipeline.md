# Plan d'évolution de la pipeline — Enrichissement (M3B3)

Ce document décrit la stratégie technique pour intégrer la détection de langue et l'analyse de sentiment dans la pipeline FastIA.

## 1. Schéma cible de la pipeline

L'étape d'enrichissement sera insérée après le nettoyage et l'anonymisation, afin de traiter des données propres mais avant le stockage SQL pour garantir que la base contient les métadonnées dès l'insertion.

**Flux de données révisé :**
1.  **Collecte** (Multi-source : Email, Chat, Web)
2.  **Cleaning** (Normalisation, Doublons)
3.  **Anonymisation** (Suppression des PII)
4.  **Enrichissement (NOUVEAU)**
    *   `detect_language()`
    *   `analyze_sentiment()`
5.  **Augmentation** (Optionnel, uniquement si full pipeline)
6.  **Stockage SQL** (Insertion avec colonnes de métadonnées)

## 2. Évolution du schéma SQL

Bien que la colonne `langue` existe déjà par anticipation dans certains scripts, le schéma doit être stabilisé avec les champs suivants :

```sql
ALTER TABLE demandes 
ADD COLUMN langue VARCHAR(10),
ADD COLUMN langue_confidence FLOAT,
ADD COLUMN sentiment VARCHAR(20),
ADD COLUMN sentiment_score FLOAT;
```

*Note : La migration sera gérée via Alembic dans l'itération suivante.*

## 3. Impact sur le modèle FastIA M1

La détection de langue et de sentiment aura un impact direct sur la logique de priorité :

*   **Règles métier (Post-enrichissement)** : Si `langue != 'fr'`, forcer `priorite = 'haute'` et router vers la file internationale.
*   **Aide au support** : Si `sentiment == 'négatif'`, ajouter un flag d'alerte visuel dans l'interface de l'opérateur.
*   **Évolution future** : Utiliser ces nouveaux champs comme *features* d'entrée pour un futur modèle de classification (Module 4) au lieu de simples règles hard-codées.

## 4. Roadmap de mise en œuvre

1.  **Phase PoC (Actuel)** : Implémentation de `src/pipeline/enrich.py` avec `langdetect`.
2.  **Phase Intégration** : Modification de `src/pipeline/run.py` pour inclure l'enrichissement par défaut.
3.  **Phase Industrialisation** : Passage à `fasttext` pour la langue et `distilcamembert` pour le sentiment afin d'augmenter la précision.
4.  **Phase Monitoring** : Mise en place d'un dashboard de qualité pour monitorer les erreurs de détection.
