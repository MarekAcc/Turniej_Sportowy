
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Tournament, Team, Match, Coach, Player, MatchEvent, Referee
from . import db
from .services.tournament import calculate_ranking
from .services.create import create_player, create_tournament, create_team, create_match, create_match_event
from flask_login import login_user, login_required, logout_user, current_user
from collections import defaultdict

views = Blueprint('views', __name__)

# HOME PAGE --------------------------------------------------------------------------------------------------------


@views.route('/')
def home():
    return render_template("home.html", user=current_user)


@views.route('/home-admin')
@login_required
def home_admin():
    tournament = Tournament.find_tournament('A Klasa')
    teams = Tournament.get_teams(tournament.id)

    return render_template("home_admin.html", user=current_user, tournament=tournament, teams=teams)


@views.route('/tournaments')
def tournaments():
    query = request.args.get('query')

    # Jeśli zapytanie jest obecne, używamy metody `find_tournament` z modelu
    if query:
        try:
            # Szukamy pojedynczego turnieju po nazwie
            tournament = Tournament.find_tournament(query)
            # Jeśli turniej został znaleziony, zwróć w liście
            tournaments = [tournament] if tournament else []
        except ValueError as e:
            # Obsługa błędów, np. gdy nie znaleziono turnieju
            flash(str(e), 'danger')
            tournaments = []
    else:
        # Jeśli brak zapytania, pobieramy wszystkie turnieje
        tournaments = Tournament.get_tournaments()

    return render_template("tournaments.html", tournaments=tournaments, user=current_user)


@views.route('/teams')
def teams():
    query = request.args.get('query')

    # Jeśli zapytanie jest obecne, używamy metody `find_team` z modelu
    if query:
        try:
            # Szukamy drużyny po nazwie
            team = Team.find_team(query)
            # Jeśli drużyna została znaleziona, zwróć ją w liście
            teams = [team] if team else []
        except ValueError as e:
            # Obsługa błędów, np. gdy nie znaleziono drużyny
            flash(str(e), 'danger')
            teams = []
    else:
        # Jeśli brak zapytania, pobieramy wszystkie drużyny
        teams = Team.get_teams()

    return render_template("teams.html", teams=teams, user=current_user)


@views.route('/players')
def players():
    query = request.args.get('query')

    if query:
        # Rozdzielamy query na imię i nazwisko, jeśli wpisano pełne imię i nazwisko
        parts = query.split(' ', 1)
        if len(parts) == 2:  # Jeśli podano dwa słowa
            first_name, last_name = parts
            players = Player.query.filter(
                (Player.firstName.ilike(f"%{first_name}%")) &
                (Player.lastName.ilike(f"%{last_name}%"))
            ).all()
        else:  # Jeśli podano jedno słowo, szukamy po imieniu lub nazwisku
            players = Player.query.filter(
                (Player.firstName.ilike(f"%{query}%")) |
                (Player.lastName.ilike(f"%{query}%"))
            ).all()

        message = None if players else "Nie znaleziono zawodników"
    else:
        players = Player.query.all()
        message = None

    return render_template("players.html", players=players, message=message, user=current_user)


@views.route('/coaches')
def coaches():
    query = request.args.get('query')

    if query:
        # Szukamy trenera po pełnym imieniu i nazwisku lub częściowym
        parts = query.split(' ', 1)
        if len(parts) == 2:
            first_name, last_name = parts
            coaches = Coach.query.filter(
                (Coach.firstName.ilike(f"%{first_name}%")) &
                (Coach.lastName.ilike(f"%{last_name}%"))
            ).all()
        else:
            coaches = Coach.query.filter(
                (Coach.firstName.ilike(f"%{query}%")) |
                (Coach.lastName.ilike(f"%{query}%"))
            ).all()
    else:
        coaches = Coach.query.all()

    return render_template("coaches.html", coaches=coaches, user=current_user)


@views.route('/referees')
def referees():
    query = request.args.get('query')

    if query:
        try:
            # Szukamy sędziego na podstawie zapytania
            referee = Referee.find_ref(query)
            referees = [referee] if referee else []

            if not referee:
                flash("Nie znaleziono sędziego.", 'danger')
        except ValueError as e:
            flash("Błąd w przetwarzaniu zapytania: " + str(e), 'danger')
            referees = []
    else:
        referees = Referee.get_refs()
    return render_template("referees.html", referees=referees, user=current_user)

@views.route('/referee/<int:referee_id>')
def referee_details(referee_id):
    referee = Referee.query.get(referee_id)
    matches = Match.query.filter(Match.referee_id == referee_id)
    
    return render_template("referee_details.html", referee=referee, user=current_user, matches = matches)

# detale dla stron --------------------------------------------------------------------------------------------------------


@views.route('/tournament/<int:tournament_id>')
def tournament_details(tournament_id):
    tournament = Tournament.query.get(tournament_id)

    if not tournament:
        flash("Turniej nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    ranking = None
    rounds = None

    # Logika dla turniejów ligowych
    if tournament.type == 'league':
        ranking = calculate_ranking(tournament_id)

    # Logika dla turniejów typu playoff
    elif tournament.type == 'playoff':
        matches = Match.query.filter_by(tournament_id=tournament_id).all()
        # Grupujemy mecze według rundy
        rounds = {r: [m for m in matches if m.round == r]
                  for r in range(1, tournament.round + 1)}

    # Pobieramy wszystkie mecze
    matches = Match.query.filter(Match.tournament_id == tournament_id).all()

    return render_template(
        "tournament_details.html",
        tournament=tournament,
        ranking=ranking,
        matches=matches,
        rounds=rounds,
        user=current_user
    )


@views.route('/team/<int:team_id>')
def team_details(team_id):
    # Pobieramy drużynę na podstawie ID
    team = Team.query.get(team_id)

    if not team:
        flash("Drużyna nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    # Pobieramy trenera drużyny
    coach = team.teamCoach

    # Pobieramy zawodników drużyny
    players = team.players

    # Pobieramy mecze drużyny (zarówno jako gospodarze, jak i goście)
    matches = team.home_matches + team.away_matches

    return render_template(
        "team_details.html",
        team=team,
        coach=coach,
        players=players,
        matches=matches,
        user=current_user
    )


@views.route('/match/<int:match_id>')
def match_details(match_id):
    match = Match.query.get(match_id)

    if not match:
        flash("Mecz nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    # Pobieramy wydarzenia związane z meczem
    match_events = MatchEvent.query.filter_by(match_id=match_id).all()

    return render_template("match_details.html", match=match, match_events=match_events, user=current_user)


@views.route('/player/<int:player_id>')
def player_details(player_id):
    # Pobieramy zawodnika na podstawie ID
    player = Player.query.get(player_id)

    if not player:
        flash("Zawodnik nie istnieje", "danger")
        return redirect(url_for('views.players'))

    # Pobieramy drużynę zawodnika
    team = player.team

    # Pobieramy MatchEventy zawodnika
    match_events = player.playerEvents

    return render_template(
        "player_details.html",
        player=player,
        team=team,
        match_events=match_events,
        user=current_user
    )


@views.route('/coach/<int:coach_id>')
def coach_details(coach_id):
    coach = Coach.query.get(coach_id)

    if not coach:
        flash("Trener nie istnieje", "danger")
        return redirect(url_for('views.coaches'))

    team = coach.team  # Relacja z modelem `Team`

    return render_template(
        "coach_details.html",
        coach=coach,
        team=team,
        user=current_user
    )

# FUNCJONALNOŚĆ TWORZENIA ---------------------------------------------------------------------------------------------------------------------


@views.route('/show-tournament', methods=['GET', 'POST'])
@login_required
def show_tournament():
    tournament = Tournament.find_tournament_by_id(30)
    teams = Tournament.get_teams(tournament.id)
    # Grupowanie meczów według rund
    matches_by_round = defaultdict(list)
    for match in tournament.matches:
        matches_by_round[match.round].append(match)

    # Sortowanie rund
    sorted_matches_by_round = dict(sorted(matches_by_round.items()))

    return render_template("tournament_admin.html", user=current_user, tournament=tournament, teams=teams, matches_by_round=sorted_matches_by_round)

# --------------COACH OD IGORA--------------------


@views.route('/coach-home', methods=['GET', 'POST'])
@login_required
def coach_home():
    return render_template("trener_p.html", user=current_user)


@views.route('/swap-players', methods=['GET', 'POST'])
@login_required
def swap_players():
    # Sprawdź, czy zalogowany użytkownik jest trenerem
    if not isinstance(current_user, Coach):
        flash("Nie masz uprawnień do zmiany zawodników.", "danger")
        return redirect(url_for('views.home'))

    # Pobierz wszystkich zawodników
    players = Player.get_players()

    if request.method == 'POST':
        # Pobierz dane z formularza
        new_player_id = request.form.get("new_player_id")
        player_id = request.form.get("player_id")

        # Walidacja danych wejściowych
        if not new_player_id or not player_id:
            flash("Należy wypełnić oba pola.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        try:
            new_player_id = int(new_player_id)
            player_id = int(player_id)
        except ValueError:
            flash("Wybierz poprawnych zawodników.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        # Pobierz zawodników z bazy danych
        new_player = Player.query.get(new_player_id)
        player = Player.query.get(player_id)

        # Sprawdź, czy zawodnicy istnieją
        if not new_player or not player:
            flash("Jeden lub obydwaj zawodnicy nie istnieją.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        # Sprawdź, czy zawodnik należy do drużyny trenera
        if player.team_id != current_user.team_id:
            flash("Zawodnik do wymiany nie należy do twojej drużyny.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        # Sprawdź, czy nowy zawodnik nie należy do żadnej drużyny
        if new_player.team_id is not None:
            flash("Nowy zawodnik jest już przypisany do drużyny.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        # Przeprowadzenie wymiany zawodników
        try:
            # Przypisz nowego zawodnika do drużyny trenera
            new_player.team_id = current_user.team_id
            # Usuń obecnego zawodnika z drużyny
            player.team_id = None

            db.session.commit()
            flash("Wymiana zawodnika zakończona pomyślnie!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Wystąpił błąd podczas wymiany zawodników. Spróbuj ponownie.", "danger")

        return redirect(url_for('views.swap_players'))

    return render_template("swap_players.html", user=current_user, players=players)


@views.route('/change-positions', methods=['GET', 'POST'])
@login_required
def change_positions():
    # Pobierz wszystkich zawodników
    players = Player.get_players()

    # Sprawdź, czy obecny użytkownik jest trenerem
    if not isinstance(current_user, Coach):
        flash("Nie masz uprawnień do zmiany pozycji zawodników.", "danger")
        return redirect(url_for('views.home'))

    if request.method == "POST":
        player_id = request.form.get("player_id")
        position = request.form.get("position")

        try:
            player_id = int(player_id)
            position = str(position)
        except (ValueError, TypeError):
            flash("Nieprawidłowe dane wejściowe.", "danger")
            return render_template("change_positions.html", user=current_user, players=players)

        # Pobierz zawodnika na podstawie ID
        player = Player.query.get(player_id)
        if not player:
            flash("Zawodnik nie istnieje.", "danger")
            return render_template("change_positions.html", user=current_user, players=players)

        # Sprawdź, czy zawodnik należy do drużyny
        if player.team_id is None:
            flash("Ten zawodnik nie należy do żadnej drużyny.", "danger")
            return render_template("change_positions.html", user=current_user, players=players)

        # Sprawdź, czy zawodnik należy do drużyny trenera
        if player.team_id != current_user.team_id:
            flash("Ten zawodnik nie należy do twojej drużyny.", "danger")
            return render_template("change_positions.html", user=current_user, players=players)

        # Sprawdź, czy zmieniasz na tę samą pozycję
        if player.position == position:
            flash("Zawodnik już jest na tej pozycji.", "danger")
            return render_template("change_positions.html", user=current_user, players=players)

        # Zaktualizuj pozycję zawodnika
        player.position = position
        db.session.commit()
        flash("Zmiana pozycji zakończona!", "success")
        return redirect(url_for('views.change_positions'))

    return render_template("change_positions.html", user=current_user, players=players)
