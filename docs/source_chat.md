# Fiche Source : Chat en Direct

## 1. Origine de la donnée
Les données proviennent de l'outil de chat en direct (LiveChat) intégré à la plateforme FastIA. Les conversations sont capturées sous forme de logs de messages.

## 2. Volumétrie
- **Format** : CSV (historique des messages).
- **Transformation** : Aggrégation par `session_id` pour reconstruire la demande complète du visiteur.
- **Estimation** : ~50 sessions par jour.

## 3. Format et Champs Exploités
- `session_id` -> `external_id`.
- `timestamp` du premier message -> `received_at`.
- Messages `visitor` -> `body` (concaténés).
- Transcript complet (agent + visiteur) -> `canal_metadata.transcript_complet`.

## 4. Données Personnelles et RGPD
- Le chat est souvent plus informel. L'anonymisation doit être particulièrement vigilante sur les noms propres et les références partagées rapidement dans la discussion.

## 5. Biais Potentiels
- **Style** : Langage très informel, abréviations, fautes d'orthographe.
- **Urgence** : Les demandes par chat concernent souvent des blocages immédiats ou des questions simples de navigation.
- **Bruit** : Présence de messages de politesse ("bonjour", "merci") et de réponses automatiques de l'agent.
