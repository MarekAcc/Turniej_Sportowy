from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Tournament, Team, Match, Coach, Player, MatchEvent, Referee
from . import db
from .services.tournament import calculate_ranking
from .services.create import create_player, create_tournament, create_team, create_match, create_match_event
from flask_login import login_user, login_required, logout_user, current_user
from collections import defaultdict

coach = Blueprint('coach', __name__)

@coach.route('/home-coach')
@login_required
def home_coach():
    coach_team = current_user.team
    players = Team.get_players(coach_team, coach_team.id)
    return render_template("coach_dashboard.html", user=current_user, players=players)

# --------------COACH OD IGORA--------------------


@coach.route('/swap-players', methods=['GET', 'POST'])
@login_required
def swap_players():
    # Pobierz wszystkich zawodników
    coach_team = current_user.team
    team_players = Team.get_players(coach_team, coach_team.id)
    players = Player.get_players_without_team()

    if request.method == 'POST':
        # Pobierz dane z formularza
        new_player_id = request.form.get("new_player_id")
        player_id = request.form.get("player_id")

        # Walidacja danych wejściowych
        if not new_player_id or not player_id:
            flash("Należy wypełnić oba pola.", "danger")
            return render_template("swap_players.html", user=current_user, players=players, team_players=team_players)

        try:
            new_player_id = int(new_player_id)
            player_id = int(player_id)
        except ValueError:
            flash("Wybierz poprawnych zawodników.", "danger")
            return render_template("swap_players.html", user=current_user, players=players, team_players=team_players)

        # Pobierz zawodników z bazy danych
        new_player = Player.query.get(new_player_id)
        player = Player.query.get(player_id)

        # Sprawdź, czy zawodnicy istnieją
        if not new_player or not player:
            flash("Jeden lub obydwaj zawodnicy nie istnieją.", "danger")
            return render_template("swap_players.html", user=current_user, players=players, team_players=team_players)

        # Sprawdź, czy zawodnik należy do drużyny trenera
        if player.team_id != current_user.team_id:
            flash("Zawodnik do wymiany nie należy do twojej drużyny.", "danger")
            return render_template("swap_players.html", user=current_user, players=players, team_players=team_players)

        # Sprawdź, czy nowy zawodnik nie należy do żadnej drużyny
        if new_player.team_id is not None:
            flash("Nowy zawodnik jest już przypisany do drużyny.", "danger")
            return render_template("swap_players.html", user=current_user, players=players, team_players=team_players)

        # Przeprowadzenie wymiany zawodników
        try:
            # Przypisz nowego zawodnika do drużyny trenera
            new_player.team_id = current_user.team_id
            # Usuń obecnego zawodnika z drużyny
            player.team_id = None

            db.session.commit()
            flash("Wymiana zawodnika zakończona pomyślnie!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Wystąpił błąd podczas wymiany zawodników. Spróbuj ponownie.", "danger")

        return redirect(url_for('coach.swap_players'))

    return render_template("swap_players.html", user=current_user, players=players, team_players=team_players)


@coach.route('/change-position/<int:player_id>/<position>', methods=['POST'])
@login_required
def change_position(player_id, position):
    # Pobierz wszystkich zawodników z druzyny trenera
    coach_team = current_user.team
    team_players = Team.get_players(coach_team, coach_team.id)

    if request.method == "POST":
        print(player_id)
        print(position)
        try:
            player_id = int(player_id)
            position = str(position)
        except (ValueError, TypeError):
            flash("Nieprawidłowe dane wejściowe.", "danger")
            return redirect(url_for('coach.home_coach'))

        # Pobierz zawodnika na podstawie ID
        player = Player.query.get(player_id)
        if not player:
            flash("Zawodnik nie istnieje.", "danger")
            return redirect(url_for('coach.home_coach'))

        # Sprawdź, czy zawodnik należy do drużyny
        if player.team_id is None:
            flash("Ten zawodnik nie należy do żadnej drużyny.", "danger")
            return redirect(url_for('coach.home_coach'))

        # Sprawdź, czy zawodnik należy do drużyny trenera
        if player.team_id != current_user.team_id:
            flash("Ten zawodnik nie należy do twojej drużyny.", "danger")
            return redirect(url_for('coach.home_coach'))

        # Sprawdź, czy zmieniasz na tę samą pozycję
        if player.position == position:
            flash("Zawodnik już jest na tej pozycji.", "danger")
            return redirect(url_for('coach.home_coach'))

        # Zaktualizuj pozycję zawodnika
        player.position = position
        db.session.commit()
        flash("Zmiana pozycji zakończona!", "success")
        return redirect(url_for('coach.home_coach'))
