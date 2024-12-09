from app.models import Team
from app import db

def delete_team(name):
    team = Team.query.filter_by(name=name).first()
    if not team:
        raise ValueError(f"Druzyna o nazwie '{name}' NIE istnieje!")
    
    for player in team.players:
        player.team_id = None 

    # # Usuń powiązanego trenera (jeśli istnieje)
    # if team.teamCoach:
    #     db.session.delete(team.teamCoach)

    # # Usuń mecze, w których drużyna brała udział
    # for match in team.home_matches + team.away_matches:
    #     db.session.delete(match)
    
    db.session.delete(team)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Błąd podczas usuwania drużyny '{name}': {e}")
    

#Funkcja do zwracania n druzyn. (obsluga błędów, co gdy nie ma tylu coachow, funkcje sortowania(np alfabetycznie, albo inne opcje)
def get_teams(n):
    # TO DO
    print(n)
