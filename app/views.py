
from flask import Blueprint
from .models import Tournament,Team,Match
from . import db

views = Blueprint('views', __name__)


@views.route('/')
def home():
    tournament = Tournament(name="Champions League", type="league", status="active")
    db.session.add(tournament)
    db.session.commit()

    return "<h1>Dodano druzyne</h1>"