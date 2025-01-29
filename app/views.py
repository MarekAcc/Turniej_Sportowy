
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Tournament, Team, Match, Coach, Player, MatchEvent, Referee
from . import db
from .services.tournament import calculate_ranking
from .services.create import create_player, create_tournament, create_team, create_match, create_match_event
from flask_login import login_user, login_required, logout_user, current_user
from collections import defaultdict
from .admin import admin_required
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

    # Jeśli zapytanie jest obecne, filtrujemy turnieje
    if query:
        try:
            # Pobieramy wszystkie turnieje
            all_tournaments = Tournament.get_tournaments()

            # Filtrujemy turnieje zaczynające się na podany ciąg znaków (case-insensitive)
            tournaments = [tournament for tournament in all_tournaments if tournament.name.lower(
            ).startswith(query.lower())]

            # Jeśli lista turniejów jest pusta, wyświetlamy komunikat
            if not tournaments:
                flash("Nie znaleziono turniejów pasujących do zapytania.", "warning")
        except ValueError as e:
            # Obsługa błędów, np. problem z bazą danych
            flash(str(e), "danger")
            tournaments = []
    else:
        # Jeśli brak zapytania, pobieramy wszystkie turnieje
        tournaments = Tournament.get_tournaments()

    return render_template("tournaments.html", tournaments=tournaments, user=current_user)


@views.route('/teams')
def teams():
    query = request.args.get('query')

    # Jeśli zapytanie jest obecne, filtrujemy drużyny
    if query:
        try:
            # Pobieramy wszystkie drużyny
            all_teams = Team.get_teams()

            # Filtrujemy drużyny zaczynające się na podany ciąg znaków (case-insensitive)
            teams = [team for team in all_teams if team.name.lower(
            ).startswith(query.lower())]

            # Jeśli lista drużyn jest pusta, wyświetlamy komunikat
            if not teams:
                flash("Nie znaleziono drużyn pasujących do zapytania.", "warning")
        except ValueError as e:
            # Obsługa błędów, np. problem z bazą danych
            flash(str(e), "danger")
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
            parts = query.split(' ', 1)
            if len(parts) == 2:
                first_name, last_name = parts
                refs = Referee.query.filter(
                    (Referee.firstName.ilike(f"%{first_name}%")) &
                    (Referee.lastName.ilike(f"%{last_name}%"))
                ).all()
            else:
                refs = Referee.query.filter(
                    (Referee.firstName.ilike(f"%{query}%")) |
                    (Referee.lastName.ilike(f"%{query}%"))
                ).all()
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

    return render_template("referee_details.html", referee=referee, user=current_user, matches=matches)

# detale dla stron --------------------------------------------------------------------------------------------------------


@views.route('/tournament/<int:tournament_id>')
def tournament_details(tournament_id):
    tournament = Tournament.query.get(tournament_id)

    # Jeśli turniej nie istnieje, przekieruj z komunikatem
    if not tournament:
        flash("Turniej nie istnieje", "danger")
        return redirect(url_for('views.tournaments'))

    ranking = None
    rounds = None
    matches = []

    # Logika dla turniejów ligowych
    if tournament.type == 'league':
        try:
            # Obliczanie rankingu, obsługa wyjątku w przypadku braku meczów
            ranking = calculate_ranking(tournament_id)
        except ValueError as e:
            flash(str(e), "warning")  # Wyświetlenie komunikatu o błędzie
            ranking = {}

    # Logika dla turniejów typu playoff
    elif tournament.type == 'playoff':
        matches = Match.query.filter_by(tournament_id=tournament_id).all()
        if matches:
            # Grupujemy mecze według rundy
            rounds = {r: [m for m in matches if m.round == r]
                      for r in range(1, tournament.round + 1)}
        else:
            flash("Brak meczów w turnieju.", "warning")
            rounds = {}

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



@views.route('/choose-tournament-to-manage', methods=['GET', 'POST'])
@login_required
@admin_required
def choose_tournament_to_manage():
    all_tournaments = Tournament.query.all()

    if request.method == 'POST':
        tournament_id = request.form.get('tournament_id')
        return redirect(url_for('views.manage_tournament', tournament_id=tournament_id))

    return render_template('choose_tournament_to_manage.html', tournaments=all_tournaments)


@views.route('/manage-tournament', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tournament():
    tournament_id = request.args.get('tournament_id', type=int)
    tournament = Tournament.find_tournament_by_id(tournament_id)

    if request.method == 'POST':
        print("ajaja")

    return render_template('manage_tournament.html', tournament=tournament)


@views.route('/cancel-tournament/<int:tournament_id>', methods=['POST'])
@login_required
@admin_required
def cancel_tournament(tournament_id):
    # Obsługa przerwania turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)
    # Tournament.cancel(tournament.name)
    flash(f'Przerwano turniej {tournament.name}!', 'success')
    return redirect(url_for('views.home_admin'))


@views.route('/end-tournament/<int:tournament_id>', methods=['POST'])
@login_required
@admin_required
def end_tournament(tournament_id):
    # Obsługa zakończenia turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)

    flash(f'Zakończono turniej {tournament.name}!', 'success')
    return redirect(url_for('views.home_admin'))


@views.route('/delete-tournament/<int:tournament_id>', methods=['POST'])
@login_required
@admin_required
def delete_tournament(tournament_id):
    Tournament.delete(tournament_id)
    return redirect(url_for('views.home_admin'))


@views.route('/draw-next-round/<int:tournament_id>', methods=['POST'])
@login_required
@admin_required
def draw_next_round(tournament_id):
    # Obsługa losowania kolejnej rundy
    tournament = Tournament.find_tournament_by_id(tournament_id)
    pass

@views.route('/delete-player', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_player():
    all_players = Player.query.all()
    if request.method == 'POST':
        player_id = request.form.get('player_id')
        try:
            Player.delete_player(player_id)
            flash('Pomyślnie wyrejestrowano zawodnika!', 'success')
            return redirect(url_for('views.home_admin'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('delete_player.html', players=all_players)

    return render_template('delete_player.html', players=all_players)


@views.route('/delete-team', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_team():
    all_teams = Team.query.all()
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        try:
            Team.delete_team(team_id)
            flash('Pomyślnie wyrejestrowano druzyne!', 'success')
            return redirect(url_for('views.home_admin'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('delete_team.html', teams=all_teams)

    return render_template('delete_team.html', teams=all_teams)

@views.route('/match-adder', methods=['GET', 'POST'])
@login_required
@admin_required
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


@views.route('/manage-match', methods=['GET', 'POST'])
@admin_required
@login_required
def manage_match():
    match_id = request.args.get('match_id', type=int)
    match = Match.find_match_by_id(match_id)

    if not match.referee:
        flash('Ten mecz nie ma przypianego sędziego! Nie moze się odbyć!','warning')

    tournament = Tournament.find_tournament_by_id(match.tournament_id)

    homeTeam = Team.find_team_by_id(match.homeTeam_id)
    awayTeam = Team.find_team_by_id(match.awayTeam_id)

    if request.method == 'POST':
        scoreHome = request.form.get('scoreHome')
        scoreAway = request.form.get('scoreAway')

        match.scoreHome = scoreHome
        match.scoreAway = scoreAway
        match.status = 'ended'

        # Aktualizacja punktów dla drużyn w turnieju ligowym

        if match.tournament.type == 'league':
            home_team = match.home_team
            away_team = match.away_team

            if not home_team or not away_team:
                raise ValueError(
                    "Nie można znaleźć drużyn przypisanych do meczu.")

            if scoreHome > scoreAway:
                home_team.score += 3  # Gospodarz wygrywa

            elif scoreHome < scoreAway:
                away_team.score += 3  # Goście wygrywają

            else:
                home_team.score += 1  # Remis
                away_team.score += 1  # Remis

        db.session.commit()
        flash('Dodano wynik meczu!', 'success')
        return redirect(url_for('admin.home_admin'))

    return render_template('manage_match.html', tournament=tournament, homeTeam=homeTeam, awayTeam=awayTeam, user=current_user)


@views.route('/match-event-adder', methods=['GET', 'POST'])
@admin_required
@login_required
def match_event_adder():
    matches = Match.get_matches()
    players = Player.get_players()
    if request.method == "POST":
        match_id = int(request.form.get('match_id'))
        player_id = int(request.form.get('player_id'))
        eventType = request.form.get('eventType')

        match = next((m for m in matches if m.id == match_id), None)
        player = next((p for p in players if p.id == player_id), None)

        if not match or not player:
            flash("Nie znaleziono meczu lub gracza.", "error")
            return render_template("match-event-adder.html", user=current_user, matches=matches, players=players)
        # Sprawdź, czy gracz należy do jednej z drużyn w meczu
        if player.team_id not in {match.homeTeam_id, match.awayTeam_id}:
            flash("Wybrany gracz nie brał udziału w tym meczu.", "danger")
            return render_template("match-event-adder.html", user=current_user, matches=matches, players=players)
        # Utwórz event, jeśli gracz uczestniczył w meczu
        try:
            create_match_event(eventType, match_id, player_id)
            flash("Pomyślnie dodano match-event!", "success")
        except Exception as e:
            flash(f"Nie udało się dodać match-event: {e}", "danger")

        return render_template("match-event-adder.html", user=current_user, matches=matches, players=players)

    # Obsługa metody GET
    return render_template("match-event-adder.html", user=current_user, matches=matches, players=players)


@views.route('/match-event-detail/<int:match_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def match_event_detail(match_id):
    match = Match.query.get(match_id)
    if not match:
        flash("Mecz nie istnieje.", "danger")
        return redirect(url_for('views.match_event_adder'))

    if request.method == "POST":
        home_goals_sum = 0
        away_goals_sum = 0

        # Zliczanie goli dla każdej drużyny
        for player in match.home_team.players:
            goals = request.form.get(f"goals_{player.id}", "0")
            goals = int(goals) if goals.isdigit() else 0
            home_goals_sum += goals

        for player in match.away_team.players:
            goals = request.form.get(f"goals_{player.id}", "0")
            goals = int(goals) if goals.isdigit() else 0
            away_goals_sum += goals

        # Walidacja sumy goli
        if home_goals_sum != match.scoreHome:
            flash(
                f"Nieprawidłowa suma goli dla drużyny gospodarzy. Powinna wynosić {match.scoreHome}, a wynosi {home_goals_sum}.", "danger")
            return render_template("match-event-detail.html", user=current_user, match=match)

        if away_goals_sum != match.scoreAway:
            flash(
                f"Nieprawidłowa suma goli dla drużyny gości. Powinna wynosić {match.scoreAway}, a wynosi {away_goals_sum}.", "danger")
            return render_template("match-event-detail.html", user=current_user, match=match)

        # Jeśli walidacja przeszła, zapisz dane
        for player in match.home_team.players + match.away_team.players:
            goals = request.form.get(f"goals_{player.id}", "0")
            goals = int(goals) if goals.isdigit() else 0

            red_card = request.form.get(f"red_card_{player.id}", False)

            if goals > 0:
                for _ in range(goals):
                    try:
                        create_match_event("goal", match_id, player.id)
                    except ValueError:
                        flash("Błąd create_match_event!", "danger")
                        return render_template("match-event-detail.html", user=current_user, match=match)

            if red_card:
                create_match_event("redCard", match_id, player.id)


        match.status = 'managed'
        db.session.commit()
        flash("Wydarzenia zostały zapisane!", "success")
        return redirect(url_for('admin.manage_tournament', tournament_id=match.tournament_id))

    return render_template("match-event-detail.html", user=current_user, match=match)
