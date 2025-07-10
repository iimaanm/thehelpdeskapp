from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

# Setting up the database instance for the app
db = SQLAlchemy()
DB_NAME = "database.db"

def create_app(config=None):
    # Configuring the Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'softwareandagile'  # Secret key for session management and security
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # SQLite database URI
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Importing models to ensure tables are created
    from .models import User, Ticket, Department
    create_database(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    if config:
        app.config.update(config)

    return app

# Function to create a new database if one does not exist
def create_database(app):
    from seed_db import seed_database
    db_path = 'helpdeskapp/' + DB_NAME
    db_exists = path.exists(db_path)
    
    with app.app_context():
        db.create_all()
        if not db_exists:
            seed_database()
        else:
            print("Database already exists")