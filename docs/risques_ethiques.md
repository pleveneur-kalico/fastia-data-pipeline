# Note Réglementaire et Éthique - FastIA

## 1. Conformité RGPD
Le pipeline de traitement des données FastIA intègre une étape systématique d'anonymisation des données à caractère personnel (PII).
- **Emails, Téléphones, URLs** : Masquage par Regex.
- **Noms propres** : Masquage via le modèle de reconnaissance d'entités nommées (NER) de SpaCy (`fr_core_news_sm`).

## 2. Biais Identifiés
Suite à l'audit du dataset (`audit_synthese.json`), les biais suivants ont été identifiés :
- **Biais de longueur** : Les catégories comme "Réclamation" ont tendance à être plus longues que les "Informations générales". Le modèle pourrait apprendre à classer par longueur plutôt que par contenu sémantique.
- **Déséquilibre des classes** : Certaines combinaisons (ex: Information générale + Priorité Haute) sont absentes.
- **Risques de Faux Positifs** : Le modèle NER peut parfois masquer des mots qui ne sont pas des noms (ex: début de phrase).

## 3. Stratégies d'Atténuation
- **Normalisation** : Nettoyage des espaces et caractères spéciaux pour réduire le bruit.
- **Validation** : Vérification stricte des catégories et priorités pour assurer la cohérence.
- **Augmentation (Futur)** : Il est recommandé de générer des données synthétiques pour équilibrer les classes sous-représentées.

## 4. Recommandations
- Ne jamais désactiver l'étape d'anonymisation avant l'exportation vers un environnement tiers.
- Effectuer des tests de robustesse sur le modèle final pour vérifier qu'il ne discrimine pas selon la longueur ou le ton des messages.
