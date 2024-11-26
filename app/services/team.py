from app.models import Team
from app import db

def create_team(name, tournament_id=None):
    if tournament_id:
        new_team = Team(name=name, tournament_id=tournament_id)
        db.session.add(new_team)
        db.session.commit()
    else:
        new_team = Team(name=name)
        db.session.add(new_team)
        db.session.commit()

    return new_team

