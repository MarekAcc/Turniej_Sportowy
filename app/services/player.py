from app.models import Player
from app import db

def new_player(firstName, lastName, age):
    if len(firstName) > 50:
        raise ValueError('Imię jest za długie!')
    if len(lastName) > 50:
        raise ValueError('Nazwisko jest za długie!')

    new_player = Player(firstName=firstName, lastName=lastName, age=int(age), status='active')
    db.session.add(new_player)
    db.session.commit()