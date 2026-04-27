# Fiche Source : Emails Clients

## 1. Origine de la donnée
Les données sont produites directement par les clients de FastIA lorsqu'ils contactent le support via l'adresse `support@fastia.io`. Contrairement aux formulaires web qui sont structurés, l'email est une source non structurée où l'utilisateur est libre de la forme et du contenu.

## 2. Volumétrie
D'après l'échantillon fourni (`emails_fastia.mbox`) :
- **Échantillon** : 8 emails sur une période de 5 jours (du 6 au 10 avril 2026).
- **Moyenne journalière** : ~1,6 emails / jour.
- **Extrapolation mensuelle** : ~48 emails / mois.
- **Extrapolation annuelle** : ~580 emails / an.

*Note : Cette volumétrie est relativement faible, ce qui suggère que l'email est utilisé pour des demandes plus complexes ou par une base client spécifique.*

## 3. Format et Champs Exploités
Le format brut est le **MBOX** (standard RFC 4155).
Les champs porteurs d'informations exploitables sont :
- `Message-ID` : Identifiant unique du message (clé d'idempotence).
- `From` : Identité de l'expéditeur (nom et email).
- `Date` : Date et heure d'envoi (pour la saisonnalité).
- `Subject` : Objet du mail (contexte court).
- `Body` : Contenu textuel (corps du message).
- `In-Reply-To` / `References` : Pour la reconstruction des fils de discussion (threads).

## 4. Données Personnelles et RGPD
La source email est riche en données à caractère personnel (DCP) :
- **Identifiants directs** : Adresse email, nom/prénom dans le champ `From` ou dans la signature.
- **Coordonnées** : Numéros de téléphone souvent présents dans les signatures.
- **Identifiants métier** : Références clients (ex: `PRO-44219`), numéros de factures (ex: `FA-2026-0312`).

**Rappel des règles d'anonymisation (M2)** : 
Toute donnée permettant d'identifier un individu doit être masquée (ex: `[EMAIL]`, `[PHONE]`, `[CLIENT_REF]`) avant stockage définitif ou utilisation pour le fine-tuning.

## 5. Biais Potentiels
Le canal email introduit des biais spécifiques par rapport au Chat ou au Web :
- **Démographie** : On peut faire l'hypothèse d'une clientèle plus âgée ou plus "corporate" privilégiant l'email.
- **Forme** : Demandes plus longues, plus formelles, avec des formules de politesse qui peuvent "noyer" l'intention réelle.
- **Complexité** : L'email est souvent utilisé pour des problèmes profonds ou des réclamations, là où le chat est utilisé pour des questions rapides.
- **Bruit** : Présence de signatures, de mentions légales et de citations (historique des échanges) qui doivent être nettoyées.
