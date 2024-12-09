# Tutaj dodać wszystkie funkcje do tworzenia instancji Modeli
# Operacje na modelach dodać jako metody
<<<<<<< HEAD
from app.models import Player, Tournament, Team, Coach, Match, MatchEvent
=======
from app.models import Player, Tournament, Team, Coach, Match,MatchEvent
>>>>>>> Marek
from app import db


def create_player(firstName, lastName, age):
    if len(firstName) > 50:
        raise ValueError('Imię jest za długie!')
    if len(lastName) > 50:
        raise ValueError('Nazwisko jest za długie!')

    new_player = Player(firstName=firstName, lastName=lastName,
                        age=int(age), status='active')
    db.session.add(new_player)
    db.session.commit()

    # tutaj pozmieniać to co będzie sprawdzanie przy frontendzie a co przy backendzie


def create_tournament(name, type, status):
    if len(name) > 100:
        raise ValueError('Nazwa turnieju jest za długa!')

    if Tournament.query.filter_by(name=name).first():
        raise ValueError(f"Turniej o nazwie '{name}' już istnieje!")

    if type == 'Liga':
        type = 'league'
    elif type == 'Turniej pucharowy':
        type = 'playoff'
    else:
        raise ValueError('Błąd formatu!')
<<<<<<< HEAD
=======
    
>>>>>>> Marek

    if status == 'Aktywny':
        status = 'active'
    elif status == 'Zakończony':
        status = 'ended'
    elif status == 'Anulowany':
        status = 'canceled'
    elif status == 'planned':
        status = 'planned'
    else:
        raise ValueError('Błąd statusu!')

    new_tournament = Tournament(name=name, type=type, status=status)
    db.session.add(new_tournament)
    db.session.commit()
    return new_tournament

<<<<<<< HEAD

def create_team(name, tournament_name, players):
    if len(name) > 100:
        raise ValueError('Nazwa drużyny jest za długa!')

    if Team.query.filter_by(name=name).first():
        raise ValueError(f"Drużyna o nazwie '{name}' już istnieje!")

    tournament = Tournament.query.filter_by(name=tournament_name).first()
    if not tournament:
        raise ValueError(f"Turniej o nazwie '{tournament_name}' NIE ISTNIEJE!")

    player_objects = []
    for p in players:
        first_name, last_name = p.split(" ", 1)
        player = Player.query.filter_by(
            firstName=first_name, lastName=last_name).first()
        if not player:
            raise ValueError(
                f"Zawodnik '{first_name} {last_name}' NIE ISTNIEJE!")
        if player.team_id is not None:
            raise ValueError(
                f"Zawodnik '{first_name} {last_name}' jest już przypisany do innej drużyny!")
        player_objects.append(player)

    # Wszystkie warunki są spełnione, można utworzyć drużynę
    new_team = Team(name=name, tournament_id=tournament.id)
=======
def create_team(name, players):
    if len(name) > 100 or len(name) < 4:
        raise ValueError('Nazwa druzyny jest nieprawidlowej dlugosci!')

    if Team.query.filter_by(name=name).first():
        raise ValueError(f"Druzyna o nazwie '{name}' już istnieje!")
    
    new_team = Team(name=name)
>>>>>>> Marek
    db.session.add(new_team)
    db.session.flush()  # Pobranie ID nowej drużyny bez zatwierdzania transakcji

    # Przypisanie zawodników do drużyny
    for player in player_objects:
        player.team_id = new_team.id

    # Zatwierdzenie całej transakcji
    db.session.commit()

<<<<<<< HEAD
=======
    for p in players:
        if p.team_id != None:
            raise ValueError(f"Zawodnik '{p.first_name} {p.last_name}' jest juz przypisany do innej druzyny!")
        p.team_id = new_team.id
        
    db.session.commit()
>>>>>>> Marek

def create_coach(firstName, lastName, age, login, password1, password2):
    if len(firstName) > 50:
        raise ValueError('Imię jest za długie!')

    if len(lastName) > 50:
        raise ValueError('Nazwisko jest za długie!')

    if len(login) < 4 or len(login) > 30:
        raise ValueError(
            'Login jest nieprawdłowej długości! min. 4 znaki max. 30')

    if Coach.query.filter_by(login=login).first():
        raise ValueError(
            f"Uzytkownik '{login}' juz istnieje! Wybierz inny login.")

    if len(password1) < 4 or len(password1) > 50:
        raise ValueError(
            'Hasło jest nieprawdłowej długości! min. 4 znaki max. 50')

    # Wrzucic do walidacji formularza (poza tą funkcją)
    if password1 != password2:
        raise ValueError('Hasła nie są takie same!')

    new_coach = Coach(firstName=firstName, lastName=lastName,
                      age=age, login=login, password=password1)
    db.session.add(new_coach)
    db.session.commit()
    return new_coach


def create_match(homeTeam_id, awayTeam_id, scoreHome, scoreAway, status):
    # Pobranie drużyn z bazy danych
    home_team = Team.query.get(homeTeam_id)
    away_team = Team.query.get(awayTeam_id)

    # Sprawdzenie, czy drużyny należą do tego samego turnieju
    if home_team.tournament_id != away_team.tournament_id:
        raise ValueError("Drużyny muszą należeć do tego samego turnieju!")

    if home_team == away_team:
        raise ValueError("Drużyny nie moga być takie same!")
    # Ustalenie tournament_id na podstawie drużyn
    tournament_id = home_team.tournament_id

    # Utworzenie nowego meczu
    new_match = Match(
        homeTeam_id=homeTeam_id,
        awayTeam_id=awayTeam_id,
        scoreHome=int(scoreHome),
        scoreAway=int(scoreAway),
        status=status,
        tournament_id=tournament_id
    )

    # Zapis do bazy danych
    db.session.add(new_match)
    db.session.commit()

    return new_match
<<<<<<< HEAD


def create_match_event(eventType, match_id, player_id):

    new_match_event = MatchEvent(
        eventType=eventType,
        match_id=match_id,
        player_id=player_id
    )

    db.session.add(new_match_event)
    db.session.commit()

    return new_match_event
=======
def create_match_event(eventType, match_id, player_id):
    
    
    new_match_event = MatchEvent(
    eventType = eventType,
    match_id = match_id,
    player_id = player_id
    )
    
    
    db.session.add(new_match_event)
    db.session.commit()
    
    return new_match_event
>>>>>>> Marek
