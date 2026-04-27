# Plan d'Augmentation des Données - Brief 3

## 1. État des lieux (Audit Brief 2)

Le dataset actuel contient **96 exemples** avec la distribution suivante :

- **Support technique** : 22
- **Information générale** : 22 (0 en priorité 'haute' - GAP CRITIQUE)
- **Demande commerciale** : 18
- **Demande de transformation** : 17
- **Réclamation** : 17

La priorité 'haute' est globalement sous-représentée (28/96).

## 2. Objectifs

- **Volume cible** : 500 exemples (100 par catégorie).
- **Équilibre des priorités** : Viser ~40% de priorité 'haute' pour chaque catégorie.
- **Diversité stylistique** : Introduire des variations de longueur et de ton (formel/informel).

## 3. Stratégie technique

### Technique A : Paraphrase par LLM (Ollama)
- **Cible** : Toutes les catégories existantes.
- **Fonctionnement** : Utiliser le modèle `gemini-3-flash-preview:cloud` via Ollama pour générer 2 à 3 variations de chaque exemple "original".
- **Contrôle** : Prompt strict demandant de conserver la catégorie et la priorité mais de changer la formulation, la longueur ou le ton.

### Technique B : Génération par Gabarit (Templates)
- **Cible** : Priorité 'haute' pour la catégorie "Information générale".
- **Fonctionnement** : Utilisation de templates structurés avec des variables interchangeables (ex: "URGENT : [Question Sûreté] sur [Service] ?").
- **Exemples visés** : Questions sur la sécurité, la conformité légale ou les interruptions de service majeures.

## 4. Volume visé par Cible

| Catégorie | Original | Cible Total | Augmentation nécessaire | Techniques |
|---|---|---|---|---|
| Support technique | 22 | 100 | +78 | Paraphrase (LLM) |
| Information générale | 22 | 100 | +78 | Gabarit (20 haute) + Paraphrase (58) |
| Demande commerciale | 18 | 100 | +82 | Paraphrase (LLM) |
| Demande de transformation | 17 | 100 | +83 | Paraphrase (LLM) |
| Réclamation | 17 | 100 | +83 | Paraphrase (LLM) |

## 5. Validation et Traçabilité

- **Flag `source`** : Chaque nouvel exemple sera marqué `source: "synthetic"`.
- **Validation de schéma** : Passage obligatoire par le validateur (catégorie correcte, champs non vides).
- **Revue humaine** : Audit de 10% des lignes générées (50 lignes) consigné dans `docs/revue_augmentation.csv`.
