# Fiche Source : Formulaires Web

## 1. Origine de la donnée
Les données proviennent du formulaire de contact du site web FastIA. Les clients remplissent un formulaire structuré avec leur email, un sujet optionnel et leur message.

## 2. Volumétrie
- **Format** : JSONL (1 ligne par soumission).
- **Estimation** : ~10-20 soumissions par jour via le site web.

## 3. Format et Champs Exploités
- `submission_id` -> `external_id` (Identifiant unique).
- `submitted_at` -> `received_at` (Date de soumission).
- `form.message` -> `body` (Contenu de la demande).
- `form.subject` -> `subject` (Sujet, avec fallback sur le début du message).
- `ip_country`, `user_agent` -> `canal_metadata`.

## 4. Données Personnelles et RGPD
- **Identifiants** : Email de l'expéditeur.
- **RGPD** : Le champ `consent_marketing` est présent mais ignoré par la pipeline. L'anonymisation standard (M2) est appliquée sur le corps du message.

## 5. Biais Potentiels
- Demandes généralement plus courtes et directes que par email.
- Utilisation majoritaire par de nouveaux clients ou des prospects (demandes commerciales, bugs d'interface).
