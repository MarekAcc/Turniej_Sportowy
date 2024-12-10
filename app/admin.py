from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Tournament,Team,Match, Coach, Player, MatchEvent
from . import db
from .services.tournament import calculate_ranking
from .services.create import create_player, create_tournament, create_team, create_match, create_match_event
from flask_login import login_user, login_required, logout_user, current_user
from collections import defaultdict

admin = Blueprint('admin', __name__)

@admin.route('/home-admin')
@login_required
def home_admin():
    return render_template("home_admin.html", user=current_user)

# Dodawanie zawodnika do bazy
@admin.route('/new-player', methods=['GET', 'POST']) 
@login_required  # Wymagane zalogowanie użytkownika
def player_adder():
    # Sprawdzenie, czy metoda żądania to 'POST'
    if request.method == 'POST':
        # Pobranie danych z formularza
        firstName = request.form.get('firstName')  # Imię zawodnika
        lastName = request.form.get('lastName')    # Nazwisko zawodnika
        age = request.form.get('age')             # Wiek zawodnika

        # Walidacja wprowadzonych danych
        if not firstName or not lastName or not age:  # Sprawdzenie, czy wszystkie pola zostały uzupełnione
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('new_player.html', user=current_user)

        try:
            # Próba utworzenia zawodnika w bazie danych
            create_player(firstName, lastName, age)  # Funkcja dodająca zawodnika
            flash('Zawodnik został pomyślnie dodany!', 'success')
            return redirect(url_for('admin.home_admin', user=current_user))  # Przekierowanie na stronę główną admina
        except ValueError as e:
            # Obsługa błędu podczas tworzenia zawodnika
            flash(str(e), 'danger')
            return render_template('new_player.html', user=current_user)  # Ponowne załadowanie formularza

    # Renderowanie strony z formularzem, jeśli metoda żądania to 'GET'
    return render_template("new_player.html", user=current_user)

@admin.route('/delete-player', methods=['GET', 'POST'])
@login_required
def delete_player():
    all_players = Player.query.all()
    if request.method == 'POST':
        player_id = request.form.get('player_id')
        if not player_id:
            flash("Wybierz zawodnika!", 'danger')
            return render_template('delete_player.html',players=all_players)
        try:
            Player.delete_player(player_id)
            flash('Pomyślnie wyrejestrowano zawodnika!', 'success')
            return redirect(url_for('admin.home_admin'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('delete_player.html', players=all_players)

    return render_template('delete_player.html',players=all_players)

# Dodawanie nowej drużyny
@admin.route('/team-adder', methods=['GET', 'POST'])
@login_required
def team_adder():
    # Pobranie listy zawodników bez przypisanej drużyny
    players = Player.get_players_without_team()
    coaches = Coach.query.filter(Coach.firstName != 'ADMIN').all()

    # Sprawdzenie, czy metoda żądania to 'POST'
    if request.method == 'POST':
        name = request.form.get('name')  # Pobranie nazwy drużyny z formularza
        team_players = []  # Lista zawodników w drużynie

        # Pobranie trenera druzyny z formularza
        coach_id = request.form.get('coach_id')
        try:
            coach = Coach.find_coach_by_id(coach_id)
        except ValueError as e:
            flash(str(e), 'danger') 
            return render_template("register_team.html", user=current_user, players=players, coaches=coaches)

        # Pobranie danych zawodników z formularza
        for i in range(1, 3):
            player_id = request.form.get(f'player_id_{i}')
            if not player_id:
                flash('Wszyscy zawodnicy są wymagani!', 'danger')
                return render_template("register_team.html", user=current_user, players=players, coaches=coaches)
            player = Player.find_player_by_id(player_id)
            team_players.append(player)

        # Sprawdzenie, czy nazwa drużyny została podana
        if not name:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template("register_team.html", user=current_user, players=players, coaches=coaches)

        try:
            # Próba utworzenia drużyny
            create_team(name, team_players,coach)
            flash('Drużyna została pomyślnie zarejestrowana!', 'success')
            return redirect(url_for('admin.home_admin', user=current_user))
        except ValueError as e:
            # Obsługa błędów podczas tworzenia drużyny
            flash(str(e), 'danger') 
            return render_template("register_team.html", user=current_user, players=players, coaches=coaches)

    # Renderowanie strony z formularzem, jeśli metoda żądania to 'GET'
    return render_template("register_team.html", user=current_user, players=players, coaches=coaches)

@admin.route('/delete-team', methods=['GET', 'POST'])
@login_required
def delete_team():
    all_teams = Team.query.all()
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        if not team_id:
            flash("Wybierz druzyne!", 'danger')
            return render_template('delete_team.html',teams=all_teams)
        
        try:
            Team.delete_team(team_id)
            flash('Pomyślnie wyrejestrowano druzyne!', 'success')
            return redirect(url_for('admin.home_admin'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('delete_team.html',teams=all_teams)

    return render_template('delete_team.html',teams=all_teams)

@admin.route('/create-tournament', methods=['GET', 'POST'])
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
            new_tournament = create_tournament(tournamentName,tournamentType, 'planned')
            flash('Turniej został pomyślnie dodany!', 'success')
            return redirect(url_for('admin.teams_to_tournament_adder', numTeams=numTeams, tournament_id=new_tournament.id))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("create_tournament.html", user=current_user)
    return render_template("create_tournament.html", user=current_user)

@admin.route('/add-teams-to-tournament', methods=['GET', 'POST'])
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
                return redirect(url_for('admin.tournament_adder'))
            except ValueError as e:
                flash(str(e), 'danger')

        else:
            flash(
                f'Wszystkie {num_teams} drużyny muszą zostać dodane!', 'danger')

    # Tworzymy dynamiczne formularze do dodania drużyn
    return render_template("add_teams_to_tournament.html", user=current_user, num_teams=num_teams, teams=all_teams)

@admin.route('/choose-tournament-to-manage', methods=['GET', 'POST'])
@login_required
def choose_tournament_to_manage():
    all_tournaments = Tournament.query.all()
    if request.method == 'POST':
        tournament_id = request.form.get('tournament_id')
        if not tournament_id:
            flash(f'Wybierz druzyne!', 'warning')
            return render_template('choose_tournament_to_manage.html',tournaments=all_tournaments)
        else:
            return redirect(url_for('admin.manage_tournament', tournament_id=tournament_id))

    return render_template('choose_tournament_to_manage.html',tournaments=all_tournaments)

@admin.route('/manage-tournament', methods=['GET', 'POST'])
@login_required
def manage_tournament():
    tournament_id = request.args.get('tournament_id', type=int)
    tournament = Tournament.find_tournament_by_id(tournament_id)

    if request.method == 'POST':
        print("ajaja")

    return render_template('manage_tournament.html',tournament=tournament)

@admin.route('/end-tournament/<int:tournament_id>', methods=['POST'])
@login_required
def end_tournament(tournament_id):
    # Obsługa zakończenia turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)
    try:
        Tournament.finish(tournament_id)
        flash(f'Zakończono turniej {tournament.name}!', 'success')
        return redirect(url_for('admin.home_admin'))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.home_admin'))

@admin.route('/cancel-tournament/<int:tournament_id>', methods=['POST'])
@login_required
def cancel_tournament(tournament_id):
    # Obsługa przerwania turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)
    try:
        Tournament.cancel(tournament_id)
        flash(f'Przerwano turniej {tournament.name}!', 'success')
        return redirect(url_for('admin.home_admin'))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.home_admin'))
    
@admin.route('/delete-tournament/<int:tournament_id>', methods=['POST'])
@login_required
def delete_tournament(tournament_id):   
    # Obsługa usuniecia turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)
    try:
        Tournament.delete(tournament_id)
        flash(f'Usunięto turniej {tournament.name}!', 'success')
        return redirect(url_for('admin.home_admin'))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.home_admin'))
    
@admin.route('/draw-next-round/<int:tournament_id>', methods=['POST'])
@login_required
def draw_next_round(tournament_id):
    # Obsługa losowania kolejnej rundy
    tournament = Tournament.find_tournament_by_id(tournament_id)
    try:
        Tournament.generate_next_round(tournament)
        return redirect(url_for('admin.home_admin'))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.home_admin'))
    
@admin.route('/choose-match-to-manage', methods=['GET', 'POST'])
@login_required
def choose_match_to_manage():
    all_matches = Match.query.all()
    if request.method == 'POST':
        match_id = request.form.get('match_id')
        match = Match.find_match_by_id(match_id)
        if match.status != 'planned':
            flash('Nie mozna edytować zakonczonego meczu!', 'warning')
            return render_template('choose_match_to_manage.html',matches=all_matches)
        
        return redirect(url_for('admin.manage_match', match_id=match_id))

    return render_template('choose_match_to_manage.html',matches=all_matches)

@admin.route('/manage-match', methods=['GET', 'POST'])
@login_required
def manage_match():
    match_id = request.args.get('match_id', type=int)
    match = Match.find_match_by_id(match_id)

    tournament = Tournament.find_tournament_by_id(match.tournament_id)
    homeTeam = Team.find_team_by_id(match.homeTeam_id)
    awayTeam= Team.find_team_by_id(match.awayTeam_id)

    if request.method == 'POST':
        scoreHome = request.form.get('scoreHome')
        scoreAway = request.form.get('scoreAway')

        match.scoreHome = scoreHome
        match.scoreAway = scoreAway
        match.status = 'ended'

        players_home = homeTeam.players
        players_away = awayTeam.players

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

        db.session.commit()
        flash('Dodano wynik meczu!', 'success')
        return redirect(url_for('admin.match_event_adder'))

    return render_template('manage_match.html',tournament=tournament,homeTeam=homeTeam,awayTeam=awayTeam)

@admin.route('/match-event-adder', methods=['GET', 'POST'])
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
