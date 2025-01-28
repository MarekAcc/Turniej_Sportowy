
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

    return render_template("referee_details.html", referee=referee, user=current_user, matches=matches)

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


@views.route('/create-tournament', methods=['GET', 'POST'])
@login_required
def tournament_adder():
    if request.method == 'POST':
        tournamentName = request.form.get('tournamentName')
        tournamentType = request.form.get('tournamentType')
        numTeams = request.form.get('numTeams')  # Liczba drużyn
        numTeams = int(numTeams)
        if not tournamentName or not tournamentType or not numTeams or numTeams < 2:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('create_tournament.html', user=current_user)

        if tournamentType == 'Turniej pucharowy' and (numTeams <= 0 or (numTeams & (numTeams - 1)) != 0):
            flash('Ilość druzyn w turnieju PLAY-OFF musi być potęgą liczby 2!', 'danger')
            return render_template('create_tournament.html', user=current_user)

        try:
            new_tournament = create_tournament(
                tournamentName, tournamentType, 'planned')
            flash('Turniej został pomyślnie dodany!', 'success')
            return redirect(url_for('views.teams_to_tournament_adder', numTeams=numTeams, tournament_id=new_tournament.id))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("create_tournament.html", user=current_user)
    return render_template("create_tournament.html", user=current_user)


@views.route('/add-teams-to-tournament', methods=['GET', 'POST'])
@login_required
def teams_to_tournament_adder():
    # Pobieranie liczby drużyn
    num_teams = request.args.get('numTeams', type=int)
    tournament_id = request.args.get(
        'tournament_id', type=int)  # Pobieranie ID turnieju

    # Pobieramy obiekt turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)

    # Pobieramy wszystkie druzyny
    all_teams = Team.get_teams_without_tournament()

    if request.method == 'POST':
        teams = []
        for i in range(num_teams):
            # Pobieramy ID drużyny z formularza
            team_id = request.form.get(f'team_{i}')
            if team_id:
                team = Team.query.get(team_id)  # Pobieramy drużynę po ID
                teams.append(team)

        if len(teams) == num_teams:
            try:
                Tournament.add_teams(tournament.name, teams)
                Tournament.generate_matches(tournament)
                flash('Drużyny zostały dodane pomyślnie!', 'success')
                # Przekierowanie do strony głównej lub innej
                return redirect(url_for('views.tournament_adder'))
            except ValueError as e:
                flash(str(e), 'danger')

        else:
            flash(
                f'Wszystkie {num_teams} drużyny muszą zostać dodane!', 'danger')

    # Tworzymy dynamiczne formularze do dodania drużyn
    return render_template("add_teams_to_tournament.html", user=current_user, num_teams=num_teams, teams=all_teams)


@views.route('/choose-tournament-to-manage', methods=['GET', 'POST'])
@login_required
def choose_tournament_to_manage():
    all_tournaments = Tournament.query.all()

    if request.method == 'POST':
        tournament_id = request.form.get('tournament_id')
        return redirect(url_for('views.manage_tournament', tournament_id=tournament_id))

    return render_template('choose_tournament_to_manage.html', tournaments=all_tournaments)


@views.route('/manage-tournament', methods=['GET', 'POST'])
@login_required
def manage_tournament():
    tournament_id = request.args.get('tournament_id', type=int)
    tournament = Tournament.find_tournament_by_id(tournament_id)

    if request.method == 'POST':
        print("ajaja")

    return render_template('manage_tournament.html', tournament=tournament)


@views.route('/cancel-tournament/<int:tournament_id>', methods=['POST'])
@login_required
def cancel_tournament(tournament_id):
    # Obsługa przerwania turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)
    # Tournament.cancel(tournament.name)
    flash(f'Przerwano turniej {tournament.name}!', 'success')
    return redirect(url_for('views.home_admin'))


@views.route('/end-tournament/<int:tournament_id>', methods=['POST'])
@login_required
def end_tournament(tournament_id):
    # Obsługa zakończenia turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)

    flash(f'Zakończono turniej {tournament.name}!', 'success')
    return redirect(url_for('views.home_admin'))


@views.route('/delete-tournament/<int:tournament_id>', methods=['POST'])
@login_required
def delete_tournament(tournament_id):
    Tournament.delete(tournament_id)
    return redirect(url_for('views.home_admin'))


@views.route('/draw-next-round/<int:tournament_id>', methods=['POST'])
@login_required
def draw_next_round(tournament_id):
    # Obsługa losowania kolejnej rundy
    tournament = Tournament.find_tournament_by_id(tournament_id)
    pass


# Dodawanie zawodnika do bazy
@views.route('/new-player', methods=['GET', 'POST'])
@login_required
def player_adder():
    if request.method == 'POST':
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        age = request.form.get('age')

        if not firstName or not lastName or not age:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('new_player.html', user=current_user)
        try:
            create_player(firstName, lastName, age)
            flash('Zawodnik został pomyślnie dodany!', 'success')
            return redirect(url_for('views.home_admin', user=current_user))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('new_player.html', user=current_user)

    return render_template("new_player.html", user=current_user)


@views.route('/delete-player', methods=['GET', 'POST'])
@login_required
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


@views.route('/team-adder', methods=['GET', 'POST'])
@login_required
def team_adder():
    # Pobierz zawodnikow bez druzyny
    players = Player.get_players_without_team()

    if request.method == 'POST':
        name = request.form.get('name')
        team_players = []
        # Pobieranie zawodnikow z formularza
        for i in range(1, 3):
            player_id = request.form.get(f'player_id_{i}')
            if not player_id:
                flash('Wszyscy zawodnicy są wymagani!', 'danger')
                return render_template("register_team.html", user=current_user, players=players)
            player = Player.find_player_by_id(player_id)
            team_players.append(player)

        if not name:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template("register_team.html", user=current_user, players=players)
        try:
            create_team(name, team_players)
            flash('Druzyna została pomyślnie zarejestrowana!', 'success')
            return render_template("register_team.html", user=current_user, players=players)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("register_team.html", user=current_user, players=players)

    return render_template("register_team.html", user=current_user, players=players)


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


@views.route('/choose-match-to-manage', methods=['GET', 'POST'])
@login_required
def choose_match_to_manage():

    all_matches = Match.query.all()

    if request.method == 'POST':
        match_id = request.form.get('match_id')
        return redirect(url_for('views.manage_match', match_id=match_id))

    return render_template('choose_match_to_manage.html', matches=all_matches)


@views.route('/manage-match', methods=['GET', 'POST'])
@login_required
def manage_match():
    match_id = request.args.get('match_id', type=int)
    match = Match.find_match_by_id(match_id)

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
        return redirect(url_for('views.home_admin'))

    return render_template('manage_match.html', tournament=tournament, homeTeam=homeTeam, awayTeam=awayTeam, user=current_user)


@views.route('/match-event-adder', methods=['GET', 'POST'])
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
                    create_match_event("goal", match_id, player.id)

            if red_card:
                create_match_event("redCard", match_id, player.id)

        flash("Wydarzenia zostały zapisane!", "success")
        return redirect(url_for('views.match_event_adder'))

    return render_template("match-event-detail.html", user=current_user, match=match)

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
