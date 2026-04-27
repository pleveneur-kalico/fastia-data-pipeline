# Brief 1 — Brancher la première nouvelle source : les emails clients

## Contexte du projet

La pipeline FastIA tourne en interne depuis la fin du Module 2 : un dataset propre, augmenté, versionné en base PostgreSQL, et un fine-tuning rejouable. Mais ce dataset a été construit à partir d'une seule extraction figée, alors qu'**en production les demandes clients FastIA arrivent en continu par trois canaux différents** : emails support, formulaires du site web, chat en direct.

Jusqu'ici, ces trois flux étaient agrégés à la main par l'équipe support : quelqu'un copiait-collait, harmonisait grossièrement et envoyait un fichier Excel à l'équipe data. Cette époque est révolue. Votre manager vous confie l'**industrialisation de l'ingestion multi-source**, à commencer par le canal historique : **les emails**. Un script de collecte a déjà été ébauché par un collègue avant son départ — il fonctionne mal, n'est pas testé, et n'écrit pas en base. C'est la première brique à reprendre.

---

## Objectif principal

Étendre le schéma SQL pour accueillir l'origine des demandes (canal et métadonnées), implémenter un loader robuste pour la source emails (format `mbox`), réparer le script de collecte hérité, et documenter cette nouvelle source comme une source de premier niveau de la pipeline FastIA.

---

## Prérequis

- Module 2 complété : pipeline `src/pipeline/`, base PostgreSQL/MySQL avec table `demandes`, dataset v2 chargé
- Docker (ou installation locale) pour la base de données
- Échantillon `data/raw/emails_fastia.mbox` fourni avec ce module

---

## Étapes du projet

### 1. Cadrage de la nouvelle source

Avant tout code, prendre 30 minutes pour répondre dans `docs/source_email.md` :

- **Qui** produit cette donnée ? (clients via leur boîte mail)
- **Quelle volumétrie** réelle estimer ? (à partir du fichier fourni, extrapoler à un mois, un an)
- **Quel format brut** (`mbox`) et quels champs portent une info exploitable (`From`, `Subject`, `Date`, `Body`, `Message-ID`, `In-Reply-To`)
- **Quelles données personnelles** sont nécessairement présentes (adresse email, nom dans la signature, références client) → rappel des règles M2 sur l'anonymisation
- **Quels biais ce canal va-t-il introduire** dans le dataset global ? (clientèle email = profil plus âgé, demandes plus longues et plus formelles que le chat — à vérifier au Brief 2)

### 2. Évolution du schéma SQL

Le schéma M2 a anticipé un champ `canal` mais ne capture pas les métadonnées par source. Faire évoluer la table `demandes` pour ajouter :

| Colonne | Type | Justification |
|---|---|---|
| `received_at` | `TIMESTAMP` | date d'arrivée côté client (pas date d'insertion) — utile pour analyser la saisonnalité |
| `external_id` | `VARCHAR(255)` | identifiant natif du canal (ex. `Message-ID` pour email) — clé d'idempotence |
| `canal_metadata` | `JSONB` (PostgreSQL) ou `JSON` (MySQL) | sac de métadonnées propres au canal (sujet, thread, user-agent, etc.) |

Contraintes :

- **Index unique** sur `(canal, external_id)` pour empêcher la double-insertion
- **Migration versionnée** via Alembic (ou `alembic-mysql`) — un nouveau fichier de migration, pas de modification manuelle du DDL
- La migration doit être **réversible** (`upgrade` + `downgrade` testés)
- Aucune ligne existante du dataset v2 ne doit être perdue

### 3. Implémentation du loader email

Créer `src/sources/email_loader.py` exposant :

```python
def load_mbox(path: Path) -> Iterator[RawDemande]:
    """Itère sur les messages d'un fichier mbox et yield un RawDemande par mail."""
```

Avec un dataclass / Pydantic model `RawDemande` :

```python
class RawDemande(BaseModel):
    canal: Literal["email", "web", "chat"]
    external_id: str
    received_at: datetime
    sender: str | None       # avant anonymisation
    subject: str | None
    body: str
    canal_metadata: dict
```

Le loader doit :

- Décoder correctement les corps en `quoted-printable` et `base64`
- Décoder les en-têtes encodés `=?utf-8?...?=`
- Gérer les emails **multipart** (préférer `text/plain`, fallback HTML → texte via `BeautifulSoup`)
- **Couper les signatures et les citations** (lignes commençant par `>`, blocs `-- \n`, etc.) — un `strip_quoted_text()` dédié
- Rejeter (avec log) les messages sans corps utilisable

### 4. Réparation du script hérité

Un fichier `src/sources/legacy_collect.py` est fourni dans le dépôt M3 (à récupérer dans les ressources du module). Il contient au moins **trois bugs** :

1. Un encoding hardcodé qui plante sur les emails non-UTF-8
2. Une absence de gestion d'idempotence (les ré-exécutions doublent les lignes)
3. Une perte de la timezone sur `received_at`

Votre travail :

- Identifier les bugs en lisant le code et en lançant le script sur l'échantillon
- Corriger sans tout réécrire (l'objectif n'est pas la reprise complète, c'est de tenir un héritage)
- Ajouter un **test de non-régression** par bug corrigé dans `tests/test_legacy_collect.py`

### 5. Intégration au reste de la pipeline

Adapter `src/pipeline/run.py` pour qu'il accepte un nouveau mode :

```bash
python -m src.pipeline.run ingest --source email --input data/raw/emails_fastia.mbox
```

Ce mode doit :

1. Charger les emails via `email_loader`
2. Appliquer les traitements de cleaning du M2 (normalisation, déduplication interne au lot)
3. Appliquer l'anonymisation du M2 sur `body`
4. Insérer dans la base avec gestion d'idempotence sur `(canal, external_id)`
5. Logger un récapitulatif : reçus, dédupliqués, anonymisés, insérés, rejetés

À ce stade, la **catégorisation et la priorité** sont laissées vides — elles seront produites par l'API FastIA M1 dans un brief ultérieur.

### 6. Documentation

Mettre à jour :

- `docs/datasheet.md` — ajouter une section **Sources** listant chaque canal avec sa fiche
- `docs/source_email.md` — fiche détaillée de la source email (format, fréquence, volumétrie réelle observée, biais attendu, contraintes RGPD spécifiques)
- `docs/data_lifecycle.md` — mettre à jour le schéma de flux pour montrer la nouvelle entrée

---

## Livrables

- **Dépôt GitHub** mis à jour avec :
  - `src/sources/email_loader.py` + tests
  - `src/sources/legacy_collect.py` corrigé + tests de non-régression
  - Migration Alembic réversible (`alembic/versions/<hash>_add_canal_metadata.py`)
  - Mise à jour de `src/pipeline/run.py` (mode `ingest`)
  - `docs/source_email.md`, `docs/datasheet.md` et `docs/data_lifecycle.md` mis à jour
- **README.md** mis à jour : commande d'ingestion, schéma SQL actualisé, prérequis migration
- Les tests passent : `pytest tests/ -v`

---

## Charge de travail estimée

4 à 5 heures

---

## Ressources

- [Python `mailbox` — lire un fichier mbox](https://docs.python.org/3/library/mailbox.html)
- [Python `email.parser` — décodage des en-têtes et corps](https://docs.python.org/3/library/email.parser.html)
- [Alembic — autogenerate et migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [BeautifulSoup — extraire du texte d'un HTML](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PostgreSQL — type `JSONB` et indexation](https://www.postgresql.org/docs/current/datatype-json.html)

---

## Bonus

- Détecter automatiquement les **threads** (via `In-Reply-To` / `References`) et stocker un `thread_id` qui regroupe les échanges d'une même conversation
- Implémenter un **mode incrémental** : `--since 2026-04-01` ne réinjecte que les emails postérieurs à cette date
- Ajouter un endpoint `POST /ingest/email` à l'API FastIA M1 qui accepte un upload mbox et déclenche la pipeline (préfigure le M3 B2)
