# Brief 2 — Brancher web et chat, harmoniser, segmenter

## Contexte du projet

Avec le canal email branché au Brief 1, FastIA dispose enfin d'une ingestion industrialisée. Mais la majorité du volume passe en réalité par les **deux autres canaux** : le formulaire de contact du site web (JSON livré par un webhook) et le chat en direct (export quotidien CSV depuis l'outil de chat). Chacun a sa structure, ses biais et ses propres pièges.

Votre mission : **brancher ces deux sources dans la pipeline, les harmoniser** au modèle commun défini au Brief 1, **dédupliquer cross-canal** (un client mécontent peut envoyer la même demande par chat puis par email pour faire pression), et surtout **comprendre comment chaque canal déforme la distribution du dataset global** avant de réentraîner.

---

## Objectif principal

Implémenter les loaders web et chat, mettre en place une couche d'intégration unifiée avec déduplication cross-canal, et produire une analyse segmentée par canal qui éclaire les choix d'augmentation et de rééquilibrage à venir.

---

## Prérequis

- Brief 1 M3 complété : schéma SQL étendu, `email_loader` fonctionnel, mode `ingest` opérationnel
- Échantillons fournis dans `data/raw/` :
  - `formulaires_web.json` — 1 fichier, 1 ligne JSON par soumission
  - `chat_logs.csv` — exports CSV quotidiens du chat

---

## Étapes du projet

### 1. Loader formulaires web

Créer `src/sources/web_loader.py` :

```python
def load_web_jsonl(path: Path) -> Iterator[RawDemande]:
    ...
```

Le format des soumissions :

```json
{
  "submission_id": "WEB-2026-04-12-7831",
  "submitted_at": "2026-04-12T14:23:11Z",
  "form": {
    "email": "client@example.com",
    "subject": "Mon site ne charge plus",
    "message": "Bonjour, ...",
    "consent_marketing": false
  },
  "user_agent": "Mozilla/5.0 ...",
  "ip_country": "FR"
}
```

Particularités à gérer :

- Le `subject` est parfois absent → fallback sur les 60 premiers caractères du `message`
- Le `consent_marketing` n'est **pas** une donnée à ingérer pour la pipeline IA — minimisation RGPD : on l'écarte explicitement
- L'`ip_country` est utile comme **métadonnée** (bias géographique) mais pas comme donnée d'entraînement → range dans `canal_metadata`

### 2. Loader chat

Créer `src/sources/chat_loader.py`. Le CSV a un format conversationnel :

```csv
session_id,timestamp,role,message
CHAT-9921,2026-04-12T09:01:03Z,visitor,bonjour je n arrive pas a payer
CHAT-9921,2026-04-12T09:01:14Z,agent,Bonjour, pouvez-vous préciser l'erreur ?
CHAT-9921,2026-04-12T09:01:46Z,visitor,erreur 502 quand je clique payer
CHAT-9921,2026-04-12T09:02:11Z,agent,Merci, je transfère au support technique.
```

Particularités :

- Une **demande client** = la concaténation des messages `visitor` d'une même `session_id`, dans l'ordre chronologique
- Les messages `agent` sont écartés du `body` mais conservés dans `canal_metadata.transcript_complet`
- Une session sans aucun message `visitor` est rejetée (avec log)
- Penser au cas d'une session **non clôturée** ou tronquée (dernière ligne d'un export quotidien)

### 3. Couche d'intégration unifiée

Créer `src/sources/integrate.py` qui expose un point d'entrée unique :

```python
def ingest(source: Literal["email", "web", "chat"], path: Path) -> IngestReport:
    ...
```

Cette fonction :

1. Sélectionne le bon loader (dispatch sur `source`)
2. Applique les traitements communs M2 (normalisation, anonymisation)
3. Appelle la **déduplication cross-canal** (étape suivante)
4. Insère en base avec idempotence
5. Retourne un `IngestReport` structuré (dataclass) : compteurs, rejets motivés, exemples d'erreurs

### 4. Déduplication cross-canal

C'est la partie subtile. Implémenter `src/sources/dedup.py` :

- **Dédup intra-source** : déjà fait via la contrainte `(canal, external_id)` au B1
- **Dédup cross-source** : un même client peut écrire la même chose par deux canaux différents — on ne veut pas l'apprendre deux fois

Stratégie proposée (à challenger et justifier dans `docs/dedup_strategy.md`) :

- Calcul d'une empreinte sémantique légère : `hash(normalize(body[:300]))`
- Seuil temporel : deux empreintes identiques émises par le **même `sender` (ou même email anonymisé)** dans une **fenêtre de 48h** → conserver la première, marquer la seconde `dedup_status = "cross_channel_duplicate"`
- **Ne pas supprimer physiquement** les doublons cross-canal — les marquer en base (nouvelle colonne `dedup_status`) car l'info "le client a relancé par chat 2h après son email" est précieuse pour les briefs M4+

Tests Pytest sur :
- Cas trivial : deux exemplaires identiques → 1 actif, 1 marqué
- Cas faux-positif à éviter : deux clients différents avec le même `body` (ex. "bonjour") → les deux conservés
- Cas hors fenêtre : même empreinte à 5 jours d'intervalle → les deux conservés

### 5. Analyse segmentée par canal

Notebook `notebook_brief2_module3.ipynb` qui répond à :

- **Volumétrie** par canal (effectifs et %)
- **Distribution des longueurs** `body` par canal (histogramme + box) — confirmer / infirmer l'intuition "chat = court, email = long"
- **Distribution des catégories** par canal (depuis le dataset M2 + classifs déjà faites + nouvelles ingestions étiquetées si dispo) — repérer les sur-représentations (ex. chat surreprésente `Information générale`, email surreprésente `Réclamation`)
- **Données sensibles** par canal — les regex M2 trouvent-elles plus de PII dans certains canaux ? (le chat a-t-il plus de prénoms en clair ? le web a-t-il moins de signatures ?)
- **Saisonnalité** : volume par canal × jour de la semaine × heure
- **Qualité** : taux de rejet à l'ingestion par canal, motifs principaux

Conclure par une section **"Biais introduits par la multi-source"** qui liste les biais **nouveaux** vs ceux déjà identifiés en M2 sur le dataset mono-source.

### 6. Évolution de la stratégie d'augmentation

Le `docs/plan_augmentation.md` du M2 ciblait des combinaisons `catégorie × priorité` sous-représentées. À la lumière du B2 M3, il faut probablement raisonner en **`catégorie × canal`** voire **`catégorie × priorité × canal`**.

Mettre à jour `docs/plan_augmentation.md` (section "Révision M3") :

- Identifier les triplets sous-représentés
- Décider si on augmente synthétiquement ou si on va chercher plus de data réelle d'un canal donné
- Justifier (un compromis qualité / coût / représentativité)

### 7. Mise à jour de la pipeline et du data_lifecycle

- Étendre la commande `python -m src.pipeline.run ingest --source <web|chat>` aux deux nouveaux loaders
- Mettre à jour `docs/data_lifecycle.md` : nouveau schéma de flux multi-sources, points de vigilance dédup, nouvelles colonnes `dedup_status`
- Mettre à jour la **datasheet** : les sources web et chat ont chacune leur fiche

---

## Livrables

- **Dépôt GitHub** mis à jour avec :
  - `src/sources/web_loader.py`, `chat_loader.py`, `integrate.py`, `dedup.py` + tests Pytest
  - `notebook_brief2_module3.ipynb`
  - `docs/dedup_strategy.md`, `docs/source_web.md`, `docs/source_chat.md`
  - Mises à jour : `docs/datasheet.md`, `docs/data_lifecycle.md`, `docs/plan_augmentation.md`
- **README.md** mis à jour avec les 3 commandes d'ingestion et un schéma multi-canal
- Migration SQL ajoutant la colonne `dedup_status` (Alembic) + index utiles
- Tous les tests passent

---

## Charge de travail estimée

5 à 6 heures

---

## Ressources

- [`csv` et `pandas.read_csv` — gérer les CSV mal formés](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [Pydantic v2 — modèles et validators](https://docs.pydantic.dev/latest/)
- [Datasketch — MinHash pour dédup approchée (alternative au hash naïf)](https://ekzhu.com/datasketch/minhash.html)
- [Documentation RGPD — principe de minimisation](https://www.cnil.fr/fr/principes-cles/rgpd-minimisation-donnees)

---

## Bonus

- Remplacer le `hash(normalize(body[:300]))` par une **dédup sémantique** via embeddings légers (`sentence-transformers/all-MiniLM-L6-v2`) et comparaison cosinus — comparer faux-positifs / faux-négatifs avec la version naïve
- Ajouter une source **MongoDB** (ex. logs d'un produit interne FastIA stockés en NoSQL) — montre que la pipeline absorbe le NoSQL aussi
- Brancher l'API FastIA M1 sur les nouvelles ingestions : pour chaque demande nouvellement insérée sans `categorie`, appeler `POST /predict` et enrichir la base
