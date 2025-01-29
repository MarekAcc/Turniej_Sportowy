# Tutaj dodać wszystkie funkcje do tworzenia instancji Modeli
# Operacje na modelach dodać jako metody
from app.models import Player, Tournament, Team, Coach, Match, MatchEvent, Referee
from app import db


# Funkcja dodawania zawodnika do bazy
def create_player(firstName, lastName, age):
    if len(firstName) > 50 or len(firstName) < 1:
        raise ValueError('Imię jest za długie!')
    if len(lastName) > 50 or len(lastName) < 1:
        raise ValueError('Nazwisko jest za długie!')
    if int(age) < 12 or int(age) > 99:
        raise ValueError('Nieprawidłowy wiek!')

    new_player = Player(firstName=firstName, lastName=lastName,
                        age=int(age), status='active')
    db.session.add(new_player)
    db.session.commit()


def create_tournament(name, type, status):
    if len(name) > 100 or len(name) < 4:
        raise ValueError('Nazwa turnieju jest nieprawidłowej dlugości! (4-100 znaków)')

    if Tournament.query.filter_by(name=name).first():
        raise ValueError(f"Turniej o nazwie '{name}' już istnieje!")

    if type == 'Liga':
        type = 'league'
        round = None
    elif type == 'Turniej pucharowy':
        type = 'playoff'
        round = 1
    else:
        raise ValueError('Błąd formatu!')

    new_tournament = Tournament(
        name=name, type=type, status=status, round=round)
    db.session.add(new_tournament)
    db.session.commit()
    return new_tournament


def create_team(name, players, coach):
    if len(name) > 100 or len(name) < 4:
        raise ValueError('Nazwa druzyny jest nieprawidlowej dlugosci!')

    if Team.query.filter_by(name=name).first():
        raise ValueError(f"Druzyna o nazwie '{name}' już istnieje!")
    
    if coach.team != None:
        raise ValueError(f"Trener {coach.firstName} {coach.lastName} jest juz przeypisany do innej druzyny!")

    new_team = Team(name=name)
    db.session.add(new_team)
    db.session.commit()

    # for p in players:
    #     if p.team_id != None:
    #         raise ValueError(
    #             f"Zawodnik '{p.first_name} {p.last_name}' jest juz przypisany do innej druzyny!")
    #     p.team_id = new_team.id

    coach.team_id = new_team.id

    db.session.commit()


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
    '''Dodać do aktualizuj status meczu'''
    players_home = home_team.players
    players_away = away_team.players
    for player in players_home:
        if player.position == "field":
            player.appearances += 1
        if player.status == "suspended":
            player.status == "active"
    for player in players_away:
        if player.position == "field":
            player.appearances += 1
        if player.status == "suspended":
            player.status == "active"

    # Zapis do bazy danych
    db.session.add(new_match)
    db.session.commit()

    return new_match


def create_match_event(eventType, match_id, player_id):

    match = Match.query.get(match_id)
    if not match:
        raise ValueError(f"Mecz o ID {match_id} nie istnieje.")

    # Pobranie turnieju
    tournament = match.tournament
    if not tournament:
        raise ValueError(f"Turniej dla meczu o ID {match_id} nie istnieje.")

    # Zabezpieczenie przed dodawaniem wydarzeń, jeśli wygenerowano kolejną rundę
    if tournament.type == 'playoff' and tournament.round > match.round:
        raise ValueError(
            "Nie można dodawać wydarzeń do meczu, ponieważ następna runda turnieju została już wygenerowana."
        )

    # Sprawdzenie, czy można dodać kolejny gol
    if eventType == "goal":
        # Zliczanie istniejących wydarzeń typu "goal" w meczu
        current_home_goals = len([
            event for event in match.matchEvents
            if event.eventType == "goal" and event.player_id in [player.id for player in match.home_team.players]
        ])
        current_away_goals = len([
            event for event in match.matchEvents
            if event.eventType == "goal" and event.player_id in [player.id for player in match.away_team.players]
        ])

        # Sprawdzenie, czy dodanie kolejnego gola jest możliwe
        if (current_home_goals and current_home_goals >= match.scoreHome) and (current_away_goals and current_away_goals >= match.scoreAway):
            raise ValueError(
                f"Nie można dodać kolejnego gola, wynik meczu już został osiągnięty.")

    new_match_event = MatchEvent(
        eventType=eventType,
        match_id=match_id,
        player_id=player_id
    )

    player = Player.query.get(player_id)
    if not player:
        raise ValueError(f"Zawodnik o ID {player_id} nie istnieje.")

    if eventType == "goal":
        player.goals += 1
    elif eventType == "redCard":
        player.status = "suspended"

    db.session.add(new_match_event)
    db.session.commit()

    return new_match_event


def create_referee(firstName, lastName, age):
    if len(firstName) > 50 or len(firstName) < 1:
        raise ValueError('Imię jest za długie!')
    if len(lastName) > 50 or len(lastName) < 1:
        raise ValueError('Nazwisko jest za długie!')
    if int(age) < 12 or int(age) > 99:
        raise ValueError('Nieprawidłowy wiek!')

    new_referee = Referee(firstName=firstName, lastName=lastName,
                          age=int(age))
    db.session.add(new_referee)
    db.session.commit()
