from ..models import Match


def get_future_matches(limit=None):
    query = Match.query.filter_by(statut='futur').order_by(Match.date_match)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_past_matches(limit=None):
    query = Match.query.filter_by(statut='passe').order_by(Match.date_match.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_match_by_id(match_id):
    return Match.query.get(match_id)


def get_available_zones(match):
    return [zone for zone in match.zones if zone.places_restantes > 0]
