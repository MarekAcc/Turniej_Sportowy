from . import db
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(102), unique=True, nullable=False)
    type = db.Column(db.Enum('league', 'playoff',
                     name='tournament_type_enum'), nullable=False)
    status = db.Column(db.Enum('active', 'ended', 'canceled',
                       name='tournament_status_enum'), nullable=False)

    round = db.Column(db.Integer)
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

        # Sprawdzamy, czy turniej jest w stanie "active"
        if tournament.status == 'active':
            raise ValueError("Nie można dodać drużyny do aktywnego turnieju.")

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

    # obsluga bledow
    @classmethod
    def remove_team_from_tournament(cls, name, team_name):
        # Wyszukujemy turniej po nazwie
        tournament = cls.query.filter_by(name=name).first()
        if not tournament:
            raise ValueError(f"Turniej o nazwie {name} nie istnieje.")

        # Sprawdzamy, czy turniej nie jest zakończony
        if tournament.status == 'ended' or tournament.status == 'active':
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

    @classmethod
    def finish(cls, tournament_id):
        tournament = cls.query.get(tournament_id)
        if not tournament:
            raise ValueError("Turniej nie istnieje.")

        if tournament.status == 'ended':
            raise ValueError("Turniej już został zakończony.")

        # Sprawdzenie, czy istnieją mecze o statusie 'planned'
        planned_matches = Match.query.filter_by(
            tournament_id=tournament.id, status='planned').count()
        if planned_matches > 0:
            raise ValueError(
                "Nie można zakończyć turnieju, ponieważ istnieją niezakończone mecze.")

        # Dodatkowe zabezpieczenie dla turnieju typu 'playoff'
        if tournament.type == 'playoff':
            last_round = tournament.round
            ended_matches = Match.query.filter_by(
                tournament_id=tournament.id, round=last_round, status='ended').count()
            if ended_matches != 1:
                raise ValueError(
                    "Nie można zakończyć turnieju typu 'playoff', ponieważ ostatnia runda nie została poprawnie zakończona (dokładnie jeden mecz musi być zakończony).")

        tournament.status = 'ended'
        db.session.commit()
    # Anulowanie turnieju, przerwanie go mimo, ze sie nie zakonczyl

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

        if tournament.status != 'planned':
            raise ValueError(
                "Nie mozna usunąc turnieju, który trwa lub się odbył")

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
        elif tournament.type == 'playoff':  # 1 runda
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
    def generate_next_round(cls, tournament):
        current_round = tournament.round

        # Pobranie wszystkich meczów z aktualnej rundy
        matches_in_round = Match.query.filter_by(
            tournament_id=tournament.id,
            round=current_round
        ).all()

        # Sprawdzenie, czy wszystkie mecze w rundzie są zakończone
        if any(match.status != 'ended' for match in matches_in_round):
            raise ValueError(
                "Nie można wygenerować kolejnej rundy, dopóki wszystkie mecze obecnej rundy nie zostaną zakończone.")

        # Pobranie zwycięzców z zakończonych meczów
        winners = []
        for match in matches_in_round:
            if match.scoreHome > match.scoreAway:
                winners.append(match.home_team)
            elif match.scoreAway > match.scoreHome:
                winners.append(match.away_team)
            else:
                raise ValueError(
                    "Mecz zakończył się remisem, co nie jest dozwolone w turnieju play-off.")

        if len(winners) < 2:
            raise ValueError(
                "Pozostał tylko jeden zwycięzca! Ostatnia runda juz się odbyla!")
        # Sprawdzenie, czy liczba zwycięzców jest parzysta
        if len(winners) % 2 != 0:
            raise ValueError(
                "Nieparzysta liczba zwycięzców - coś poszło nie tak.")

        # Generowanie nowych meczów na podstawie zwycięzców
        next_round = current_round + 1
        new_matches = []
        for i in range(0, len(winners), 2):
            match = Match(
                homeTeam_id=winners[i].id,
                awayTeam_id=winners[i + 1].id,
                tournament_id=tournament.id,
                status='planned',
                scoreHome=None,
                scoreAway=None,
                round=next_round
            )
            new_matches.append(match)

        # Dodanie nowych meczów do bazy danych
        db.session.add_all(new_matches)

        # Aktualizacja rundy w turnieju
        tournament.round = next_round
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

    referee_id = db.Column(db.Integer, db.ForeignKey(
        'referee.id'))
    
    referee = db.relationship("Referee", foreign_keys=[referee_id], back_populates="matches")

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
    def finish_match(cls, match, scoreHome, scoreAway):
        homeTeam = match.home_team
        awayTeam = match.away_team

        if match.status == 'ended':
            raise ValueError("Mecz już został zakończony.")
        
        match.scoreHome = scoreHome
        match.scoreAway = scoreAway
        players_home = homeTeam.players
        players_away = awayTeam.players
        
        db.session.commit()
        
        for player in players_home:
            if player.position =="field":
                player.appearances+=1
            if player.status == "suspended":
                player.status == "active"
        for player in players_away:
            if player.position == "field":
                player.appearances+=1 
            if player.status == "suspended":
                player.status == "active"
        # Zapis zmian w bazie danych
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
    def remove_match(cls, id):
        match = cls.find_match_by_id(id)
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

    # Znajduje trenera po ID
    @classmethod
    def find_coach_by_id(cls, id):
        p = cls.query.get(id)
        if not p:
            raise ValueError("Nie istnieje trener o takim ID.")
        return p

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


class Referee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    matches = db.relationship('Match', back_populates='referee')

    @classmethod
    def find_ref(cls, query):
        """Znajdź sędziego na podstawie imienia i nazwiska."""
        first_name, last_name = query.split(" ", 1) if " " in query else (query, "")
        return cls.query.filter(
            db.and_(
                cls.firstName.ilike(f"%{first_name}%"),
                cls.lastName.ilike(f"%{last_name}%")
            )
        ).first()
    
    @classmethod
    def find_referee_by_id(cls, id):
        p = cls.query.get(id)
        if not p:
            raise ValueError("Nie istnieje sędzia o takim ID.")
        return p

    
    @classmethod
    def get_refs(cls, n = None, sort_by = "lastName"):
        query = cls.query.order_by(getattr(cls, sort_by).asc())
        if n:
            query = query.limit(n)
        return query.all()

        
        
