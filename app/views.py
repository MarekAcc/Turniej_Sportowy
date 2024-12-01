
from flask import Blueprint, render_template, request
from .models import Tournament,Team,Match
from . import db
from .services.tournament import create_tournament
from .services.player import create_player
from .services.team import create_team

views = Blueprint('views', __name__)

Username_trener = 'trener'
Password_trener = 'trener'
Username_admin = 'admin'
Password_admin = 'admin'

@views.route('/')
def home():
    # new_tournament = create_tournament('A Klasa','league', 'ended')
    return render_template("home.html")

@views.route('/create-tournament', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        tournamentName = request.form.get('tournamentName')
        tournamentType = request.form.get('tournamentType')
        create_tournament(tournamentName,tournamentType, 'ended')

    return render_template("create_tournament.html")

@views.route('/player')
def player():
    # new_player = create_player('Marco','Reus', 29, 'active')
    return "<h1>Dodano zawodnika</h1>"

@views.route('/team', methods=['GET','POST'])
def team():
    if request.method == 'POST':
        name = request.form.get('name')
        id_turnieju = request.form.get('tournament_id')
        create_team(name,int(id_turnieju))
        
    return render_template("register_team.html")


@views.route('/login', methods=['GET', 'POST'])
def login():
   
    if request.method == 'POST':
        Username = request.form.get('username')
        Password = request.form.get('password')
        if Username == Username_trener and Password == Password_trener:
            return render_template("trener_p.html")
        if Username == Username_admin and Password == Password_admin:
            return render_template("admin_p.html")
    return render_template("login.html")    
