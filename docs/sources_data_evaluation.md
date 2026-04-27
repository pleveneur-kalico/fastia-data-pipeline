# Évaluation des sources de données — Enrichissement (M3B3)

Ce document évalue les solutions techniques pour la détection de langue et l'analyse de sentiment dans la pipeline FastIA.

## 1. Détection de langue

| Source | Accessibilité | Qualité | Coût | RGPD | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **langdetect** (PyPI) | Immédiate (`pip install`) | Bonne sur FR/EN, peut faiblir sur textes ES très courts. | Nul (Local) | Conforme (Traitement local) | **Retenu pour PoC** |
| **fasttext** (Facebook) | Nécessite le téléchargement d'un modèle (126MB). | Excellente (Baseline mondiale). | Nul (Local) | Conforme | **Alternative court terme** |
| **Google Cloud Translation** | Nécessite compte GCP + Clé API. | État de l'art. | Payant au caractère. | Risque (Transfert hors UE) | **Écarté** |

### Détails Techniques - Détection de langue
*   **langdetect** : Basé sur le portage Python de la bibliothèque Java de Google. Très léger, pas de dépendance lourde.
*   **fasttext (lid.176.bin)** : Plus robuste aux fautes de frappe et aux langues proches, mais demande plus de RAM (~150MB en mémoire).

## 2. Analyse de sentiment

| Source | Accessibilité | Qualité | Coût | RGPD | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **distilcamembert-base-sentiment** | HuggingFace (`transformers`) | Très bonne (modèle spécifique FR). | Nul (Local) | Conforme | **Retenu comme baseline** |
| **VADER** (via NLTK) | Immédiate. | Médiocre en FR (nécessite traduction). | Nul | Conforme | **Écarté** |
| **Modèle sur mesure (Fine-tuning)** | Nécessite ~500 exemples annotés. | Potentiellement la meilleure. | Élevé (Temps humain) | Conforme | **Option future (Module 4)** |

### Détails Techniques - Sentiment
*   **distilcamembert** : Nécessite l'installation de `torch` et `transformers`. Modèle lourd (~270MB). Excellente compréhension des nuances du français.
*   **Fine-tuning** : Permettrait de capturer le jargon spécifique au support client de FastIA, mais le ROI doit être prouvé par le PoC.

## 3. Contraintes opérationnelles et de gouvernance

*   **Installation** : L'ajout de modèles de Deep Learning (Transformers) augmentera significativement la taille du `venv` et le temps de build CI/CD.
*   **Latence** : L'inférence sur CPU (serveur standard) pour Camembert peut prendre entre 50ms et 200ms par message.
*   **Confidentialité** : Le choix de solutions **locales** (langdetect, models HF) garantit qu'aucune donnée client ne quitte l'infrastructure FastIA, respectant ainsi les engagements de sécurité.
