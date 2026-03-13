import difflib
import random
import re
import string
import unicodedata
from datetime import datetime

from flask import session

from ..repositories.match_repository import (
    get_available_zones,
    get_future_matches,
    get_past_matches,
)
from ..repositories.reservation_repository import (
    create_reservation_and_decrement_zone,
    get_match_by_id,
    get_match_and_zone,
    reservation_code_exists,
)


INTENT_LEXICON = {
    'bonjour': [
        'bonjour', 'bonjor', 'bonjou', 'salut', 'salu', 'hello', 'bonsoir', 'hey', 'coucou', 'hi', 'yo'
    ],
    'aide': [
        'aide', 'aid', 'help', 'menu', 'quoi faire', 'comment', 'commande', 'options'
    ],
    'scores': [
        'score', 'scoer', 'resultat', 'resultats', 'dernier score', 'scores recents', 'recent', 'passe'
    ],
    'matchs_futurs': [
        'prochain', 'prochian', 'programme', 'calendrier', 'agenda', 'a venir', 'futur', 'match a venir'
    ],
    'reserver': [
        'reserver', 'reservere', 'reservation', 'reserv', 'billet', 'ticket', 'acheter', 'achat', 'place'
    ],
    'prediction': [
        'prediction', 'predire', 'pronostic', 'pronostique', 'prevoir', 'gagnant',
        'vainqueur', 'probabilite', 'qui va gagner'
    ],
    'annuler': [
        'annuler', 'annule', 'retour', 'quitter', 'stop', 'recommencer'
    ],
}

AFFIRMATIVE_WORDS = ['oui', 'ouii', 'ok', 'okay', 'yes', 'confirme', 'valide', 'go']
NEGATIVE_WORDS = ['non', 'no', 'annule', 'annuler', 'stop', 'pas']
TEAM_STOPWORDS = {'de', 'du', 'des', 'fc', 'as', 'olympique', 'equipe'}


def _norm(text):
    nfkd = unicodedata.normalize('NFKD', text or '')
    return ''.join(char for char in nfkd if not unicodedata.combining(char)).lower()


def _tokens(text):
    return re.findall(r"[a-z0-9']+", _norm(text))


def _fuzzy_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def _token_in_tokens_fuzzy(token, message_tokens, threshold=0.82):
    if token in message_tokens:
        return True
    for candidate in message_tokens:
        if _fuzzy_ratio(token, candidate) >= threshold:
            return True
    return False


def _phrase_match_score(phrase, message_tokens):
    phrase_tokens = _tokens(phrase)
    if not phrase_tokens:
        return 0.0

    hits = 0
    for token in phrase_tokens:
        if _token_in_tokens_fuzzy(token, message_tokens):
            hits += 1
    return hits / len(phrase_tokens)


def message_mentions_team(message, team_name):
    normalized_message = _norm(message)
    normalized_team = _norm(team_name)

    if normalized_team in normalized_message:
        return True

    message_tokens = _tokens(normalized_message)
    team_tokens = [
        token for token in _tokens(normalized_team)
        if token not in TEAM_STOPWORDS and len(token) >= 3
    ]
    if not team_tokens:
        return False

    hits = 0
    for token in team_tokens:
        if _token_in_tokens_fuzzy(token, message_tokens, threshold=0.8):
            hits += 1

    needed = 1 if len(team_tokens) == 1 else max(1, len(team_tokens) - 1)
    return hits >= needed


def _contains_fuzzy_word(message, words, threshold=0.83):
    message_tokens = _tokens(message)
    if not message_tokens:
        return False

    for token in message_tokens:
        for candidate in words:
            candidate_norm = _norm(candidate)
            if token == candidate_norm or _fuzzy_ratio(token, candidate_norm) >= threshold:
                return True
    return False


def detect_intent(text):
    normalized = _norm(text)
    message_tokens = _tokens(normalized)

    # Cancellation should win over booking when both words appear.
    if _contains_fuzzy_word(normalized, INTENT_LEXICON['annuler'], threshold=0.8):
        return 'annuler'

    best_intent = None
    best_score = 0.0

    for intent, keywords in INTENT_LEXICON.items():
        for keyword in keywords:
            if _norm(keyword) in normalized:
                return intent

            score = _phrase_match_score(keyword, message_tokens)
            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score >= 0.75:
        return best_intent
    return None


def predire_vainqueur(match):
    dom = match.domicile
    ext = match.exterieur
    force_dom = dom.force_globale + 5
    force_ext = ext.force_globale
    total = force_dom + force_ext or 1

    raw_dom = force_dom / total
    raw_ext = force_ext / total

    prob_nul = round(min(15 + (1 - abs(raw_dom - raw_ext)) * 10, 30), 1)
    remaining = 100 - prob_nul
    prob_dom = round(raw_dom * remaining, 1)
    prob_ext = round(remaining - prob_dom, 1)

    diff = abs(force_dom - force_ext)
    confiance = 'elevee' if diff > 20 else ('moderee' if diff > 10 else 'faible')

    if prob_dom > prob_ext + 5:
        vainqueur = dom.nom
    elif prob_ext > prob_dom + 5:
        vainqueur = ext.nom
    else:
        vainqueur = 'Match equilibre'

    return {
        'vainqueur': vainqueur,
        'prob_dom': prob_dom,
        'prob_nul': prob_nul,
        'prob_ext': prob_ext,
        'confiance': confiance,
        'force_dom': dom.force_globale,
        'force_ext': force_ext,
    }


def _welcome():
    return (
        "Bonjour&nbsp;! 👋 Bienvenue sur <b>FootBot</b>, votre assistant de réservation de billets de football&nbsp;!<br><br>"
        "Je peux vous aider à&nbsp;:<br>"
        "⚽ Voir les <b>scores récents</b><br>"
        "📅 Consulter les <b>prochains matchs</b><br>"
        "🎫 <b>Réserver une place</b><br>"
        "🔮 Obtenir une <b>prédiction de match</b><br><br>"
        "Que puis-je faire pour vous&nbsp;?"
    )


def _help():
    return (
        "Voici ce que je peux faire&nbsp;:<br><br>"
        "⚽ <b>Scores récents</b> — <i>\"Derniers résultats\"</i><br>"
        "📅 <b>Prochains matchs</b> — <i>\"Programme des matchs\"</i><br>"
        "🎫 <b>Réserver</b> — <i>\"Je veux réserver une place\"</i><br>"
        "🔮 <b>Prédiction</b> — <i>\"Pronostic des matchs\"</i><br>"
        "❌ <b>Annuler</b> — <i>\"Annuler\"</i>"
    )


def _scores_recents():
    matchs = get_past_matches(limit=8)
    if not matchs:
        return "Aucun résultat disponible pour l'instant."

    result = "<b>📊 Derniers résultats :</b><br><br>"
    for match in matchs:
        if match.score_dom > match.score_ext:
            winner = f"<b>{match.domicile.nom}</b>"
            loser = match.exterieur.nom
            score = f"<b>{match.score_dom}</b> - {match.score_ext}"
        elif match.score_ext > match.score_dom:
            winner = match.domicile.nom
            loser = f"<b>{match.exterieur.nom}</b>"
            score = f"{match.score_dom} - <b>{match.score_ext}</b>"
        else:
            winner = match.domicile.nom
            loser = match.exterieur.nom
            score = f"{match.score_dom} - {match.score_ext}"

        result += (
            f"🏆 <i>{match.competition}</i> · {match.date_match}<br>"
            f"&nbsp;&nbsp;{winner} {score} {loser}<br><br>"
        )
    return result


def _matchs_futurs():
    matchs = get_future_matches()
    if not matchs:
        return "Aucun match à venir pour l'instant."

    result = "<b>📅 Prochains matchs :</b><br><br>"
    for index, match in enumerate(matchs, 1):
        total = match.places_restantes_total
        dispo = f"✅ {total} places" if total > 0 else "❌ Complet"
        result += (
            f"<b>{index}.</b> {match.domicile.nom} vs {match.exterieur.nom}<br>"
            f"&nbsp;&nbsp;📅 {match.date_match} à {match.heure_match} · 🏟️ {match.stade.nom}<br>"
            f"&nbsp;&nbsp;🏆 {match.competition} · {dispo}<br><br>"
        )
    result += "Voulez-vous <b>réserver</b> ou voir les <b>prédictions</b>&nbsp;?"
    return result


def _show_zones(match):
    zones = get_available_zones(match)
    if not zones:
        return "Désolé, il n'y a plus de places disponibles pour ce match."

    result = (
        f"<b>🏟️ {match.affichage}</b><br>"
        f"📅 {match.date_match} à {match.heure_match} · {match.stade.nom}, {match.stade.ville}<br><br>"
        "<b>Zones disponibles :</b><br><br>"
    )
    for index, zone in enumerate(zones, 1):
        result += (
            f"<b>{index}.</b> {zone.categorie}<br>"
            f"&nbsp;&nbsp;💶 <b>{zone.prix:.0f}€</b> · 🎫 {zone.places_restantes} places restantes<br><br>"
        )
    result += "Entrez le <b>numéro</b> de la zone souhaitée :"
    return result


def _start_reservation(conv, user_msg):
    matchs = get_future_matches()
    available = [match for match in matchs if match.places_restantes_total > 0]
    if not available:
        return "Désolé, tous les matchs sont complets pour le moment. 😔"

    for match in available:
        if message_mentions_team(user_msg, match.domicile.nom) or message_mentions_team(user_msg, match.exterieur.nom):
            conv['match_id'] = match.id
            conv['state'] = 'liste_zones'
            session.modified = True
            return _show_zones(match)

    conv['state'] = 'liste_matchs'
    session.modified = True
    result = "<b>🎫 Réservation de billets</b><br><br>Voici les matchs disponibles :<br><br>"
    for index, match in enumerate(matchs, 1):
        total = match.places_restantes_total
        dispo = f"✅ {total} places" if total > 0 else "❌ Complet"
        prix_min = min((zone.prix for zone in match.zones if zone.places_restantes > 0), default=0)
        result += (
            f"<b>{index}.</b> {match.domicile.nom} vs {match.exterieur.nom}<br>"
            f"&nbsp;&nbsp;📅 {match.date_match} à {match.heure_match} · 🏟️ {match.stade.nom}<br>"
            f"&nbsp;&nbsp;🏆 {match.competition} · {dispo} · à partir de <b>{prix_min:.0f}€</b><br><br>"
        )
    result += "Entrez le <b>numéro</b> du match qui vous intéresse :"
    return result


def _predictions(user_msg=None):
    matchs = get_future_matches()
    if not matchs:
        return "Aucun match à venir pour les prédictions."

    if user_msg:
        subset = [
            match
            for match in matchs
            if message_mentions_team(user_msg, match.domicile.nom) or message_mentions_team(user_msg, match.exterieur.nom)
        ]
        if subset:
            matchs = subset

    result = "<b>🔮 Prédictions des matchs à venir :</b><br><br>"
    for match in matchs:
        prediction = predire_vainqueur(match)
        result += (
            f"<b>{match.domicile.nom} vs {match.exterieur.nom}</b><br>"
            f"&nbsp;&nbsp;📅 {match.date_match} · {match.competition}<br>"
            f"&nbsp;&nbsp;🔮 Favori : <b>{prediction['vainqueur']}</b> (confiance : {prediction['confiance']})<br>"
            f"&nbsp;&nbsp;📊 {match.domicile.nom} <b>{prediction['prob_dom']}%</b> | "
            f"Nul <b>{prediction['prob_nul']}%</b> | {match.exterieur.nom} <b>{prediction['prob_ext']}%</b><br>"
            f"&nbsp;&nbsp;💪 Force : {match.domicile.nom} {prediction['force_dom']}/100 · "
            f"{match.exterieur.nom} {prediction['force_ext']}/100<br><br>"
        )
    result += (
        "<i>⚠️ Les prédictions sont basées sur les statistiques des équipes "
        "et ne constituent pas des garanties de résultat.</i>"
    )
    return result


def _finalize_reservation(conv):
    match, zone = get_match_and_zone(conv['match_id'], conv['zone_id'])
    nom = conv['nom']
    email = conv['email']

    if match is None or zone is None:
        conv.update({'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None})
        session.modified = True
        return "Réservation invalide. Merci de recommencer en tapant <b>réserver</b>."

    if zone.places_restantes <= 0:
        conv.update({'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None})
        session.modified = True
        return "Désolé, cette zone est désormais complète. 😔<br>Tapez <b>réserver</b> pour choisir une autre zone."

    code = None
    for _ in range(20):
        candidate = 'FT' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not reservation_code_exists(candidate):
            code = candidate
            break

    if code is None:
        code = 'FT' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    row = random.choice('ABCDEFGHIJKLMNOP')
    siege = f"{row}{random.randint(1, 50):02d}"

    create_reservation_and_decrement_zone(
        match=match,
        zone=zone,
        code=code,
        nom=nom,
        email=email,
        siege=siege,
        reservation_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
    )

    conv.update({'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None})
    session.modified = True

    return (
        f"✅ <b>Réservation confirmée !</b><br><br>"
        f"🎫 <b>Code :</b> <code>{code}</code><br>"
        f"🪑 <b>Siège :</b> {siege}<br>"
        f"🏟️ <b>Match :</b> {match.affichage}<br>"
        f"📅 <b>Date :</b> {match.date_match} à {match.heure_match}<br>"
        f"📍 <b>Stade :</b> {match.stade.nom}, {match.stade.ville}<br>"
        f"🎫 <b>Zone :</b> {zone.categorie}<br>"
        f"💶 <b>Prix :</b> {zone.prix:.0f}€<br>"
        f"👤 <b>Nom :</b> {nom}<br>"
        f"📧 <b>Email :</b> {email}<br><br>"
        f"Présentez le code <b>{code}</b> à l'entrée du stade. Bonne chance à votre équipe ! ⚽"
    )


def process_message(user_msg):
    if 'conv' not in session:
        session['conv'] = {'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None}

    conv = session['conv']
    state = conv.get('state', 'idle')
    intent = detect_intent(user_msg)
    normalized_msg = _norm(user_msg)

    if intent == 'annuler' and state != 'idle':
        conv.update({'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None})
        session.modified = True
        return "Réservation annulée. Comment puis-je vous aider ? Tapez <b>aide</b>."

    if state == 'idle':
        if intent == 'bonjour':
            return _welcome()
        if intent == 'aide':
            return _help()
        if intent == 'scores':
            return _scores_recents()
        if intent == 'matchs_futurs':
            return _matchs_futurs()
        if intent == 'reserver':
            return _start_reservation(conv, user_msg)
        if intent == 'prediction':
            return _predictions(user_msg)
        return "Je n'ai pas compris. 🤔<br><br>" + _help()

    if state == 'liste_matchs':
        matchs = get_future_matches()

        if intent == 'prediction':
            return _predictions(user_msg)
        if intent == 'scores':
            return _scores_recents()
        if intent == 'annuler':
            conv.update({'state': 'idle'})
            session.modified = True
            return "Réservation annulée."

        if user_msg.strip().isdigit():
            index = int(user_msg.strip())
            if 1 <= index <= len(matchs):
                match = matchs[index - 1]
                if match.places_restantes_total == 0:
                    return f"Le match <b>{match.affichage}</b> est complet. Choisissez un autre numéro."
                conv['match_id'] = match.id
                conv['state'] = 'liste_zones'
                session.modified = True
                return _show_zones(match)
            return f"Numéro invalide. Entrez un numéro entre 1 et {len(matchs)}."

        for match in matchs:
            if message_mentions_team(user_msg, match.domicile.nom) or message_mentions_team(user_msg, match.exterieur.nom):
                conv['match_id'] = match.id
                conv['state'] = 'liste_zones'
                session.modified = True
                return _show_zones(match)

        return "Veuillez entrer le <b>numéro</b> du match (ex&nbsp;: 1, 2, 3...) ou le nom d'une équipe."

    if state == 'liste_zones':
        match = get_match_by_id(conv['match_id'])
        if match is None:
            conv.update({'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None})
            session.modified = True
            return "Le match sélectionné n'est plus disponible. Tapez <b>réserver</b> pour recommencer."
        zones = get_available_zones(match)

        if user_msg.strip().isdigit():
            index = int(user_msg.strip())
            if 1 <= index <= len(zones):
                zone = zones[index - 1]
                conv['zone_id'] = zone.id
                conv['state'] = 'saisir_nom'
                session.modified = True
                return f"<b>{zone.categorie}</b> — <b>{zone.prix:.0f}€</b> la place.<br><br>Pour finaliser, entrez votre <b>nom complet</b>&nbsp;:"
            return f"Numéro invalide. Choisissez entre 1 et {len(zones)}."
        return "Entrez le <b>numéro</b> de la zone souhaitée."

    if state == 'saisir_nom':
        nom = user_msg.strip()
        if len(nom) < 2:
            return "Nom trop court. Veuillez entrer votre <b>nom complet</b>."
        conv['nom'] = nom
        conv['state'] = 'saisir_email'
        session.modified = True
        return f"Merci <b>{nom}</b>&nbsp;! Entrez maintenant votre <b>adresse e-mail</b>&nbsp;:"

    if state == 'saisir_email':
        email = user_msg.strip()
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return "Adresse e-mail invalide. Exemple&nbsp;: <i>jean@gmail.com</i>"
        conv['email'] = email
        conv['state'] = 'confirmer'
        session.modified = True
        match, zone = get_match_and_zone(conv['match_id'], conv['zone_id'])
        return (
            f"<b>📋 Récapitulatif&nbsp;:</b><br><br>"
            f"🏟️ <b>Match :</b> {match.affichage}<br>"
            f"📅 <b>Date :</b> {match.date_match} à {match.heure_match}<br>"
            f"📍 <b>Stade :</b> {match.stade.nom}, {match.stade.ville}<br>"
            f"🎫 <b>Zone :</b> {zone.categorie}<br>"
            f"💶 <b>Prix :</b> {zone.prix:.0f}€<br>"
            f"👤 <b>Nom :</b> {conv['nom']}<br>"
            f"📧 <b>Email :</b> {email}<br><br>"
            "Confirmez-vous cette réservation ? (<b>oui</b> / <b>non</b>)"
        )

    if state == 'confirmer':
        if _contains_fuzzy_word(normalized_msg, AFFIRMATIVE_WORDS):
            return _finalize_reservation(conv)
        if _contains_fuzzy_word(normalized_msg, NEGATIVE_WORDS):
            conv.update({'state': 'idle', 'match_id': None, 'zone_id': None, 'nom': None, 'email': None})
            session.modified = True
            return "Réservation annulée. Comment puis-je vous aider ?"
        return "Répondez <b>oui</b> pour confirmer ou <b>non</b> pour annuler."

    return _help()
