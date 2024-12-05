from app.models import Coach
from app import db


def register_coach(firstName, lastName, age, login, password1, password2):
    if len(firstName) > 50:
        raise ValueError('Imię jest za długie!')
    
    if len(lastName) > 50:
        raise ValueError('Nazwisko jest za długie!')
    
    if len(login) < 4 or len(login) > 30:
        raise ValueError('Login jest nieprawdłowej długości! min. 4 znaki max. 30')
    
    if Coach.query.filter_by(login=login).first():
        raise ValueError(f"Uzytkownik '{login}' juz istnieje! Wybierz inny login.")
    
    if len(password1) < 4 or len(password1) > 50:
        raise ValueError('Hasło jest nieprawdłowej długości! min. 4 znaki max. 50')
    
    if password1 != password2 :
        raise ValueError('Hasła nie są takie same!')
    
    new_coach = Coach(firstName=firstName, lastName=lastName, age=age, login=login, password = password1)
    db.session.add(new_coach)
    db.session.commit()
    return new_coach
    
#Funkcja do zwracania n trenerów. (obsluga błędów, co gdy nie ma tylu coachow, funkcje sortowania(np alfabetycznie, albo inne opcje)
def get_coaches(n):
    # TO DO
    print(n)

    