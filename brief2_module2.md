# Brief 2 — Pipeline de nettoyage et détection des biais

## Contexte du projet

Votre audit du Brief 1 a mis en évidence plusieurs problèmes de qualité dans le dataset FastIA : doublons, incohérences, valeurs suspectes, et surtout des zones d'ombre sur les biais potentiels. Votre manager valide le diagnostic et vous confie la suite : **construire la pipe de nettoyage qui transforme le dataset brut en dataset prêt à l'entraînement, de façon reproductible, et documenter l'analyse des biais**.

À partir de ce brief, la règle change : plus de nettoyage manuel dans un notebook exploratoire. Chaque transformation doit être codée dans un script ou une fonction réutilisable, paramétrée et testable. L'objectif est qu'un nouveau développeur puisse rejouer la pipe en une commande et retomber sur le même dataset de sortie.

---

## Objectif principal

Implémenter une pipeline de préparation des données reproductible (nettoyage + détection et atténuation de biais), produire un dataset nettoyé versionné, et rédiger une note argumentée sur les risques éthiques identifiés et les choix de traitement effectués.

---

## Prérequis

- Brief 1 complété : datasheet, documentation du cycle de vie, diagnostic de qualité produits
- Liste des actions correctives identifiées dans `docs/audit_v1.md`

---

## Étapes du projet

### 1. Architecture de la pipeline

Créer une structure de projet :

```
src/
  pipeline/
    __init__.py
    load.py         # chargement du JSONL
    clean.py        # fonctions de nettoyage
    bias.py         # détection de biais
    validate.py     # contrôles de sortie
    run.py          # orchestration
data/
  raw/              # input non modifié
  interim/          # étapes intermédiaires
  processed/        # dataset final
tests/
  test_clean.py
```

Chaque fonction de nettoyage prend un `DataFrame` en entrée, retourne un `DataFrame` en sortie. Pas d'effet de bord. Paramètres explicites.

### 2. Data-cleaning

Implémenter au minimum les traitements suivants :

| Étape | Fonction | Traitement |
|---|---|---|
| Chargement | `load_jsonl()` | lit le fichier et aplatit `output.*` en colonnes `categorie`, `priorite`, `reponse_suggeree` |
| Doublons | `drop_duplicates()` | suppression des doublons exacts + quasi-doublons via hash normalisé |
| Normalisation texte | `normalize_text()` | strip, collapse espaces multiples, uniformisation des guillemets, gestion casse en préservant le texte original dans `input_raw` |
| Valeurs manquantes | `handle_missing()` | stratégie explicite selon le champ (suppression si `input` vide, imputation si `reponse_suggeree` vide via règle documentée) |
| Outliers de longueur | `flag_length_outliers()` | détection via z-score ou IQR sur les longueurs, décision de conservation/suppression documentée |
| Validation de schéma | `validate()` | vérifie que `categorie` ∈ {liste fermée}, `priorite` ∈ {`haute`, `normale`}, aucun champ obligatoire vide |

Chaque fonction a :

- Une docstring qui explique le traitement et les paramètres
- Au moins un test unitaire Pytest
- Un log via Loguru qui compte les lignes entrantes, sortantes et supprimées

### 3. Audit de biais

Produire un notebook `notebook_brief2_bias.ipynb` qui investigue :

- **Biais de représentation** — distribution catégorie × priorité, identification des combinaisons sous-représentées
- **Biais linguistique** — longueur moyenne et registre (formel / informel) par catégorie, repérage de corrélations suspectes (ex. toutes les demandes courtes classées en `Information générale`)
- **Biais de réponse** — le champ `reponse_suggeree` reproduit-il un style uniforme par catégorie ? Y a-t-il des formulations qui pourraient être perçues comme condescendantes ou dégradantes pour certains segments ?
- **Données sensibles** — repérage par regex ou NER léger des occurrences de noms, emails, numéros de téléphone, adresses dans les champs `input` et `reponse_suggeree`

Pour chaque biais identifié, proposer une stratégie d'atténuation (à appliquer au Brief 3 ou plus tard) et documenter la décision prise pour le dataset nettoyé (masquer, supprimer, conserver tel quel avec justification).

### 4. Anonymisation

Implémenter `src/pipeline/anonymize.py` qui :

- Détecte et masque emails, numéros de téléphone, URLs
- Remplace les prénoms/noms détectés par un placeholder `[NOM]`
- Préserve la lisibilité du texte pour l'entraînement du modèle

Les choix sont à justifier : un placeholder générique préserve le contexte, une suppression pure peut casser la syntaxe. Documenter.

### 5. Orchestration et reproductibilité

Écrire `src/pipeline/run.py` qui enchaîne toutes les étapes et produit :

```
data/processed/dataset_fastia_clean_v1.jsonl
data/processed/dataset_fastia_clean_v1.meta.json  # métadonnées : date, hash, stats avant/après
```

Le script doit être lançable via :

```bash
python -m src.pipeline.run --input data/raw/dataset_fastia_module1.jsonl --output data/processed/dataset_fastia_clean_v1.jsonl
```

### 6. Note réglementaire et éthique

Rédiger `docs/risques_ethiques.md` (1 à 2 pages) couvrant :

- **Cartographie des risques éthiques** identifiés au Brief 1 et au Brief 2
- **Référentiel réglementaire** applicable au cas FastIA — RGPD (traitement de données clients, minimisation, droit à l'oubli) et AI Act (catégorisation du système, obligations selon le niveau de risque)
- **Choix effectués** dans la pipeline et leur justification au regard de ces textes
- **Risques résiduels** — ce que la pipeline ne résout pas, à surveiller en aval

---

## Livrables

- **Dépôt GitHub** mis à jour avec :
  - Le code de la pipeline dans `src/pipeline/`
  - Les tests Pytest dans `tests/`
  - Le dataset nettoyé versionné dans `data/processed/`
  - Le notebook d'audit de biais `notebook_brief2_bias.ipynb`
  - `docs/risques_ethiques.md`
- **README.md** complété avec :
  - Description de chaque étape de la pipeline
  - Commande de lancement
  - Tableau avant/après (effectifs, distribution des catégories, % de doublons supprimés, etc.)
- Les tests Pytest passent tous (`pytest tests/ -v`)

---

## Charge de travail estimée

6 à 7 heures

---

## Ressources

- [CNIL — AI Act et RGPD](https://www.cnil.fr/fr/intelligence-artificielle)
- [spaCy — détection d'entités nommées en français](https://spacy.io/models/fr)
- [Loguru — journalisation Python](https://loguru.readthedocs.io)
- [Pytest — fixtures et paramétrage](https://docs.pytest.org)

---

## Bonus

- Ajouter une étape `detect_language()` qui flague les demandes non francophones
- Calculer et tracer une matrice de corrélation entre `longueur(input)`, `categorie`, `priorite` pour étayer l'analyse de biais
- Publier un rapport HTML de profilage (ex. `ydata-profiling`) sur le dataset brut et le dataset nettoyé, et les comparer
