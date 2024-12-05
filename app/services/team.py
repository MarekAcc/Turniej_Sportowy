from app.models import Team, Tournament, Player
from app import db

def register_team(name, tournament_name, players):
    if len(name) > 100:
        raise ValueError('Nazwa druzyny jest za długa!')

    if Team.query.filter_by(name=name).first():
        raise ValueError(f"Druzyna o nazwie '{name}' już istnieje!")
    
    tournament = Tournament.query.filter_by(name=tournament_name).first()
    if not tournament:
        raise ValueError(f"Turniej o nazwie '{tournament_name}' NIE ISTNIEJE!")
    
    new_team = Team(name=name, tournament_id=tournament.id)
    db.session.add(new_team)
    db.session.commit()

    for p in players:
        first_name, last_name = p.split(" ",1)
        player = Player.query.filter_by(firstName=first_name, lastName=last_name).first()
        if not player:
            raise ValueError(f"Zawodnik '{first_name} {last_name}' NIE ISTNIEJE!")
        if player.team_id != None:
            raise ValueError(f"Zawodnik '{first_name} {last_name}' jest juz przypisany do innej druzyny!")
        player.team_id = new_team.id
        
    db.session.commit()

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
