from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()


def create_app():

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'nice'

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:Wasa126x@localhost:5432/tournament'

    db.init_app(app)
    migrate.init_app(app, db)

    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')

    from .models import Coach
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Coach.query.get(int(id))

    return app
