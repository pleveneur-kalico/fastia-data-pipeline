# Brief 3 — Anticiper un nouveau besoin métier et planifier l'évolution data

## Contexte du projet

La pipeline FastIA absorbe désormais trois canaux et harmonise tout cela en base. Lors du dernier comité produit, le directeur métier a posé une nouvelle ambition :

> *« Un tiers de nos demandes entrantes ne sont plus en français — on a beaucoup de PME franco-espagnoles et anglophones depuis l'ouverture de l'offre B2B. On voudrait que l'IA détecte automatiquement la langue d'origine et remonte ces demandes en priorité haute sur le canal dédié, parce qu'on a une équipe spécialisée mais on ne sait pas leur router le bon volume. Et accessoirement, savoir si le client est mécontent ou pas dès la lecture, ça aiderait à prioriser les réclamations sévères. »*

Vous n'allez **pas implémenter cette feature de bout en bout** dans ce brief. Vous allez faire ce qu'un bon développeur IA fait avant de coder : **cadrer le besoin, identifier les données qui manquent, vérifier ce qui est accessible, et planifier l'évolution de la pipeline** sans casser le M2 et le début du M3.

---

## Objectif principal

Cadrer un nouveau besoin métier sur le projet FastIA existant, identifier et qualifier les sources de données nécessaires (internes et externes), évaluer leur accessibilité, et produire un plan d'évolution de la pipeline avec une preuve de concept minimale d'une seule étape d'enrichissement.

---

## Prérequis

- Briefs 1 et 2 du Module 3 complétés : pipeline multi-source fonctionnelle, base à jour
- `docs/datasheet.md`, `docs/data_lifecycle.md`, `docs/plan_augmentation.md` à jour à fin B2

---

## Étapes du projet

### 1. Cadrage du besoin métier

Rédiger `docs/cadrage_besoin_metier.md` (1 à 2 pages) en répondant a minima à :

- **Reformulation** du besoin en une phrase opérationnelle (pas marketing)
- **Personas concernés** : qui produit la donnée, qui la consomme, qui décide en aval
- **Critères de succès** mesurables : ex. "détecter la langue avec ≥ 95% d'accuracy sur un échantillon de validation FR/EN/ES de 200 lignes" — pas "ça marche bien"
- **Hypothèses à vérifier** : a-t-on vraiment 1/3 de demandes non-FR ? sur quels canaux ? sur quelle période ?
- **Non-objectifs** explicites : ce que ce besoin n'inclut PAS (ex. on ne fait pas de traduction automatique, on ne change pas l'API publique)
- **Risques éthiques préliminaires** : détection de langue → corrélation possible avec origine géographique → AI Act, classification d'un système ; détection de sentiment → décision automatisée potentiellement défavorable

### 2. Vérification empirique sur les données existantes

Avant de rajouter quoi que ce soit, **regarder la base actuelle**. Notebook `notebook_brief3_module3.ipynb` :

- **Détection de langue exploratoire** sur les `body` actuellement en base via `langdetect` ou `fasttext`
- Quelle est la **vraie répartition** des langues, par canal ?
- L'hypothèse métier "1/3 non-FR" est-elle vérifiée ?
- Pour le sentiment : éventuellement passer un petit modèle FR (`cmarkea/distilcamembert-base-sentiment` ou équivalent) sur un échantillon de 100 lignes et regarder la distribution

Ce passage est volontairement court (1h) — l'idée est de **ramener une réponse chiffrée** à la prochaine réunion, pas de produire un modèle.

### 3. Identification des sources de données pertinentes

Rédiger `docs/sources_data_evaluation.md` qui présente, sous forme de tableau, les sources candidates pour répondre au besoin :

| Source | Type | Accessible ? | Qualité | Coût | RGPD | Verdict |
|---|---|---|---|---|---|---|
| Détection de langue locale (`langdetect`) | librairie Python | oui, gratuit | bon FR/EN, moyen ES court | nul | OK | retenir |
| Détection de langue par `fasttext` (modèle pré-entraîné `lid.176.bin`) | modèle binaire 130 MB | oui | excellent toutes langues | nul (offline) | OK | retenir si latence acceptable |
| API Google Cloud Translation `detectLanguage` | REST | oui sur compte payant | excellent | facturé / requête | données envoyées hors UE | à éviter |
| Sentiment FR — modèle HuggingFace `cmarkea/distilcamembert-base-sentiment` | modèle 270 MB | oui, libre | bon mais entraîné sur reviews ≠ support client | nul (offline) | OK | retenir comme baseline |
| Sentiment FR — fine-tuner notre propre modèle sur 200 demandes annotées en interne | dataset à constituer | nécessite annotation manuelle | inconnu, à mesurer | temps humain | OK | proposer en B2 itération suivante |

**Pour chaque ligne**, vérifier réellement :

- L'**existence** (URL, package PyPI, ou contact fournisseur)
- La **disponibilité** (compte requis ? clé API ? quota ?)
- L'**accès** (peut-on installer / appeler depuis l'environnement FastIA ?)
- Les **contraintes opérationnelles** (latence, RAM nécessaire, dépendance réseau)
- Les **contraintes légales** (transfert hors UE, conditions d'utilisation)

### 4. Plan d'évolution de la pipeline

Rédiger `docs/plan_evolution_pipeline.md` couvrant :

- **Schéma cible** : où s'insère l'étape d'enrichissement (`enrich_language`, `enrich_sentiment`) — au moment de l'ingestion ? après le cleaning ? avant le stockage ?
- **Évolution du schéma SQL** : nouvelles colonnes (`langue`, `langue_confidence`, `sentiment`, `sentiment_score`) — proposer la migration Alembic à venir, ne pas l'appliquer encore
- **Impact sur le modèle FastIA M1** : si la priorité doit dépendre de la langue, faut-il le reentraîner avec un nouveau prompt ? ou ajouter une règle métier en post-prédiction ? (*spoiler* : règle métier d'abord, fine-tuning si besoin avéré — c'est moins cher et plus auditable)
- **Roadmap proposée** sur les briefs / modules suivants

### 5. Preuve de concept — une seule étape d'enrichissement

Implémenter `src/pipeline/enrich.py` avec **une seule** étape complète, au choix entre `enrich_language()` et `enrich_sentiment()` (pas les deux — l'objectif est la profondeur, pas la largeur) :

- Fonction pure : `RawDemande` ou `pd.DataFrame` en entrée → enrichi en sortie
- Un test Pytest sur 5 cas (ex. pour `enrich_language` : un FR clair, un EN clair, un ES clair, un mix FR/EN, une chaîne vide)
- Une commande CLI : `python -m src.pipeline.enrich --field language --input ... --output ...`
- Mesure du **coût d'inférence** : temps moyen par ligne, RAM consommée

### 6. Note d'éco-conception

Rédiger `docs/ecoconception_enrichissement.md` court (1 page) :

- Quelle option choisie consomme le moins de ressources, à qualité égale ?
- Peut-on **filtrer en amont** pour ne pas appeler le modèle sur tout le dataset ? (ex. : ne pas relancer `enrich_language` sur les lignes déjà enrichies → idempotence)
- Si on doit ré-enrichir l'historique complet, combien de minutes / kWh approximativement ? Vaut-il la peine ?

### 7. Mise à jour de la documentation projet

- `docs/datasheet.md` — section "Champs dérivés" décrivant les futurs `langue` et `sentiment` (même si non encore en base)
- `docs/data_lifecycle.md` — ajout d'une étape "Enrichissement" entre cleaning et stockage
- `docs/risques_ethiques.md` — section "Risques liés à la détection automatique" (catégorisation indirecte par langue, biais socio-éco)

---

## Livrables

- **Dépôt GitHub** mis à jour avec :
  - `docs/cadrage_besoin_metier.md`
  - `docs/sources_data_evaluation.md`
  - `docs/plan_evolution_pipeline.md`
  - `docs/ecoconception_enrichissement.md`
  - `notebook_brief3_module3.ipynb`
  - `src/pipeline/enrich.py` (une étape implémentée + tests)
  - Mises à jour : `docs/datasheet.md`, `docs/data_lifecycle.md`, `docs/risques_ethiques.md`
- **README.md** finalisé pour M3 : section "Roadmap data" avec ce qui est fait (B1, B2, B3 PoC) et ce qui reste à faire (généralisation enrichissement, migration SQL, ré-entraînement éventuel)

---

## Charge de travail estimée

3 à 4 heures

---

## Ressources

- [`langdetect` — détection de langue rapide](https://pypi.org/project/langdetect/)
- [`fasttext` — `lid.176` modèle de détection de langue](https://fasttext.cc/docs/en/language-identification.html)
- [`cmarkea/distilcamembert-base-sentiment` — sentiment FR](https://huggingface.co/cmarkea/distilcamembert-base-sentiment)
- [AI Act — annexes (catégorisation des systèmes IA selon le risque)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- [Green Algorithms — estimer l'empreinte carbone d'un calcul](https://www.green-algorithms.org/)

---

## Bonus

- Implémenter **les deux** étapes d'enrichissement et comparer leur coût d'inférence
- Mettre en place une stratégie de **cache** sur l'enrichissement (clé : `hash(body)`) pour ne pas recalculer si le body est inchangé
- Ouvrir une discussion (issue GitHub avec template) sur le ré-entraînement éventuel de l'API FastIA M1 avec les nouveaux champs en entrée — à transmettre au futur Module 4
