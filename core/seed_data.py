import random

from .extensions import db
from .models import Equipe, Stade, Match, ZonePlace


def seed_db():
    equipes_data = [
        dict(nom="PSG", pays="France", victoires=22, nuls=5, defaites=3, buts_pour=68, buts_contre=28, forme_recente="WWWDW"),
        dict(nom="Olympique de Marseille", pays="France", victoires=16, nuls=7, defaites=7, buts_pour=52, buts_contre=38, forme_recente="WDWLW"),
        dict(nom="Olympique Lyonnais", pays="France", victoires=14, nuls=8, defaites=8, buts_pour=47, buts_contre=41, forme_recente="DLWWL"),
        dict(nom="AS Monaco", pays="France", victoires=18, nuls=4, defaites=8, buts_pour=58, buts_contre=35, forme_recente="WWLWW"),
        dict(nom="LOSC Lille", pays="France", victoires=15, nuls=6, defaites=9, buts_pour=44, buts_contre=33, forme_recente="WLDWW"),
        dict(nom="Real Madrid", pays="Espagne", victoires=25, nuls=3, defaites=2, buts_pour=78, buts_contre=22, forme_recente="WWWWW"),
        dict(nom="FC Barcelone", pays="Espagne", victoires=21, nuls=6, defaites=3, buts_pour=72, buts_contre=30, forme_recente="LWDWW"),
        dict(nom="Bayern Munich", pays="Allemagne", victoires=23, nuls=4, defaites=3, buts_pour=80, buts_contre=25, forme_recente="WWWLW"),
        dict(nom="Manchester City", pays="Angleterre", victoires=20, nuls=6, defaites=4, buts_pour=65, buts_contre=28, forme_recente="DWWWW"),
        dict(nom="Liverpool FC", pays="Angleterre", victoires=19, nuls=5, defaites=6, buts_pour=62, buts_contre=32, forme_recente="WLWWW"),
        dict(nom="Juventus FC", pays="Italie", victoires=16, nuls=7, defaites=7, buts_pour=48, buts_contre=36, forme_recente="WLLWW"),
        dict(nom="Atletico Madrid", pays="Espagne", victoires=17, nuls=9, defaites=4, buts_pour=50, buts_contre=27, forme_recente="DDWWW"),
    ]
    equipes = []
    for data in equipes_data:
        item = Equipe(**data)
        db.session.add(item)
        equipes.append(item)
    db.session.flush()
    eq = {e.nom: e for e in equipes}

    stades_data = [
        dict(nom="Parc des Princes", ville="Paris", capacite=47929),
        dict(nom="Orange Velodrome", ville="Marseille", capacite=67394),
        dict(nom="Stade de France", ville="Saint-Denis", capacite=81338),
        dict(nom="Groupama Stadium", ville="Lyon", capacite=59186),
        dict(nom="Stade Louis II", ville="Monaco", capacite=18523),
        dict(nom="Allianz Riviera", ville="Nice", capacite=35624),
    ]
    stades = []
    for data in stades_data:
        item = Stade(**data)
        db.session.add(item)
        stades.append(item)
    db.session.flush()
    st = {s.nom: s for s in stades}

    matchs_passes = [
        ("PSG", "Olympique de Marseille", "Parc des Princes", "2025-06-08", "20:45", "Ligue 1", 3, 1),
        ("AS Monaco", "Olympique Lyonnais", "Stade Louis II", "2025-06-15", "17:00", "Ligue 1", 2, 2),
        ("Olympique de Marseille", "LOSC Lille", "Orange Velodrome", "2025-06-22", "20:45", "Ligue 1", 1, 0),
        ("Juventus FC", "Atletico Madrid", "Stade de France", "2025-06-29", "20:45", "International Champions Cup", 2, 1),
        ("Bayern Munich", "Real Madrid", "Stade de France", "2025-07-06", "21:00", "Champions League", 1, 2),
        ("PSG", "FC Barcelone", "Parc des Princes", "2025-07-13", "21:00", "Champions League", 0, 1),
        ("Olympique Lyonnais", "PSG", "Groupama Stadium", "2025-07-20", "20:45", "Ligue 1", 1, 3),
        ("Liverpool FC", "Manchester City", "Stade de France", "2025-07-27", "17:30", "Premier League", 2, 2),
    ]
    for dom, ext, stade, date, heure, comp, score_dom, score_ext in matchs_passes:
        db.session.add(Match(
            domicile_id=eq[dom].id,
            exterieur_id=eq[ext].id,
            stade_id=st[stade].id,
            date_match=date,
            heure_match=heure,
            competition=comp,
            score_dom=score_dom,
            score_ext=score_ext,
            statut='passe',
        ))

    matchs_futurs = [
        ("PSG", "AS Monaco", "Parc des Princes", "2025-08-03", "20:45", "Ligue 1"),
        ("Olympique de Marseille", "Olympique Lyonnais", "Orange Velodrome", "2025-08-10", "17:00", "Ligue 1"),
        ("Juventus FC", "Bayern Munich", "Stade de France", "2025-08-14", "20:45", "Amical Club"),
        ("Real Madrid", "PSG", "Stade de France", "2025-08-17", "21:00", "Champions League"),
        ("FC Barcelone", "Manchester City", "Stade de France", "2025-08-20", "21:00", "Champions League"),
        ("LOSC Lille", "AS Monaco", "Groupama Stadium", "2025-08-24", "15:00", "Ligue 1"),
        ("PSG", "Liverpool FC", "Parc des Princes", "2025-08-28", "21:00", "Champions League"),
        ("Atletico Madrid", "FC Barcelone", "Stade de France", "2025-08-31", "20:45", "LaLiga Summer Series"),
    ]

    zones_template = [
        ("VIP Tribune Presidentielle", 350.0, 200, 45),
        ("Tribune Basse Nord", 120.0, 2000, 1350),
        ("Tribune Basse Sud", 120.0, 2000, 980),
        ("Tribune Haute Est", 75.0, 3000, 2100),
        ("Tribune Haute Ouest", 75.0, 3000, 1800),
        ("Virage Nord (Ultras)", 45.0, 5000, 3200),
        ("Virage Sud", 45.0, 5000, 2600),
    ]

    for dom, ext, stade, date, heure, comp in matchs_futurs:
        match = Match(
            domicile_id=eq[dom].id,
            exterieur_id=eq[ext].id,
            stade_id=st[stade].id,
            date_match=date,
            heure_match=heure,
            competition=comp,
            statut='futur',
        )
        db.session.add(match)
        db.session.flush()

        for categorie, prix, places_totales, base_restantes in zones_template:
            variation = random.randint(-8, 8)
            restantes = max(0, base_restantes + variation * (base_restantes // 100))
            db.session.add(ZonePlace(
                match_id=match.id,
                categorie=categorie,
                prix=prix,
                places_totales=places_totales,
                places_restantes=restantes,
            ))

    db.session.commit()


def init_db_with_seed():
    db.create_all()
    if not Equipe.query.first():
        seed_db()
