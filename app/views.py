
from flask import Blueprint, render_template, request, flash
from .models import Tournament,Team,Match, Coach, Player
from . import db
from .services.create import create_player, create_tournament, create_team
from flask_login import login_user, login_required, logout_user, current_user

views = Blueprint('views', __name__)

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

    players = Player.get_players(10)
    for player in players:
        print(player.firstName)
    return render_template("home.html", user=current_user)

@views.route('/create-tournament', methods=['GET', 'POST'])
@login_required
def tournament_adder():
    if request.method == 'POST':
        tournamentName = request.form.get('tournamentName')
        tournamentType = request.form.get('tournamentType')
        tournamentStatus = request.form.get('tournamentStatus')

        if not tournamentName or not tournamentType or not tournamentStatus:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('create_tournament.html', user=current_user)
        try:  
            create_tournament(tournamentName,tournamentType, tournamentStatus)
            flash('Turniej został pomyślnie dodany!', 'success')
            return render_template("create_tournament.html", user=current_user)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("create_tournament.html", user=current_user)
    return render_template("create_tournament.html", user=current_user)

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
    if request.method == 'POST':
        name = request.form.get('name')
        tournament = request.form.get('tournament')
        players = []
        for i in range(1,17):
            player = request.form.get(f'player{i}')
            if not player:
                flash('Wszyscy zawodnicy są wymagani!', 'danger')
                return render_template('register_team.html', user=current_user)
            players.append(player)

        if not name or not tournament:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('register_team.html', user=current_user)
        try:
            create_team(name,tournament,players)
            flash('Druzyna została pomyślnie zarejestrowana!', 'success')
            return render_template("register_team.html", user=current_user)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("register_team.html", user=current_user)
        
    return render_template("register_team.html", user=current_user)
  
@views.route('/match-adder', methods=['GET','POST'])
@login_required
def match_adder():
    print("TODO")

@views.route('/match-event-adder', methods=['GET','POST'])
@login_required
def match_event_adder():
    print("TODO")