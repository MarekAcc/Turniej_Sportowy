from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .services.coach import register_coach
from flask_login import login_user, login_required, logout_user, current_user
from .models import Tournament,Team,Match, Coach

auth = Blueprint('auth', __name__)

@auth.route('/sign-up', methods=['GET','POST'])
def sign_up():
    if request.method == 'POST':
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        age = request.form.get('age')
        login = request.form.get('login')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Sprawdzenie czy formularze nie są puste
        if not firstName or not lastName or not age or not login or not password1 or not password2:
            flash('Wszystkie pola są wymagane!', 'danger')
            return render_template('sign_up.html', user=current_user)
        
        # Proba dodania nowego coacha(usera), jezeli funkcja register_coach wyrzuci błąd to 
        # wyswietla się komunikat i trzeba robić od nowa
        try:
            user = register_coach(firstName, lastName, age, login, password1, password2)
            login_user(user, remember=True)
            flash('Zarejestrowałeś się pomyślnie!', 'success')
            return redirect(url_for('views.home'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('sign_up.html', user=current_user)
    # Jesli nie jest POSTem czyli jest GETem to wyswietl stronę rejestracji    
    return render_template('sign_up.html', user=current_user)

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
            session['is_admin'] = True
            return render_template("home_admin.html", user=current_user)
        else:
            session['is_admin'] = False
        flash('Zalogowałeś się pomyślnie!', 'success')
        return render_template("trener_p.html", user=current_user)
    # Jesli nie jest POSTem czyli jest GETem to wyswietl stronę logowania  
    return render_template("login.html", user=current_user)    

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('is_admin', None)
    flash('Zostałeś wylogowany!', 'success')
    return redirect(url_for('auth.login'))