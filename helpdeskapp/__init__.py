from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

#Setting up database
db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'softwareandagile'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)


    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Ticket, Department
    create_database(app)
    
    # Loading user function for Flask-login   
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

#Creating new database if one does not exist
def create_database(app):
    if not path.exists('helpdeskapp/' + DB_NAME):
        with app.app_context():
            db.create_all()
    print("Created new database")