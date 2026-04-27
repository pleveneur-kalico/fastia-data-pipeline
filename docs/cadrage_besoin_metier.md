# Cadrage du besoin métier — Enrichissement Intelligent (Module 3 Brief 3)

## 1. Reformulation opérationnelle du besoin
Automatiser la détection de la langue d'origine et l'analyse du sentiment des demandes entrantes afin de router prioritairement les flux non-francophones vers les équipes expertes et d'identifier immédiatement les réclamations critiques (clients mécontents).

## 2. Personas concernés
*   **Clients (Émetteurs)** : Produisent la donnée brute via Email, Chat ou Formulaire Web.
*   **Équipes de support spécialisées (Consommateurs)** : Opérateurs bilingues (EN/ES) et gestionnaires de crise qui reçoivent les flux qualifiés et priorisés.
*   **Directeur Métier / Product Manager (Décideurs)** : Utilisent les statistiques de répartition (langues, sentiments) pour ajuster les ressources humaines et la stratégie client.

## 3. Critères de succès
*   **Détection de langue** : Atteindre une précision (Accuracy) ≥ 95% sur un échantillon de validation de 200 lignes (mélange FR, EN, ES).
*   **Analyse de sentiment** : Corrélation de ≥ 80% avec une annotation humaine sur les cas de "Mésentente sévère".
*   **Performance** : Temps d'enrichissement < 100ms par message en moyenne pour ne pas ralentir l'ingestion.

## 4. Hypothèses à vérifier
*   **Volume** : Est-ce qu'effectivement 1/3 des demandes sont non-françaises ?
*   **Canaux** : La part de non-français est-elle plus élevée sur le canal Email (B2B) que sur les autres ?
*   **Saisonnalité** : La répartition des langues est-elle stable ou liée à des campagnes spécifiques ?

## 5. Non-objectifs
*   **Pas de traduction automatique** : Le contenu original reste la référence pour l'opérateur.
*   **Pas de modification de l'API publique** : L'enrichissement est interne à la pipeline et transparent pour l'utilisateur final.
*   **Pas de suppression automatisée** : Aucune demande n'est supprimée sur la base du sentiment ou de la langue.

## 6. Risques éthiques préliminaires
*   **AI Act & Biais** : La détection de langue peut être corrélée à l'origine nationale ou géographique. Une erreur de routage pourrait entraîner une discrimination de traitement (délais plus longs pour certaines langues).
*   **Sentiment & Décision Automatisée** : Un client "calme" mais ayant un problème technique majeur pourrait être dé-priorisé par erreur si le score de sentiment est le seul critère.
*   **Confidentialité** : L'utilisation de modèles externes (Cloud) pour l'enrichissement pourrait exposer des données sensibles (besoin de privilégier des solutions locales/Open Source).
