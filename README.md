# FootBot - Chatbot de reservation de matchs de football

FootBot permet de :
- consulter les scores recents,
- voir les matchs a venir,
- reserver des places selon les zones disponibles,
- obtenir des predictions sur les matchs a venir,
- comprendre des fautes de frappe simples grace a une detection fuzzy.

## Apercu des fonctionnalites

### 1) Chatbot conversationnel
- Intents : aide, scores, matchs futurs, reservation, prediction, annulation.
- Flux de reservation guide : choix du match, choix de zone, nom, email, confirmation.

### 2) Gestion des donnees avec SQLite
- Equipes
- Stades
- Matchs
- Zones de places
- Reservations

### 3) Predictions de vainqueur
Prediction heuristique basee sur :
- performances historiques (victoires, nuls, defaites),
- buts pour / buts contre,
- forme recente,
- avantage domicile.

### 4) Tolerance aux fautes de frappe
Le bot utilise :
- normalisation du texte,
- tokenisation,
- comparaison de similarite fuzzy,
- lexique d'intentions.

Exemples reconnus :
- bonjor -> bonjour
- resrever -> reserver
- scoer -> score
- predicton -> prediction

## Structure du projet

- app.py : point d'entree Flask (app factory)
- core/ : coeur de l'application
- core/config.py : configuration
- core/extensions.py : extensions Flask (SQLAlchemy)
- core/models.py : modeles de base de donnees
- core/routes.py : routes web et API
- core/seed_data.py : donnees de seed
- core/services/chatbot_service.py : logique metier du chatbot
- core/repositories/ : acces aux donnees
- static/ : CSS et JavaScript
- templates/ : page HTML

## Lancement

python app.py

Puis ouvrir dans le navigateur :
- http://127.0.0.1:5000

## Base de donnees

La base SQLite est creee automatiquement au premier lancement.
Le seed est injecte si la base est vide.


## API disponibles

- GET /api/matchs_futurs
- GET /api/scores_recents
- POST /get_response