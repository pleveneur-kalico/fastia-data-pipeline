# Note d'éco-conception — Enrichissement (M3B3)

Cette note analyse l'impact environnemental et technique de l'ajout de l'étape d'enrichissement dans la pipeline FastIA.

## 1. Comparaison des options et sobriété numérique

Pour la détection de langue, nous avons comparé trois approches :
*   **langdetect (Choisi pour PoC)** : Très sobre. Consommation CPU négligeable, aucune RAM additionnelle persistante (modèles chargés à la volée ou statistiques légères).
*   **fasttext** : Demande le chargement d'un binaire de 120MB. Plus gourmand en stockage et en RAM initiale, mais extrêmement rapide en inférence.
*   **LLM (via Ollama)** : Très énergivore. Le ratio bénéfice/coût pour une simple détection de langue est disproportionné.

**Verdict** : `langdetect` est l'option la plus sobre pour un démarrage, avec une empreinte carbone quasi nulle sur les volumes actuels.

## 2. Stratégie d'idempotence et filtrage

Pour minimiser les calculs inutiles, nous implémenterons les mécanismes suivants :
*   **Filtre sur l'état** : Ne déclencher `enrich_language` que si la colonne `langue` est `NULL` ou `unknown` dans la base.
*   **Seuil de déclenchement** : Ne pas lancer de détection sur les textes de moins de 10 caractères (trop peu de signal, risque d'erreur élevé, économie de cycles CPU).
*   **Mise en cache** : Sur les flux répétitifs (ex: Chat), utiliser un cache de hash pour éviter de re-détecter la langue d'un message identique.

## 3. Estimation de l'impact sur l'historique

Si nous devons enrichir l'historique complet (env. 500 lignes) :
*   **Temps CPU** : ~1 seconde au total avec `langdetect`.
*   **Consommation électrique** : Négligeable (inférieure à 0.001 kWh).
*   **Recommandation** : L'enrichissement de l'historique est fortement recommandé car il apporte une valeur métier élevée (statistiques de répartition) pour un coût énergétique dérisoire.

En revanche, pour l'étape de **Sentiment** (via Camembert), le coût sera 100x supérieur. Nous recommandons de ne l'activer que sur les demandes "Priorité Haute" ou via un échantillonnage statistique si les ressources serveurs sont contraintes.
