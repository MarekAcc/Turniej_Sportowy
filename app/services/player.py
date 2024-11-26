from app.models import Player
from app import db

def create_player(firstName, lastName, age, status):
    if status not in ['active','suspended']:
        raise ValueError('Invalid player status')
    
    new_player = Player(firstName=firstName, lastName=lastName, age=age, status=status)
    db.session.add(new_player)
    db.session.commit()

    return new_player