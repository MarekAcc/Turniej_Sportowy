from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()

def create_app():

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'nice'

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:admin@localhost:5432/tournament'

    db.init_app(app)
    migrate.init_app(app,db)

    from .views import views

    app.register_blueprint(views, url_prefix='/') 

    return app