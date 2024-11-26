from app.models import Tournament
from app import db

def create_tournament(name, type, status):
    if type not in ['league', 'playoff']:
        raise ValueError('Invalid tournament type')
    if status not in ['active','ended','canceled']:
        raise ValueError('Invalid tournament status')
    
    new_tournament = Tournament(name=name, type=type, status=status)
    db.session.add(new_tournament)
    db.session.commit()

    return new_tournament