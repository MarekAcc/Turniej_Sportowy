from app.models import Tournament, Team, Match
from app import db


def calculate_ranking(tournmanet_id):
    tournament = Tournament.find_tournament_by_id(tournmanet_id)
    if not tournament:
        raise ValueError("Turniej nie istnieje.")

    if tournament.type != 'league':
        raise ValueError("Turniej musi być ligą.")

    # Pobieramy wszystkie mecze należące do turnieju
    matches = Match.query.filter_by(tournament_id=tournament.id).all()
    
    if not matches:
        raise ValueError("Brak meczów w turnieju.")

    # Wyznaczamy unikalne drużyny na podstawie meczów
    teams = set()
    for match in matches:
        teams.add(match.home_team)
        teams.add(match.away_team)

     # Inicjalizujemy słownik do przechowywania punktów
    ranking = {team: 0 for team in teams}

    # Liczymy punkty na podstawie wyników meczów
    for match in matches:
        if match.status != 'ended':
            continue  # Ignorujemy mecze, które się nie zakończyły

        if match.scoreHome > match.scoreAway:
            ranking[match.home_team] += 3  # 3 punkty za wygraną
        elif match.scoreHome < match.scoreAway:
            ranking[match.away_team] += 3  # 3 punkty za wygraną
        else:
            ranking[match.home_team] += 1  # 1 punkt za remis
            ranking[match.away_team] += 1

    # Sortowanie rankingu od największej liczby punktów
    sorted_ranking = dict(
        sorted(ranking.items(), key=lambda item: item[1], reverse=True))

    return sorted_ranking
