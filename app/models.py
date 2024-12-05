from . import db
from flask_login import UserMixin


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),unique=True ,nullable=False)
    type = db.Column(db.Enum('league', 'playoff', name='tournament_type_enum'), nullable=False)
    status = db.Column(db.Enum('active','ended','canceled',name='tournament_status_enum'), nullable=False)

    teams = db.relationship('Team', back_populates='tournament')
    matches = db.relationship('Match', back_populates='tournament', cascade="all, delete-orphan")


    # Jakaś obsluga błędów - raise ValueError('KOMUNIKAT')
    @classmethod
    def get_tournaments(cls, n=None, sort_by="name"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()
    
    # TO DO obsługa błędów (co gdy nie znajdzie druzyny - raise ValueError('KOMUNIKAT'))
    @classmethod
    def find_tournament(cls, name):
        return cls.query.filter_by(name=name).first()
    
    # Funkcja dodająca druzyne do turnieju(jezeli turniej jest active to nie mozna dodawac(musi byc cancelled albo jakos zawieszony
    # Dodawanie druzyny przez nazwę(NIE PRZEZ ID, zeby nie trzeba pisac konwersji z frontendu)
    def add_team():
        print("TO DO")

    def get_teams():
        print("TO DO")

    def remove_team_from_tournament():
        print("TO DO")

    # Transakcja, trzeba wykonac inne operacje, upewnic się i wgl
    def finish():
        print("TO DO")
    
    # Anulowanie turnieju, przerwanie go mimo, ze sie nie zakonczyl
    def cancel():
        print("TO DO")
    

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),unique=True ,nullable=False)

    tournament_id = db.Column(db.Integer,db.ForeignKey('tournament.id'))
    tournament = db.relationship('Tournament', back_populates='teams')
    players = db.relationship('Player', back_populates='team')

    teamCoach = db.relationship('Coach', back_populates='team')
    
    # Relacje do meczów
    home_matches = db.relationship("Match", foreign_keys="Match.homeTeam_id", back_populates="home_team")
    away_matches = db.relationship("Match", foreign_keys="Match.awayTeam_id", back_populates="away_team")

    @classmethod
    def get_teams(cls, n=None, sort_by="name"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()
    
    @classmethod
    def find_team(cls, name):
        print("TO DO")
    
    def get_players():
        # TO DO
        print("TO DO")

    # cos do edytowania byc moze kilka roznych funkcji - ZATANOWIC SIE NAD TYM
    def edit_data():
        print("TO DO")

    # Bezpieczne usuwanie druzyny z bazy danych(odpiac zawodnikow i trenrea, sprawdzic czy nie rozgrywa turnieju itp.)
    def delete_team():
        print("TO DO")

    # Zwracanie statystyk i danych ???
    def get_data():
        print("TO DO")
        

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(51),nullable=False)
    lastName = db.Column(db.String(50),nullable=False)
    age = db.Column(db.Integer,nullable=False)
    position = db.Column(db.Enum('substitute','field',name='player_position_enum'))
    status = db.Column(db.Enum('active','suspended',name='player_status_enum'), nullable=False)
    goals = db.Column(db.Integer,default=0)
    appearances = db.Column(db.Integer,default=0)
    team_id = db.Column(db.Integer,db.ForeignKey('team.id'))

    team = db.relationship('Team', back_populates='players')
    playerEvents = db.relationship('MatchEvent', back_populates='player')

    @classmethod
    def get_players(cls, n=None, sort_by="lastName"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()
    
    # Wyszukiwanie zawodnika w bazie, szukanie po imieniu i nazwisku (UWAGA! Mogą istniec dwaj zawodnicy 
    # co się tak samo nazwyają i maja tyle samo lat - jakoś to rozwiązac np. wyswietlic obydwoch i poinformowac o tym usera)
    @classmethod
    def find_player(cls, id):
        print("TO DO")

    # Bezpieczne usuwanie zawodnika
    def delete_player():
        print("TO DO")


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scoreHome = db.Column(db.Integer)
    scoreAway = db.Column(db.Integer)
    status = db.Column(db.Enum('planned','ended',name='match_status_enum'), nullable=False)

    homeTeam_id = db.Column(db.Integer,db.ForeignKey('team.id'), nullable=False)
    awayTeam_id = db.Column(db.Integer,db.ForeignKey('team.id'), nullable=False)
    tournament_id = db.Column(db.Integer,db.ForeignKey('tournament.id'), nullable=False)

    home_team = db.relationship("Team",foreign_keys=[homeTeam_id], back_populates="home_matches")
    away_team = db.relationship("Team",foreign_keys=[awayTeam_id], back_populates="away_matches")
    tournament = db.relationship("Tournament", back_populates="matches")


    matchEvents = db.relationship('MatchEvent',back_populates='match')

    @classmethod
    def get_matches(cls, n=None, sort_by="id"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()
    
    # TO DO metody takie jak przy torunamencie itp.
    


class MatchEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventType = db.Column(db.Enum('goal','redCard',name='matchEvent_type_enum'), nullable=False)
    match_id = db.Column(db.Integer,db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer,db.ForeignKey('player.id'), nullable=False)

    match = db.relationship('Match',back_populates='matchEvents')
    player = db.relationship('Player', back_populates='playerEvents')

    @classmethod
    def get_match_events(cls, n=None, sort_by="id"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    # TO DO metody takie jak przy torunamencie itp.



class Coach(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50),nullable=False)
    lastName = db.Column(db.String(50),nullable=False)
    age = db.Column(db.Integer)
    team_id = db.Column(db.Integer,db.ForeignKey('team.id'))
    team = db.relationship('Team', back_populates='teamCoach')

    login = db.Column(db.String(30),nullable=False)
    password = db.Column(db.String(50),nullable=False)

    @classmethod
    def get_coaches(cls, n=None, sort_by="lastName"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    # Bezpieczne usuwanie zawodnika
    def delete_coach():
        print("TO DO")