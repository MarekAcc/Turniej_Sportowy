
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Tournament,Team,Match, Coach, Player, MatchEvent
from . import db
from .services.create import create_player, create_tournament, create_team, create_match, create_match_event
from flask_login import login_user, login_required, logout_user, current_user
from collections import defaultdict

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html", user=current_user)

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
        first_name, *last_name_parts = query.split(' ', 1)
        last_name = last_name_parts[0] if last_name_parts else ""

        # Wykorzystanie istniejącej metody do wyszukiwania
        try:
            players = Player.find_player(
                first_name=first_name, last_name=last_name)
        except ValueError as e:
            players = []
            message = str(e)
        else:
            message = None
    else:

        players = Player.get_players()
        message = None

    return render_template("players.html", players=players, message=message, user=current_user)


@views.route('/coaches')
def coaches():
    query = request.args.get('query')

    if query:
        # Szukamy trenera po pełnym imieniu i nazwisku
        coaches = Coach.find_coach(query)
    else:
        coaches = Coach.get_coaches()

    return render_template("coaches.html", coaches=coaches, user=current_user)


@views.route('/referees')
def referees():
    return render_template("referees.html", referees=referees, user=current_user)


@views.route('/tournament/<int:tournament_id>')
def tournament_details(tournament_id):
    tournament = Tournament.query.get(tournament_id)

    if not tournament:
        flash("Turniej nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    # Pobieramy drużyny w turnieju
    teams = tournament.teams

    # Pobieramy mecze rozegrane i zaplanowane w turnieju
    matches = Match.query.filter((Match.tournament_id == tournament_id)).all()

    return render_template("tournament_details.html", tournament=tournament, teams=teams, matches=matches, user=current_user)


@views.route('/team/<int:team_id>')
def team_details(team_id):
    team = Team.query.get(team_id)

    if not team:
        flash("Drużyna nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    # Pobieramy mecze drużyny w turnieju
    matches = team.home_matches + team.away_matches

    return render_template("team_details.html", team=team, matches=matches, user=current_user)


@views.route('/match/<int:match_id>')
def match_details(match_id):
    match = Match.query.get(match_id)

    if not match:
        flash("Mecz nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    # Pobieramy wydarzenia związane z meczem
    match_events = MatchEvent.query.filter_by(match_id=match_id).all()

    return render_template("match_details.html", match=match, match_events=match_events)



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

    return render_template("tournament_admin.html", user=current_user, tournament=tournament, teams=teams,matches_by_round=sorted_matches_by_round)


@views.route('/match-adder', methods=['GET', 'POST'])
@login_required
def match_adder():
    if request.method == 'POST':
        homeTeam_id = request.form.get('homeTeam_id')
        awayTeam_id = request.form.get('awayTeam_id')
        scoreHome = request.form.get('scoreHome')
        scoreAway = request.form.get('scoreAway')
        status = request.form.get('status')

        if not homeTeam_id or not awayTeam_id:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('register_match.html', user=current_user)

        try:
            create_match(homeTeam_id, awayTeam_id,
                         scoreHome, scoreAway, status)
            flash('Mecz został pomyślnie dodany!', 'success')
        except ValueError as e:
            flash(str(e), 'danger')

    teams = Team.query.all()

    return render_template(
        "register_match.html",
        teams=teams
    )

#--------------COACH OD IGORA--------------------

@views.route('/coach-home', methods=['GET','POST'])
@login_required
def coach_home():
    return render_template("trener_p.html", user =current_user)

@views.route('/swap-players', methods=['GET', 'POST'])
@login_required
def swap_players():
    players = Player.get_players()
    if request.method == 'POST':
        # Fetch and validate input data
        new_player_id = request.form.get("new_player_id")
        player_id = request.form.get("player_id")

        if not new_player_id or not player_id:
            flash("Należy wypełnić oba pola. ", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        try:
            new_player_id = int(new_player_id)
            player_id = int(player_id)
        except ValueError:
            flash("Wybierz istniejących zawodników.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        # Fetch players from the database by ID
        new_player = Player.query.get(new_player_id)
        player = Player.query.get(player_id)

        if not new_player or not player:
            flash("Jeden lub obydwaj zawodnicy nie istnieją.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        # Validation logic for swapping players
        if player.team_id == new_player.team_id:
            flash("Wybrani zawodnicy należą do tej samej drużyny.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        if new_player.team_id is not None:
            flash("Nowy gracz ma już przypisaną drużynę.", "danger")
            return render_template("swap_players.html", user=current_user, players=players)

        try:
            Team.swap_players(player_id, new_player_id)
            flash("Wymiana zawodnika zakończona!", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash("An unexpected error occurred. Please try again.", "danger")

        return render_template("swap_players.html", user=current_user, players=players)

    return render_template("swap_players.html", user=current_user, players=players)

@views.route('/change-positions', methods=['GET','POST'])
@login_required
def change_positions():
    players = Player.get_players()
    if request.method == "POST":
       
        player_id = request.form.get("player_id")
        position = request.form.get("position")

        position = str(position)
        player_id = int(player_id)

        player = Player.query.get(player_id)
        if player.position == position:
            flash("Zawodnik już jest na tej pozycji", "danger")
            return render_template("change_positions.html", user = current_user, players =players)
        if player.team_id == None:
            flash("Ten zawodnik nie należy do żadnej drużyny", "danger")
            return render_template("change_positions.html", user = current_user, players =players)
        Player.change_position(player_id,position)
        flash("Zmiana pozycji zakończona! ", "success")
        return render_template("change_positions.html", user = current_user, players = players)
    return render_template("change_positions.html", user = current_user, players = players)