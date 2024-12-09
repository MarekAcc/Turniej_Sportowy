
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Tournament,Team,Match, Coach, Player
from . import db
from .services.create import create_player, create_tournament, create_team, create_match, create_match_event
from flask_login import login_user, login_required, logout_user, current_user

views = Blueprint('views', __name__)

"""
TO DO:
- ogolny front Kibica
- ciąglosc tworzenia Turnieju(dodawanie druzyn po) ZROBIONE
- status tworzenia turnieju(zeby nie byl od razu active) MATI
- aktualizacja statystyk zawodnikow po meczach i mmatch eventach IGOR
- Home Admina 
- Home trenera IGOR
- Wymiana zawodnikow w druzynie(trener)(zawodnik juz istniejący w bazie) IGOR
- zmiana pozycji zawodnika(gdy jest czerwona kartka to nie moze byc 'field') IGOR
- harmonogram i sędzia MAREK
- punktacja, tabela, drabinka MAREK
"""
""" 
Punkt widzenia kibica:

W górnym pasku ma być : Strona głowna, Login, Zarejestruj się

Na stronie będie docelowo 5 przyciskow: Turnieje, Druzyny, Zawodnicy, Trenerzy, Sędziowie

Po kliknięciu w któryś z nich wyświetli się kilka danych z bazy, ale najwazniejsze
bedzie pole do wyszukania, gdzie uzytkownik będzie mogl wyszukac turniej, druzyne itp. 
w zaleznosci w jaką stronę wszedł.

TURNIEJ - Wyswietli się tabela ligowa, lub drabinka(playoff), a pod spodem mecze rozegrane i zaplanowane.

Uzytkownik bedzie mogl kliknac sobie w kazda druzyne i wyswietli mu sie strona druzyny(taka sama jak gdy bedzie
szukal sobie druznyn niezaleznie od turnieju lub mozemy to bardziej zmodyfikowac pod turniej tzn. oprocz ogolnych
danych druzyny dodac na gorze mecze rozgrywane w turnieju z ktorego uzytkownik kliknal w druzyne)

Uzytkownik bedzie rowniez mogl kliknac sobie w mecz i wyswietlą mu sie informacje o tym meczu oraz wszystkie MatchEventy

DRUŻYNA- gdy uzytkownik wyszuka jakas druzyne to wyswietli mu sie profil tej druzyny (zawodnicy, trener, statystyki, mecze)

Z poziomu druzyny uzytkownik bedzie mogl sobie kliknac na zawodnika, trenera, mecz, rozgrywany turniej i obejrzec szczegóły. 

ZAWODNIK - profil zawodnika bedzie zawieral jego statystyki(mecze, gole, kary), jego druzyne i byc moze cos jeszcze

TRENER - dane i druzyna

SĘDZIA - dane, statystyki i mecze(zaplanowane i rozergrane).

"""
# Strona główna, która widzi kazdy niezalogowany uzytkownik, czyli KIBIC
@views.route('/')
def home():


    # try:
    #     team = Team.find_team('')
    #     tournament = Tournament.find_tournament_by_id(team.tournament_id)
    #     Tournament.remove_team_from_tournament(tournament.name,team.name)
    # except ValueError as e:
    #     print(f"Operacja nie powiodła się: {e}")

    return render_template("home.html", user=current_user)


@views.route('/home-admin')
@login_required
def home_admin():
    tournament = Tournament.find_tournament('A Klasa')
    teams = Tournament.get_teams(tournament.id)

    return render_template("home_admin.html", user=current_user, tournament=tournament, teams=teams)
    
@views.route('/show-tournament', methods=['GET', 'POST'])
@login_required
def show_tournament():
    tournament = Tournament.find_tournament_by_id(30)
    teams = Tournament.get_teams(tournament.id)
    return render_template("tournament_admin.html", user=current_user, tournament=tournament, teams=teams)


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
            new_tournament = create_tournament(tournamentName,tournamentType, 'planned')
            flash('Turniej został pomyślnie dodany!', 'success')
            return redirect(url_for('views.teams_to_tournament_adder',numTeams=numTeams,tournament_id=new_tournament.id))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("create_tournament.html", user=current_user)
    return render_template("create_tournament.html", user=current_user)

@views.route('/add-teams-to-tournament', methods=['GET', 'POST'])
@login_required
def teams_to_tournament_adder():
    num_teams = request.args.get('numTeams', type=int)  # Pobieranie liczby drużyn
    tournament_id = request.args.get('tournament_id', type=int)  # Pobieranie ID turnieju

    # Pobieramy obiekt turnieju
    tournament = Tournament.find_tournament_by_id(tournament_id)

    # Pobieramy wszystkie druzyny
    all_teams = Team.get_teams_without_tournament()

    if request.method == 'POST':
        teams = []
        for i in range(num_teams):
            team_id = request.form.get(f'team_{i}')  # Pobieramy ID drużyny z formularza
            if team_id:
                team = Team.query.get(team_id) # Pobieramy drużynę po ID
                teams.append(team)
        
        if len(teams) == num_teams:
            try:
                Tournament.add_teams(tournament.name,teams)
                Tournament.generate_matches(tournament)
                flash('Drużyny zostały dodane pomyślnie!', 'success')
                return redirect(url_for('views.tournament_adder'))  # Przekierowanie do strony głównej lub innej
            except ValueError as e:
                flash(str(e), 'danger')

        else:
            flash(f'Wszystkie {num_teams} drużyny muszą zostać dodane!', 'danger')

    # Tworzymy dynamiczne formularze do dodania drużyn
    return render_template("add_teams_to_tournament.html", user=current_user, num_teams=num_teams,teams=all_teams)

@views.route('/choose-tournament-to-manage', methods=['GET', 'POST'])
@login_required
def choose_tournament_to_manage():
    all_tournaments = Tournament.query.all()
    if request.method == 'POST':
        tournament_id = request.form.get('tournament_id')
        return redirect(url_for('views.manage_tournament', tournament_id=tournament_id))

    return render_template('choose_tournament_to_manage.html',tournaments=all_tournaments)

@views.route('/manage-tournament', methods=['GET', 'POST'])
@login_required
def manage_tournament():
    tournament_id = request.args.get('tournament_id', type=int)
    tournament = Tournament.find_tournament_by_id(tournament_id)

    if request.method == 'POST':
        print("ajaja")

    return render_template('manage_tournament.html',tournament=tournament)

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

@views.route('/draw-next-round/<int:tournament_id>', methods=['POST'])
@login_required
def draw_next_round(tournament_id):
    # Obsługa losowania kolejnej rundy
    tournament = Tournament.find_tournament_by_id(tournament_id)
    pass

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
            create_player(firstName,lastName,age)
            flash('Zawodnik został pomyślnie dodany!', 'success')
            return render_template('new_player.html', user=current_user)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('new_player.html', user=current_user)

    return render_template("new_player.html", user=current_user)

@views.route('/team-adder', methods=['GET','POST'])
@login_required
def team_adder():
    # Pobierz zawodnikow bez druzyny
    players = Player.get_players_without_team()

    if request.method == 'POST':
        name = request.form.get('name')
        team_players = []
        # Pobieranie zawodnikow z formularza
        for i in range(1,3):
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
            create_team(name,team_players)
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

    return render_template('choose_match_to_manage.html',matches=all_matches)

@views.route('/manage-match', methods=['GET', 'POST'])
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

        # db.session.commit()
        flash('Dodano wynik meczu!', 'success')
        return redirect(url_for('views.home_admin'))

    return render_template('manage_match.html',tournament=tournament,homeTeam=homeTeam,awayTeam=awayTeam)

@views.route('/match-event-adder', methods=['GET','POST'])
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
