from .extensions import db


class Equipe(db.Model):
    __tablename__ = 'equipes'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    pays = db.Column(db.String(50), default='')
    victoires = db.Column(db.Integer, default=0)
    nuls = db.Column(db.Integer, default=0)
    defaites = db.Column(db.Integer, default=0)
    buts_pour = db.Column(db.Integer, default=0)
    buts_contre = db.Column(db.Integer, default=0)
    forme_recente = db.Column(db.String(10), default='')

    @property
    def force_globale(self):
        total = self.victoires + self.nuls + self.defaites
        if total == 0:
            return 50.0
        win_rate = (self.victoires * 3 + self.nuls) / (total * 3)
        avg_buts = min(self.buts_pour / total / 3.5, 1.0)
        avg_enc = 1.0 - min(self.buts_contre / total / 3.5, 1.0)
        forme_pts = sum(3 if c == 'W' else (1 if c == 'D' else 0) for c in self.forme_recente[-5:])
        forme_max = max(len(self.forme_recente[-5:]) * 3, 1)
        forme = forme_pts / forme_max
        score = (win_rate * 0.35 + avg_buts * 0.25 + avg_enc * 0.2 + forme * 0.2) * 100
        return round(score, 1)


class Stade(db.Model):
    __tablename__ = 'stades'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    ville = db.Column(db.String(50), default='')
    capacite = db.Column(db.Integer, default=50000)


class Match(db.Model):
    __tablename__ = 'matchs'
    id = db.Column(db.Integer, primary_key=True)
    domicile_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    exterieur_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    stade_id = db.Column(db.Integer, db.ForeignKey('stades.id'), nullable=False)
    date_match = db.Column(db.String(20), nullable=False)
    heure_match = db.Column(db.String(10), default='20:45')
    competition = db.Column(db.String(80), default='Ligue 1')
    score_dom = db.Column(db.Integer, nullable=True)
    score_ext = db.Column(db.Integer, nullable=True)
    statut = db.Column(db.String(10), default='futur')

    domicile = db.relationship('Equipe', foreign_keys=[domicile_id])
    exterieur = db.relationship('Equipe', foreign_keys=[exterieur_id])
    stade = db.relationship('Stade')
    zones = db.relationship('ZonePlace', backref='match', lazy=True, cascade='all, delete-orphan')

    @property
    def affichage(self):
        return f"{self.domicile.nom} vs {self.exterieur.nom}"

    @property
    def score_str(self):
        if self.score_dom is not None and self.score_ext is not None:
            return f"{self.score_dom} - {self.score_ext}"
        return None

    @property
    def places_restantes_total(self):
        return sum(z.places_restantes for z in self.zones)


class ZonePlace(db.Model):
    __tablename__ = 'zones_places'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matchs.id'), nullable=False)
    categorie = db.Column(db.String(60), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    places_totales = db.Column(db.Integer, nullable=False)
    places_restantes = db.Column(db.Integer, nullable=False)


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matchs.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones_places.id'), nullable=False)
    code_reservation = db.Column(db.String(12), unique=True, nullable=False)
    nom_client = db.Column(db.String(100), nullable=False)
    email_client = db.Column(db.String(150), nullable=False)
    numero_siege = db.Column(db.String(10), nullable=False)
    date_reservation = db.Column(db.String(30), nullable=False)

    match = db.relationship('Match')
    zone = db.relationship('ZonePlace')
