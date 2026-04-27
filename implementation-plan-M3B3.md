# Plan d'implémentation — Module 3 Brief 3 : Anticiper un nouveau besoin métier

Ce document détaille la stratégie pour répondre aux exigences du Brief 3 du Module 3 de la pipeline FastIA. L'objectif est de planifier l'intégration de la détection de langue et de l'analyse de sentiment.

## 1. Résumé de la mission
Anticiper l'évolution de la pipeline en passant d'une logique de collecte/nettoyage à une logique d'enrichissement intelligent. Il ne s'agit pas d'une implémentation complète en production, mais d'une phase de cadrage, de validation empirique et d'un prototype (PoC) ciblé.

---

## 2. Étapes de réalisation

### Phase 1 : Cadrage et Analyse (Documentation)
1. **Cadrage du besoin métier** (`docs/cadrage_besoin_metier.md`)
   - Reformulation opérationnelle du besoin.
   - Identification des personas (utilisateurs finaux, opérateurs).
   - Définition de critères de succès mesurables (ex: Accuracy > 95%).
   - Analyse des risques éthiques (AI Act, biais de catégorisation).

2. **Évaluation des sources de données** (`docs/sources_data_evaluation.md`)
   - Création d'un tableau comparatif des solutions :
     - Détection langue : `langdetect` (local), `fasttext` (local), Google Cloud API.
     - Sentiment : `distilcamembert` (HuggingFace), modèles sur mesure.
   - Analyse selon : Coût, Accessibilité, Qualité, RGPD, Contraintes RAM/Latence.

### Phase 2 : Vérification Empirique (Notebook)
1. **Notebook d'exploration** (`notebook_brief3_module3.ipynb`)
   - Connexion à la base actuelle.
   - Test de détection de langue sur le champ `body`.
   - Validation (ou infirmation) de l'hypothèse métier : "1/3 des demandes sont non-françaises".
   - Premier passage d'un modèle de sentiment sur un échantillon de 100 lignes.

### Phase 3 : Conception de l'Évolution
1. **Plan d'évolution de la pipeline** (`docs/plan_evolution_pipeline.md`)
   - Schéma cible d'insertion de l'étape d'enrichissement.
   - Proposition de schéma SQL (nouvelles colonnes : `langue`, `sentiment`, scores).
   - Stratégie de mise à jour des modèles existants (règles métier vs re-entraînement).

### Phase 4 : Preuve de Concept (PoC Technique)
1. **Développement du module d'enrichissement** (`src/pipeline/enrich.py`)
   - Implémentation d'une fonction pure pour l'une des deux étapes (Langue OU Sentiment).
   - Création d'une interface CLI : `python -m src.pipeline.enrich`.
   - Mesure des coûts d'inférence (temps et RAM).
2. **Tests unitaires** (`tests/test_enrich.py`)
   - Validation avec Pytest sur 5 cas limites (langues variées, chaînes vides, etc.).

### Phase 5 : Eco-conception et Gouvernance
1. **Note d'éco-conception** (`docs/ecoconception_enrichissement.md`)
   - Analyse de la consommation de ressources.
   - Stratégie d'idempotence (ne pas traiter les lignes déjà enrichies).
2. **Mise à jour des documents maîtres**
   - `docs/datasheet.md` : Description des nouveaux champs dérivés.
   - `docs/data_lifecycle.md` : Ajout de l'étape d'enrichissement.
   - `docs/risques_ethiques.md` : Détails sur les risques de la classification automatisée.

---

## 3. Livrables finaux
- 4 nouveaux documents de documentation (`.md`).
- 3 mises à jour de documents existants.
- 1 Notebook Jupyter d'analyse.
- 1 module Python d'enrichissement avec ses tests.
- Mise à jour du `README.md` avec la Roadmap.

## 4. Estimation de charge
- **Documentation & Cadrage** : 1.5h
- **Analyse de données (Notebook)** : 1h
- **Développement PoC & Tests** : 1.5h
- **Total estimé** : ~4h
