from flask import Blueprint, jsonify, render_template, request

from .services.chatbot_service import process_message
from .models import Match

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/get_response', methods=['POST'])
def chat():
    data = request.get_json(silent=True)
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    user_msg = data['message'].strip()[:300]
    if not user_msg:
        return jsonify({'response': 'Veuillez entrer un message.'})

    return jsonify({'response': process_message(user_msg)})


@main_bp.route('/api/matchs_futurs')
def api_matchs_futurs():
    matchs = Match.query.filter_by(statut='futur').order_by(Match.date_match).limit(6).all()
    return jsonify([
        {
            'id': m.id,
            'domicile': m.domicile.nom,
            'exterieur': m.exterieur.nom,
            'date': m.date_match,
            'heure': m.heure_match,
            'competition': m.competition,
            'stade': m.stade.nom,
            'ville': m.stade.ville,
            'places_restantes': m.places_restantes_total,
        }
        for m in matchs
    ])


@main_bp.route('/api/scores_recents')
def api_scores_recents():
    matchs = Match.query.filter_by(statut='passe').order_by(Match.date_match.desc()).limit(6).all()
    return jsonify([
        {
            'domicile': m.domicile.nom,
            'exterieur': m.exterieur.nom,
            'score': m.score_str,
            'date': m.date_match,
            'competition': m.competition,
        }
        for m in matchs
    ])
