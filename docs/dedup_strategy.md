# Stratégie de Déduplication Cross-Canal

## 1. Objectif
Identifier les clients qui envoient la même demande via plusieurs canaux (ex: un email suivi d'un chat 2 heures plus tard car ils n'ont pas eu de réponse).

## 2. Méthode d'Identification
L'identification repose sur deux piliers :

### A. Empreinte Sémantique
Pour chaque demande, nous calculons un hash MD5 basé sur :
1. Le corps du message (tronqué aux **300 premiers caractères**).
2. Une normalisation stricte (minuscules, suppression des espaces blancs multiples, suppression des caractères spéciaux de ponctuation).

### B. Fenêtre Temporelle et Identité
Un message est considéré comme un doublon cross-canal si :
1. Il possède le même **expéditeur** (email ou identifiant anonymisé).
2. Il a été reçu dans une fenêtre de **48 heures** autour d'un message existant.
3. Il possède une **empreinte sémantique** identique.

## 3. Gestion des Doublons
Contrairement à la déduplication interne à un lot qui supprime les lignes, la déduplication cross-canal **conserve** les données mais les marque.

Une nouvelle colonne `dedup_status` est ajoutée à la table `demandes` :
- `original` : Premier message identifié ou message unique.
- `cross_channel_duplicate` : Message identifié comme doublon d'un message déjà existant en base ou dans le même lot.

## 4. Performance
Pour garantir la rapidité des recherches de doublons lors de l'ingestion, un index a été ajouté sur la colonne `received_at`.
