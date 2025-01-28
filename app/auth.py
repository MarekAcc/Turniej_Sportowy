from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from .services.create import create_coach
from flask_login import login_user, login_required, logout_user, current_user
from .models import Tournament,Team,Match, Coach
import re
auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['GET','POST'])
def sign_up():
    if request.method == 'POST':
        # Pobierz wartości z formularza
        firstName = request.form.get('firstName', '').strip()
        lastName = request.form.get('lastName', '').strip()
        age = request.form.get('age', '').strip()
        login = request.form.get('login', '').strip()
        password1 = request.form.get('password1', '').strip()
        password2 = request.form.get('password2', '').strip()
        # Słownik przechowujący dane użytkownika (do przekazania do szablonu)
        form_data = {
            'firstName': firstName,
            'lastName': lastName,
            'age': age,
            'login': login
        }

        # Sprawdzenie czy formularze nie są puste
        if not firstName or not lastName or not age or not login or not password1 or not password2:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('sign_up.html', user=current_user, form_data=form_data)
                # Sprawdzenie, czy hasła są zgodne
        if password1 != password2:
            flash('Hasła muszą być identyczne!', 'danger')
            return render_template('sign_up.html', user=current_user, form_data=form_data)

        # Walidacja hasła: musi zawierać małe i duże litery oraz cyfrę
        if not re.search(r'[A-Z]', password1):
            flash('Hasło musi zawierać przynajmniej jedną dużą literę!', 'danger')
            return render_template('sign_up.html', user=current_user, form_data=form_data)

        if not re.search(r'[a-z]', password1):
            flash('Hasło musi zawierać przynajmniej jedną małą literę!', 'danger')
            return render_template('sign_up.html', user=current_user, form_data=form_data)

        if not re.search(r'[0-9]', password1):
            flash('Hasło musi zawierać przynajmniej jedną cyfrę!', 'danger')
            return render_template('sign_up.html', user=current_user, form_data=form_data)
        
        # Proba dodania nowego coacha(usera), jezeli funkcja register_coach wyrzuci błąd to 
        # wyswietla się komunikat i trzeba robić od nowa
        try:
            user = create_coach(firstName, lastName, age, login, password1, password2)
            login_user(user, remember=True)
            flash('Zarejestrowałeś się pomyślnie!', 'success')
            if current_user.login == 'ADMIN':
                return redirect(url_for('admin.home_admin'))
            else:
                return redirect(url_for('coach.home_coach'))
            
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('sign_up.html', user=current_user,form_data=form_data)
    # Jesli nie jest POSTem czyli jest GETem to wyswietl stronę rejestracji    
    return render_template('sign_up.html', user=current_user, form_data={})

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        if not login or not password:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template("login.html", user=current_user) 
        
        # Sprawdzenie czy login jest prawidłowy
        user = Coach.query.filter_by(login=login).first()
        if not user:
            flash('Nieprawidłowy login!', 'danger')
            return render_template("login.html", user=current_user) 
        
        if user.password != password:
            flash('Nieprawidłowe hasło!', 'danger')
            return render_template("login.html", user=current_user)
         # Zalogowanie Usera tak jakby wewnątrz Flaska
        login_user(user, remember=True)
        # Jezeli to admin się loguje to ustawiamy flagę, która będzie potem wykorzystywana do uprwanień.
        # (admin jest po prostu jednym z trenerów o loginie = ADMIN)
        if user.login == 'ADMIN':
            flash('Zalogowałeś się jako ADMIN!', 'success')
            return redirect(url_for('admin.home_admin'))
        else:
            flash('Zalogowałeś się pomyślnie!', 'success')
            return redirect(url_for('coach.home_coach'))
    # Jesli nie jest POSTem czyli jest GETem to wyswietl stronę logowania  
    return render_template("login.html", user=current_user)    

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany!', 'success')
    return redirect(url_for('auth.login'))