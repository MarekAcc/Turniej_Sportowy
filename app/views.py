
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
- aktualizacja statystyk zawodnikow po meczach i mmatch eventach IGOR done - działa (przetestowane)
- Home Admina 
- Home trenera IGOR
- Wymiana zawodnikow w druzynie(trener)(zawodnik juz istniejący w bazie) IGOR done - działą(przetestowane)
- zmiana pozycji zawodnika(gdy jest czerwona kartka to nie moze byc 'field') IGOR done działa (przetestowane)
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


    try:
        # Tournament.remove_team_from_tournament('Tur1','Dru1')
        # Tournament.remove_team_from_tournament('Tur1','Dru3')
        # Tournament.remove_team_from_tournament('Tur1','')
        # Tournament.remove_team_from_tournament('Tur1','')
        # Tournament.remove_team_from_tournament('Tur1','')
        # Team.swap_players(int(1),int(5)) works
        Player.change_position(1, "field")
    except ValueError as e:
        print(f"Operacja nie powiodła się: {e}")

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
            tournaments = [tournament for tournament in all_tournaments if tournament.name.lower().startswith(query.lower())]
            
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
            teams = [team for team in all_teams if team.name.lower().startswith(query.lower())]
            
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
        referees = Referee.query.all()
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

@views.route('/manage-match', methods=['GET', 'POST'])
@login_required
def manage_match():
    match = Match.find_match_by_id(1)
    tournament = Tournament.find_tournament_by_id(match.tournament_id)
    homeTeam = Team.find_team_by_id(match.homeTeam_id)
    awayTeam= Team.find_team_by_id(match.awayTeam_id)

    return render_template('manage_match.html', tournament=tournament, homeTeam=homeTeam,awayTeam=awayTeam)

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