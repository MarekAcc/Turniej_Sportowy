from . import db
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from itertools import permutations
from random import shuffle


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(101), unique=True, nullable=False)
    type = db.Column(db.Enum('league', 'playoff',
                     name='tournament_type_enum'), nullable=False)
    status = db.Column(db.Enum('active', 'ended', 'canceled', 'planned',
                       name='tournament_status_enum'), nullable=False)

    teams = db.relationship('Team', back_populates='tournament')
    matches = db.relationship(
        'Match', back_populates='tournament', cascade="all, delete-orphan")

    @classmethod
    def get_tournaments(cls, n=None, sort_by="name"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

    @classmethod
    def find_tournament(cls, name):
        t = cls.query.filter_by(name=name).first()
        if not t:
            raise ValueError("Nie istnieje turniej o takiej nazwie.")
        return t

    # Szukanie turnieju po ID
    @classmethod
    def find_tournament_by_id(cls, id):
        t = cls.query.get(id)
        if not t:
            raise ValueError("Nie istnieje turniej o takim ID.")
        return t

    @classmethod
    def add_teams(cls, name, teams):
        # Wyszukujemy turniej po ID
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError(f"Turniej o nazwie {name} nie istnieje.")

        # Sprawdzamy, czy turniej jest w stanie 'planned'
        if tournament.status != 'planned':
            raise ValueError("Nie mozna dodac druzyn po rozpoczęciu turnieju")

        if not teams:
            raise ValueError(f"Brak druzyn")

        for team in teams:
            if team in tournament.teams:
                raise ValueError(
                    f"Drużyna {team.name} już znajduje się w turnieju {name}.")
            tournament.teams.append(team)
            team.tournament_id = tournament.id

        db.session.commit()

    @classmethod
    def get_teams(cls, id):
        tournament = cls.query.get(id)  # Pobierz turniej po ID
        if not tournament:
            raise ValueError(f"Nie znaleziono turnieju o ID {id}.")
        return tournament.teams

    @classmethod
    def remove_team_from_tournament(cls, name, team_name):
        # Wyszukujemy turniej po nazwie
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError(f"Turniej o nazwie {name} nie istnieje.")

        # Sprawdzamy, czy turniej nie jest zakończony
        if tournament.status == 'ended' or tournament.status == 'active':
            raise ValueError(
                "Nie można usuwać drużyn z zakończonego lub aktywnego turnieju.")

        # Wyszukujemy drużynę po nazwie
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            raise ValueError(f"Drużyna o nazwie {team_name} nie istnieje.")

        if team not in tournament.teams:
            raise ValueError(
                f"Drużyna {team_name} nie znajduje się w turnieju {name}."
            )

        tournament.teams.remove(team)
        team.tournament_id = None

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Wystąpił błąd przy usuwaniu drużyny z turnieju.")

    @classmethod
    def finish(cls, tournament_id):
        tournament = cls.query.get(tournament_id)
        if not tournament:
            raise ValueError("Turniej nie istnieje.")

        if tournament.status == 'ended':
            raise ValueError("Turniej już został zakończony.")

        tournament.status = 'ended'
        db.session.commit()

    @classmethod
    def cancel(cls, tournament_id):
        tournament = cls.query.get(tournament_id)
        if not tournament:
            raise ValueError("Turniej nie istnieje.")

        if tournament.status == 'canceled':
            raise ValueError("Turniej już został anulowany.")

        tournament.status = 'canceled'
        db.session.commit()

    @classmethod
    def delete(cls, tournament_id):
        tournament = cls.query.get(tournament_id)

        for team in tournament.teams:
            team.tournament_id = None

        for match in tournament.matches:
            db.session.delete(match)

        db.session.delete(tournament)
        db.session.commit()

    @classmethod
    def generate_matches(cls, tournament):
        matches = []
        teams = Tournament.get_teams(tournament.id)
        if tournament.type == 'league':
            for home_team, away_team in permutations(teams, 2):
                # Mecz 1: Gospodarzem jest home_team
                match1 = Match(
                    homeTeam_id=home_team.id,
                    awayTeam_id=away_team.id,
                    tournament_id=tournament.id,
                    status='planned',
                    scoreHome=None,
                    scoreAway=None,
                    round=None
                )
                matches.append(match1)
        elif tournament.type == 'playoff':
            shuffle(teams)
            # Generowanie meczów pierwszej rundy
            for i in range(0, len(teams), 2):
                home_team = teams[i]
                away_team = teams[i + 1]
                match = Match(
                    homeTeam_id=home_team.id,
                    awayTeam_id=away_team.id,
                    tournament_id=tournament.id,
                    status='planned',
                    scoreHome=None,
                    scoreAway=None,
                    round=1
                )
                matches.append(match)

        db.session.add_all(matches)
        db.session.commit()

    @classmethod
    def generate_next_round(cls, tournament, round):
        previous_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round=round-1,
            status='ended'
        ).all()
        winners = [match.home_team if match.scoreHome >
                   match.scoreAway else match.away_team for match in previous_matches]
        new_matches = []
        for i in range(0, len(winners), 2):
            match = Match(
                homeTeam_id=winners[i].id,
                awayTeam_id=winners[i + 1].id,
                tournament_id=tournament.id,
                status='planned',
                scoreHome=None,
                scoreAway=None,
                round=round + 1
            )
            new_matches.append(match)

        db.session.add_all(new_matches)
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
    def get_teams_without_tournament(cls):
        # Zwracamy wszystkich graczy, którzy nie mają przypisanego team_id
        return cls.query.filter(cls.tournament_id == None).all()

    @classmethod
    def find_team(cls, name):
        """Znajduje drużynę na podstawie nazwy."""
        return cls.query.filter_by(name=name).first()

    # Znajduje druzyne po ID
    @classmethod
    def find_team_by_id(cls, id):
        t = cls.query.get(id)
        if not t:
            raise ValueError("Nie istnieje druzyna o takim ID.")
        return t

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
        - Sprawdza czy druzyna gra/bedzie grała jakieś mecze
        """
        if not team_id:
            raise ValueError("Musisz podać ID drużyny do usunięcia.")

        team = cls.query.get(team_id)
        if not team:
            raise ValueError("Drużyna o podanym ID nie istnieje.")

        if team.tournament_id:
            raise ValueError(
                "Nie można usunąć drużyny uczestniczącej w turnieju.")
        
        if team.home_matches or team.away_matches:
            raise ValueError(
                "Nie można usunąć drużyny która grała/będzie grała mecze!")

        # Odłącz zawodników i trenera
        for player in team.players:
            player.team_id = None
        if team.teamCoach:
            team.teamCoach.team_id = None

        db.session.commit()

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
            "players": {
                "firstName": [player.firstName for player in team.players],
                "lastName ": [player.lastName for player in team.players]
            },
            "matches": {
                "home": [match.id for match in team.home_matches],
                "away": [match.id for match in team.away_matches],
            }
        }


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50), nullable=False)
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

    @classmethod
    def get_players_without_team(cls):
        # Zwracamy wszystkich graczy, którzy nie mają przypisanego team_id
        return cls.query.filter(cls.team_id == None).all()

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

    # Znajduje zawodnika po ID
    @classmethod
    def find_player_by_id(cls, id):
        p = cls.query.get(id)
        if not p:
            raise ValueError("Nie istnieje zawodnik o takim ID.")
        return p
    # Bezpieczne usuwanie zawodnika

    @classmethod
    def delete_player(cls, player_id):
        # Wyszukujemy zawodnika po imieniu i nazwisku
        player = cls.query.get(player_id)
        if not player:
            raise ValueError(
                f"Zawodnik nie istnieje.")

        # Sprawdzamy, czy zawodnik jest przypisany do jakiegoś zespołu
        if player.team:
            raise ValueError(
                f"Zawodnik należy do drużyny {player.team.name}. Najpierw usuń go z drużyny.")
        
        if player.playerEvents:
            raise ValueError(
                f"Zawodnik {player.firstName} {player.lastName} uczestniczył w MatchEventach! Nie mozesz go usunąć!")

        # Usuwamy zawodnika
        db.session.delete(player)
        db.session.commit()


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scoreHome = db.Column(db.Integer)
    scoreAway = db.Column(db.Integer)
    status = db.Column(
        db.Enum('planned', 'ended', name='match_status_enum'), nullable=False)
    round = db.Column(db.Integer)

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
    def find_match_by_id(cls, id):
        m = cls.query.get(id)
        if not m:
            raise ValueError("Nie istnieje mecz o takim ID.")
        return m

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

    @classmethod
    def find_coach(cls, query):
        """Szukamy trenera po imieniu i nazwisku."""
        return cls.query.filter(
            (cls.firstName + ' ' + cls.lastName).like(f"%{query}%")
        ).all()

    # Bezpieczne usuwanie trenera
    @classmethod
    def delete_coach(cls, coach_id):
        if not coach_id:
            raise ValueError("Musisz podać ID trenera do usunięcia.")
        coach = cls.query.get(coach_id)
        if coach.team_id:
            coach.team_id = None
        db.session.delete(coach_id)
        db.session.commit()
