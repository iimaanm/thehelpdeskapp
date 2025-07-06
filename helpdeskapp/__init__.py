from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

# Setting up the database instance for the app
# This will be used throughout the application for ORM operations
db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    # Factory function to create and configure the Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'softwareandagile'  # Secret key for session management and security
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # SQLite database URI
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirect to login page if not authenticated
    login_manager.init_app(app)

    # Registering blueprints for modularisation
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models to ensure tables are created
    from .models import User, Ticket, Department
    create_database(app)
    
    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

# Function to create a new database if one does not exist
def create_database(app):
    if not path.exists('helpdeskapp/' + DB_NAME):
        with app.app_context():
            db.create_all()  # Creates all tables defined in models
    print("Created new database")