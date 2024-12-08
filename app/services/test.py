
from . import db

teams = db.get_teams()
teams.delete_team(1)