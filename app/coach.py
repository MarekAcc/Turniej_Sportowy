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
    if coach_team:
        players = Team.get_players(coach_team, coach_team.id)
    else:
        players = {}
    return render_template("coach_dashboard.html", user=current_user, players=players)

# --------------COACH OD IGORA--------------------
@coach.route('/remove-player-from-team', methods=['POST'])
@login_required
def remove_player_from_team():
    player_id = request.form.get('player_id')

    if not player_id:
        flash('Nie podano zawodnika do usunięcia!', 'danger')
        return redirect(url_for('coach.home_coach'))

    # Znajdź zawodnika w bazie
    player = Player.query.get(player_id)

    if not player:
        flash('Nie znaleziono zawodnika!', 'danger')
        return redirect(url_for('coach.home_coach'))

    if player.team_id != current_user.team.id:
        flash('Nie możesz usunąć zawodnika z innej drużyny!', 'danger')
        return redirect(url_for('coach.home_coach'))

    # Usuń zawodnika z drużyny
    player.team_id = None
    player.position = None
    player.status = 'active'  # Lub ustaw na inną drużynę, jeśli to pożądane
    db.session.commit()

    flash(f'Zawodnik {player.firstName} {player.lastName} został usunięty z drużyny.', 'success')
    return redirect(url_for('coach.home_coach'))

@coach.route('/add-new-player', methods=['GET', 'POST'])
@login_required
def add_new_player():
    players = Player.get_players_without_team()

    if request.method == 'POST':
        # Pobierz dane z formularza
        new_player_id = request.form.get("new_player_id")

        if not new_player_id:
            flash("Należy wypełnić pole.", "danger")
            return render_template("add_new_player_by_coach.html", user=current_user, players=players)

        try:
            new_player_id = int(new_player_id)
        except ValueError:
            flash("Wybierz poprawnych zawodników.", "danger")
            return render_template("add_new_player_by_coach.html", user=current_user, players=players)

        new_player = Player.query.get(new_player_id)

        if not new_player:
            flash("Zawodnik nie istnieje", "danger")
            return render_template("add_new_player_by_coach.html", user=current_user, players=players)

        if new_player.team_id is not None:
            flash("Nowy zawodnik jest już przypisany do drużyny.", "danger")
            return render_template("add_new_player_by_coach.html", user=current_user, players=players)

        # Przeprowadzenie wymiany zawodników
        try:
            # Przypisz nowego zawodnika do drużyny trenera
            new_player.team_id = current_user.team_id

            db.session.commit()
            flash("Dodanie zawodnika zakończone pomyślnie!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Wystąpił błąd dodawania zawodnika. Spróbuj ponownie.", "danger")

        return redirect(url_for('coach.add_new_player'))
    
    return render_template("add_new_player_by_coach.html", user=current_user, players=players)

@coach.route('/change-position/<int:player_id>/<position>', methods=['POST'])
@login_required
def change_position(player_id, position):
    # Pobierz wszystkich zawodników z druzyny trenera
    coach_team = current_user.team
    team_players = Team.get_players(coach_team, coach_team.id)

    if request.method == "POST":
        try:
            player_id = int(player_id)
            position = str(position)
        except (ValueError, TypeError):
            flash("Nieprawidłowe dane wejściowe.", "danger")
            return redirect(url_for('coach.home_coach'))

        if position not in ['field', 'substitute', 'null']:
            flash("Nieprawidłowa pozycja!", "danger")
            return redirect(url_for('coach.home_coach'))
        
        if position == 'null':
            position = None
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

        if position == 'field':
            num_field_players = Player.query.filter_by(position='field', team_id=coach_team.id).count()
            if player.status == 'suspended':
                flash("Nie mozesz dodać zawieszonego zawodnika do pierwszego skladu!", "danger")
                return redirect(url_for('coach.home_coach'))
            if num_field_players >= 5:
                flash("Twój pierwszy skład jest pełny", "danger")
                return redirect(url_for('coach.home_coach'))
        elif position == 'substitute':
            num_substitute_players = Player.query.filter_by(position='substitute', team_id=coach_team.id).count()
            if num_substitute_players >= 4:
                flash("Twoja ławka rezerwowych jest pełna", "danger")
                return redirect(url_for('coach.home_coach'))

        # Zaktualizuj pozycję zawodnika
        player.position = position
        db.session.commit()
        flash("Zmiana pozycji zakończona!", "success")
        return redirect(url_for('coach.home_coach'))
