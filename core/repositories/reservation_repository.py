from ..extensions import db
from ..models import Match, Reservation, ZonePlace


def get_match_by_id(match_id):
    return db.session.get(Match, match_id)


def get_match_and_zone(match_id, zone_id):
    match = db.session.get(Match, match_id)
    zone = db.session.get(ZonePlace, zone_id)
    return match, zone


def reservation_code_exists(code):
    return Reservation.query.filter_by(code_reservation=code).first() is not None


def create_reservation_and_decrement_zone(
    match,
    zone,
    code,
    nom,
    email,
    siege,
    reservation_date,
):
    db.session.add(Reservation(
        match_id=match.id,
        zone_id=zone.id,
        code_reservation=code,
        nom_client=nom,
        email_client=email,
        numero_siege=siege,
        date_reservation=reservation_date,
    ))
    zone.places_restantes -= 1
    db.session.commit()
