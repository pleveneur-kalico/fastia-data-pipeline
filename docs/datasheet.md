# Datasheet - Dataset FastIA Module 1

## 1. Motivation
* **Pourquoi le dataset a-t-il été créé ?** Pour entraîner et évaluer un modèle de classification d'intentions et de priorisation pour le service client de FastIA.
* **Qui a financé la création ?** Projet de formation interne FastIA.

## 2. Composition
* **Nombre d'instances :** ~500 exemples (v2 augmentée).
* **Structure :** Chaque instance contient un `input` (texte utilisateur), une `categorie`, une `priorite`, une `reponse_suggeree`, un `canal` (web/email/chat), un `external_id`, des `canal_metadata` et un `dedup_status`.
* **Répartition des catégories :** Équilibrée (100 exemples par classe).

## 3. Sources et Collecte
* **JSONL Historique :** Données synthétiques initiales (Module 1).
* **Emails Clients :** Ingestion `.mbox`. Nettoyage des signatures et citations.
* **Formulaires Web :** Ingestion JSONL. Fallback sujet sur le corps du message.
* **Chat en Direct :** Ingestion CSV. Agrégation par session et capture du transcript complet.
* **Mécanisme :** Ingestion automatisée avec gestion de l'idempotence et marquage des doublons cross-canal (fenêtre de 48h).

## 4. Considérations Éthiques
* **Biais identifiés :** Les "Informations générales" sont plus courtes en moyenne, ce qui peut induire un biais de prédiction basé sur la longueur.
* **Impact :** Le modèle pourrait sous-prioriser des demandes complexes si elles sont formulées de manière concise.
* **Confidentialité :** Conforme RGPD par l'absence de données personnelles réelles.
