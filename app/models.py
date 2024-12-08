from . import db
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.Enum('league', 'playoff',
                     name='tournament_type_enum'), nullable=False)
    status = db.Column(db.Enum('active', 'ended', 'canceled',
                       name='tournament_status_enum'), nullable=False)

    teams = db.relationship('Team', back_populates='tournament')
    matches = db.relationship(
        'Match', back_populates='tournament', cascade="all, delete-orphan")

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

    # Funkcja dodająca druzyne do turnieju(jezeli turniej jest active to nie mozna dodawac)
    # Dodawanie druzyny przez nazwę(NIE PRZEZ ID, zeby nie trzeba pisac konwersji z frontendu)
    @classmethod
    def add_team(cls, name, team_name):
        # Wyszukujemy turniej po ID
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError(f"Turniej o nazwie {name} nie istnieje.")

        # Sprawdzamy, czy turniej jest w stanie "active"
        if tournament.status == 'active':
            raise ValueError("Nie można dodać drużyny do aktywnego turnieju.")

        # Wyszukujemy drużynę po nazwie
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            raise ValueError(f"Drużyna o nazwie {team_name} nie istnieje.")

        # Dodajemy drużynę do turnieju
        if team in tournament.teams:
            raise ValueError(
                f"Drużyna {team_name} już znajduje się w turnieju {name}.")

        tournament.teams.append(team)
        db.session.commit()

    @classmethod
    def get_teams(cls):
        return cls.query.first().teams

    # obsluga bledow
    @classmethod
    def remove_team_from_tournament(cls, name, team_name):
        # Wyszukujemy turniej po nazwie
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError(f"Turniej o nazwie {name} nie istnieje.")

        # Sprawdzamy, czy turniej nie jest zakończony
        if tournament.status == 'ended':
            raise ValueError(
                "Nie można usuwać drużyn z zakończonego turnieju.")

        # Wyszukujemy drużynę po nazwie
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            raise ValueError(f"Drużyna o nazwie {team_name} nie istnieje.")

        if team not in tournament.teams:
            raise ValueError(
                f"Drużyna {team_name} nie znajduje się w turnieju {name}."
            )

        tournament.teams.remove(team)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Wystąpił błąd przy usuwaniu drużyny z turnieju.")

    # Transakcja, trzeba wykonac inne operacje, upewnic się i wgl

    @classmethod
    def finish(cls, name):
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError("Turniej nie istnieje.")

        if tournament.status == 'ended':
            raise ValueError("Turniej już został zakończony.")

        tournament.status = 'ended'
        db.session.commit()
    # Anulowanie turnieju, przerwanie go mimo, ze sie nie zakonczyl

    @classmethod
    def cancel(cls, name):
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError("Turniej nie istnieje.")

        if tournament.status == 'canceled':
            raise ValueError("Turniej już został anulowany.")

        tournament.status = 'canceled'
        db.session.commit()


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    tournament = db.relationship('Tournament', back_populates='teams')
    players = db.relationship('Player', back_populates='team')

    teamCoach = db.relationship('Coach', back_populates='team')

    # Relacje do meczów
    home_matches = db.relationship(
        "Match", foreign_keys="Match.homeTeam_id", back_populates="home_team")
    away_matches = db.relationship(
        "Match", foreign_keys="Match.awayTeam_id", back_populates="away_team")

    @classmethod
    def get_teams(cls, n=None, sort_by="name"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    @classmethod
    def find_team(cls, name):
        """Znajduje drużynę na podstawie nazwy."""
        return cls.query.filter_by(name=name).first()

    def get_players(cls, name):
        team = cls.query.get(name)
        if not team:
            return 0
        return team.players

    @classmethod
    def edit_data(cls, team_id, name=None):
        """Edytuje dane drużyny. Nazwa i ID turnieju są opcjonalne."""

        team = cls.query.get(team_id)
        if not team:
            raise ValueError("Drużyna o podanym ID nie istnieje.")

        if name:
            team.name = name
        db.session.commit()

    # Bezpieczne usuwanie druzyny z bazy danych(odpiac zawodnikow i trenrea, sprawdzic czy nie rozgrywa turnieju itp.)
    @classmethod
    def delete_team(cls, team_id):
        """
        Usuwa drużynę z bazy danych. Przed usunięciem:
        - Odłącza zawodników i trenera.
        - Sprawdza, czy drużyna uczestniczy w turnieju.
        """
        if not team_id:
            raise ValueError("Musisz podać ID drużyny do usunięcia.")

        team = cls.query.get(team_id)
        if not team:
            raise ValueError("Drużyna o podanym ID nie istnieje.")

        if team.tournament_id:
            raise ValueError(
                "Nie można usunąć drużyny uczestniczącej w turnieju.")

        # Odłącz zawodników i trenera
        for player in team.players:
            player.team_id = None
        if team.teamCoach:
            team.teamCoach.team_id = None

        db.session.delete(team)
        db.session.commit()

    # Zwracanie statystyk i danych ???
    @classmethod
    def get_data(cls, team_id):
        """
        Zwraca statystyki i dane drużyny, takie jak liczba zawodników, trener, mecze.
        """
        team = cls.query.get(team_id)
        if not team:
            raise ValueError("Drużyna o podanym ID nie istnieje.")

        return {
            "name": team.name,
            "tournament": team.tournament.name if team.tournament else None,
            "coach": team.teamCoach.name if team.teamCoach else None,
            "players": [player.name for player in team.players],
            "matches": {
                "home": [match.id for match in team.home_matches],
                "away": [match.id for match in team.away_matches],
            }
        }


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(51), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Enum('substitute', 'field',
                         name='player_position_enum'))
    status = db.Column(db.Enum('active', 'suspended',
                       name='player_status_enum'), nullable=False)
    goals = db.Column(db.Integer, default=0)
    appearances = db.Column(db.Integer, default=0)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

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
    def find_player(cls, first_name, last_name, age=None):
        # Tworzymy zapytanie do bazy danych
        query = cls.query.filter_by(firstName=first_name, lastName=last_name)
        if age is not None:
            query = query.filter_by(age=age)

        # Pobieramy wszystkich zawodników spełniających kryteria
        players = query.all()

        if not players:
            raise ValueError(
                f"Nie znaleziono zawodnika o imieniu {first_name} i nazwisku {last_name}.")

        return players

    # Bezpieczne usuwanie zawodnika
    @classmethod
    def delete_player(cls, first_name, last_name):
        # Wyszukujemy zawodnika po imieniu i nazwisku
        player = cls.query.filter_by(
            firstName=first_name, lastName=last_name).first()
        if not player:
            raise ValueError(
                f"Zawodnik o imieniu {first_name} i nazwisku {last_name} nie istnieje.")

        # Sprawdzamy, czy zawodnik jest aktywny
        if player.status == 'active':
            raise ValueError("Nie można usunąć aktywnego zawodnika.")

        # Sprawdzamy, czy zawodnik jest przypisany do jakiegoś zespołu
        if player.team:
            raise ValueError(
                f"Zawodnik należy do drużyny {player.team.name}. Najpierw usuń go z drużyny.")

        # Usuwamy zawodnika
        db.session.delete(player)
        db.session.commit()


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scoreHome = db.Column(db.Integer)
    scoreAway = db.Column(db.Integer)
    status = db.Column(
        db.Enum('planned', 'ended', name='match_status_enum'), nullable=False)

    homeTeam_id = db.Column(
        db.Integer, db.ForeignKey('team.id'), nullable=False)
    awayTeam_id = db.Column(
        db.Integer, db.ForeignKey('team.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey(
        'tournament.id'), nullable=False)

    home_team = db.relationship(
        "Team", foreign_keys=[homeTeam_id], back_populates="home_matches")
    away_team = db.relationship(
        "Team", foreign_keys=[awayTeam_id], back_populates="away_matches")
    tournament = db.relationship("Tournament", back_populates="matches")

    matchEvents = db.relationship('MatchEvent', back_populates='match')

    @classmethod
    def get_matches(cls, n=None, sort_by="id"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    # TO DO metody takie jak przy torunamencie itp.

    @classmethod
    def find_match(cls, home_team_name, away_team_name, tournament_name):
        home_team = Team.query.filter_by(name=home_team_name).first()
        away_team = Team.query.filter_by(name=away_team_name).first()
        tournament = Tournament.query.filter_by(name=tournament_name).first()

        if not home_team:
            raise ValueError(f"Drużyna {home_team_name} nie istnieje.")
        if not away_team:
            raise ValueError(f"Drużyna {away_team_name} nie istnieje.")
        if not tournament:
            raise ValueError(f"Turniej {tournament_name} nie istnieje.")

        match = cls.query.filter_by(
            homeTeam_id=home_team.id,
            awayTeam_id=away_team.id,
            tournament_id=tournament.id
        ).first()

        if not match:
            raise ValueError(
                "Nie znaleziono meczu z podanymi drużynami w danym turnieju.")

        return match

    @classmethod
    def add_match(cls, home_team_name, away_team_name, tournament_name):
        # Znajdujemy drużyny i turniej
        home_team = Team.query.filter_by(name=home_team_name).first()
        away_team = Team.query.filter_by(name=away_team_name).first()
        tournament = Tournament.query.filter_by(name=tournament_name).first()

        if not home_team:
            raise ValueError(f"Drużyna {home_team_name} nie istnieje.")
        if not away_team:
            raise ValueError(f"Drużyna {away_team_name} nie istnieje.")
        if not tournament:
            raise ValueError(f"Turniej {tournament_name} nie istnieje.")

        # Sprawdzamy, czy mecz między tymi drużynami już istnieje w turnieju
        existing_match = cls.query.filter_by(
            homeTeam_id=home_team.id,
            awayTeam_id=away_team.id,
            tournament_id=tournament.id
        ).first()

        if existing_match:
            raise ValueError(
                "Mecz między tymi drużynami w tym turnieju już istnieje.")

        # Dodajemy nowy mecz
        new_match = cls(
            scoreHome=0,
            scoreAway=0,
            status='planned',
            homeTeam_id=home_team.id,
            awayTeam_id=away_team.id,
            tournament_id=tournament.id
        )
        db.session.add(new_match)
        db.session.commit()

    @classmethod
    def finish_match(cls, home_team_name, away_team_name, tournament_name, score_home, score_away):
        match = cls.find_match(home_team_name, away_team_name, tournament_name)
        if match.status == 'ended':
            raise ValueError("Mecz już został zakończony.")

        match.scoreHome = score_home
        match.scoreAway = score_away
        match.status = 'ended'
        db.session.commit()

    @classmethod
    def cancel_match(cls, home_team_name, away_team_name, tournament_name):
        match = cls.find_match(home_team_name, away_team_name, tournament_name)
        if match.status == 'ended':
            raise ValueError("Nie można anulować zakończonego meczu.")

        match.status = 'canceled'
        db.session.commit()

    @classmethod
    def remove_match(cls, home_team_name, away_team_name, tournament_name):
        match = cls.find_match(home_team_name, away_team_name, tournament_name)
        try:
            db.session.delete(match)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Wystąpił błąd podczas usuwania meczu.")


class MatchEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventType = db.Column(
        db.Enum('goal', 'redCard', name='matchEvent_type_enum'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey(
        'player.id'), nullable=False)

    match = db.relationship('Match', back_populates='matchEvents')
    player = db.relationship('Player', back_populates='playerEvents')

    @classmethod
    def get_match_events(cls, n=None, sort_by="id"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    @classmethod
    def find_events_for_player(cls, player_name):
        """
        Wyszukuje wszystkie wydarzenia dla zawodnika na podstawie jego imienia i nazwiska.
        """
        player = Player.query.filter_by(name=player_name).first()
        if not player:
            raise ValueError(f"Zawodnik o nazwie {player_name} nie istnieje.")

        events = cls.query.filter_by(player_id=player.id).all()
        if not events:
            raise ValueError(f"Brak wydarzeń dla zawodnika {player_name}.")

        return events

    @classmethod
    def find_events_for_match(cls, home_team_name, away_team_name, tournament_name):
        """
        Wyszukuje wszystkie wydarzenia dla danego meczu na podstawie nazw drużyn i turnieju.
        """
        match = Match.find_match(
            home_team_name, away_team_name, tournament_name)
        if not match:
            raise ValueError(
                f"Mecz pomiędzy {home_team_name} i {away_team_name} w turnieju {tournament_name} nie istnieje.")

        events = cls.query.filter_by(match_id=match.id).all()
        if not events:
            raise ValueError(
                f"Brak wydarzeń dla meczu pomiędzy {home_team_name} i {away_team_name} w turnieju {tournament_name}.")

        return events

    @classmethod
    def add_event(cls, match_id, player_name, event_type):
        """
        Dodaje nowe wydarzenie do meczu.
        """
        # Wyszukaj mecz
        match = Match.query.get(match_id)
        if not match:
            raise ValueError(f"Mecz o ID {match_id} nie istnieje.")

        # Wyszukaj zawodnika
        player = Player.query.filter_by(name=player_name).first()
        if not player:
            raise ValueError(f"Zawodnik o nazwie {player_name} nie istnieje.")

        # Utwórz nowe wydarzenie
        new_event = cls(eventType=event_type,
                        match_id=match.id, player_id=player.id)

        # Dodaj do sesji
        db.session.add(new_event)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Wystąpił błąd podczas dodawania wydarzenia.")

    @classmethod
    def remove_event(cls, event_id):
        """
        Usuwa wydarzenie na podstawie jego ID.
        """
        event = cls.query.get(event_id)
        if not event:
            raise ValueError(f"Wydarzenie o ID {event_id} nie istnieje.")

        # Usuń wydarzenie z sesji
        try:
            db.session.delete(event)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Wystąpił błąd podczas usuwania wydarzenia.")

    # TO DO metody takie jak przy torunamencie itp.


class Coach(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', back_populates='teamCoach')

    login = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    @classmethod
    def get_coaches(cls, n=None, sort_by="lastName"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    # Bezpieczne usuwanie zawodnika
    def delete_coach():
        print("TO DO")
