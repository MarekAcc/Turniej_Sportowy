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

#Funkcja do zwracania n zawodnikoww. (obsluga błędów, co gdy nie ma tylu zawodnikow, funkcje sortowania(np alfabetycznie, albo inne opcje)
def get_players(n):
    # TO DO
    print(n)
