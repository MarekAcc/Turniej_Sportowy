from app.models import Tournament
from app import db

def create_tournament(name, type, status):
    if len(name) > 100:
        raise ValueError('Nazwa turnieju jest za długa!')
    
    if Tournament.query.filter_by(name=name).first():
        raise ValueError(f"Turniej o nazwie '{name}' już istnieje!")
        
    if type == 'Liga':
        type = 'league'
    elif type == 'Turniej pucharowy':
        type = 'playoff'
    else:
        raise ValueError('Błąd formatu!')
    
    if status == 'Aktywny':
        status = 'active'
    elif status == 'Zakończony':
        status = 'ended'
    elif status == 'Anulowany':
        status = 'canceled'
    else:
        raise ValueError('Błąd statusu!')
    
    new_tournament = Tournament(name=name, type=type, status=status)
    db.session.add(new_tournament)
    db.session.commit()

#Funkcja do zwracania n turniejow. (obsluga błędów, co gdy nie ma tylu funkcje sortowania(np alfabetycznie, albo inne opcje)
def get_tournaments(n):
    # TO DO
    print(n)
