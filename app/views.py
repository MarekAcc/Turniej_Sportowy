
from flask import Blueprint, render_template, request, flash
from .models import Tournament,Team,Match, Coach
from . import db
from .services.tournament import create_tournament
from .services.player import new_player
from .services.team import register_team, delete_team
from flask_login import login_user, login_required, logout_user, current_user

views = Blueprint('views', __name__)

@views.route('/')
def home():
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
            new_player(firstName,lastName,age)
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
            register_team(name,tournament,players)
            flash('Druzyna została pomyślnie zarejestrowana!', 'success')
            return render_template("register_team.html", user=current_user)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template("register_team.html", user=current_user)
        
    return render_template("register_team.html", user=current_user)
  