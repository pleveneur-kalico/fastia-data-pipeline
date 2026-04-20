# Data Lifecycle - Flux de données FastIA

## 1. Schéma du flux (Pipeline)
1.  **Source :** Fichier JSONL brut (`dataset_fastia_module1.jsonl`).
2.  **Ingestion :** Script Python (Pandas) avec aplatissement des dictionnaires imbriqués.
3.  **Audit :** Vérification des types, doublons et valeurs manquantes.
4.  **Nettoyage/Normalisation :** Mise en minuscule et suppression des espaces superflus pour le hachage.
5.  **Validation :** Revue qualitative sur échantillon (20 lignes).
6.  **Export :** Synthèse JSON pour suivi de version.

## 2. Points de rupture potentiels (Bottlenecks)
* **Qualité en entrée :** Si le schéma JSON change (ex: renommage de 'output' en 'label'), le chargement échouera.
* **Volume :** Avec seulement 86 lignes, la représentativité statistique est fragile pour des cas rares.
* **Dérive (Drift) :** De nouvelles catégories de demandes (ex: "Partenariats") ne sont pas prévues dans la nomenclature actuelle.
* **Faux positifs NER :** La détection automatique de PII peut rater des noms propres mal orthographiés ou en milieu de phrase.

## 3. Maintenance
* **Fréquence de révision :** Après chaque itération de modèle (Module 2).
* **Propriétaire :** Équipe Data Engineering FastIA.
