# Datasheet - Dataset FastIA Module 1

## 1. Motivation
* **Pourquoi le dataset a-t-il été créé ?** Pour entraîner et évaluer un modèle de classification d'intentions et de priorisation pour le service client de FastIA.
* **Qui a financé la création ?** Projet de formation interne FastIA.

## 2. Composition
* **Nombre d'instances :** 86 exemples.
* **Structure :** Chaque instance contient un `input` (texte utilisateur), une `categorie` (5 classes), une `priorite` (2 classes) et une `reponse_suggeree`.
* **Répartition des catégories :** Équilibrée (~20% par classe).
* **Données confidentielles (PII) :** Aucune détectée (audit Regex et NER). Les noms propres sont absents ou fictifs.

## 3. Processus de collecte
* **Origine :** Données synthétiques générées pour simuler des interactions réelles avec un CRM.
* **Mécanisme :** Échantillonnage stratifié pour garantir la représentativité des classes métier.

## 4. Considérations Éthiques
* **Biais identifiés :** Les "Informations générales" sont plus courtes en moyenne, ce qui peut induire un biais de prédiction basé sur la longueur.
* **Impact :** Le modèle pourrait sous-prioriser des demandes complexes si elles sont formulées de manière concise.
* **Confidentialité :** Conforme RGPD par l'absence de données personnelles réelles.
