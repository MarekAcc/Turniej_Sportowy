from . import db


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),unique=True ,nullable=False)
    type = db.Column(db.Enum('league', 'playoff', name='tournament_type_enum'), nullable=False)
    status = db.Column(db.Enum('active','ended','canceled',name='tournament_status_enum'), nullable=False)

    teams = db.relationship('Team', back_populates='tournament')
    matches = db.relationship('Match', back_populates='tournament', cascade="all, delete-orphan")


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

class MatchEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventType = db.Column(db.Enum('goal','redCard',name='matchEvent_type_enum'), nullable=False)
    match_id = db.Column(db.Integer,db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer,db.ForeignKey('player.id'), nullable=False)

    match = db.relationship('Match',back_populates='matchEvents')
    player = db.relationship('Player', back_populates='playerEvents')

class Coach(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50),nullable=False)
    lastName = db.Column(db.String(50),nullable=False)
    age = db.Column(db.Integer)
    team_id = db.Column(db.Integer,db.ForeignKey('team.id'))
    team = db.relationship('Team', back_populates='teamCoach')

    login = db.Column(db.String(30),nullable=False)
    password = db.Column(db.String(50),nullable=False)


