from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from flask_login import LoginManager
from sqlalchemy import inspect, text
from datetime import timedelta
from werkzeug.exceptions import HTTPException

from .logging_config import configure_logging

# Setting up the database instance for the app
db = SQLAlchemy()
DB_NAME = "database.db"


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

def create_app(config=None):
    # Configuring the Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'placeholder-secret-key')  # Default
    database_url = os.getenv('DATABASE_URL', f'sqlite:///{DB_NAME}')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://') and not database_url.startswith('postgresql+psycopg://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['APP_ENV'] = os.getenv('APP_ENV', 'development').lower()
    app.config['AUTO_SEED_DB'] = parse_bool(os.getenv('AUTO_SEED_DB'), default=False)
    app.config['DB_INIT_ON_STARTUP'] = parse_bool(
        os.getenv('DB_INIT_ON_STARTUP'),
        default=app.config['APP_ENV'] != 'production',
    )
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')

    provided_config = config or {}
    if provided_config:
        app.config.update(provided_config)

    if app.config.get('APP_ENV') == 'production' and app.config.get('SECRET_KEY') == 'placeholder-secret-key':
        raise RuntimeError('SECRET_KEY must be set in production')

    logger = configure_logging(app)

    # Secure cookie defaults: strict in production, workable during local development/tests.
    is_production_like = not app.config.get('DEBUG', False) and not app.config.get('TESTING', False)
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config['SESSION_COOKIE_SAMESITE'] = app.config.get('SESSION_COOKIE_SAMESITE') or 'Lax'
    if 'SESSION_COOKIE_SECURE' not in provided_config:
        app.config['SESSION_COOKIE_SECURE'] = is_production_like
    app.config.setdefault('REMEMBER_COOKIE_HTTPONLY', True)
    app.config['REMEMBER_COOKIE_SAMESITE'] = app.config.get('REMEMBER_COOKIE_SAMESITE') or 'Lax'
    if 'REMEMBER_COOKIE_SECURE' not in provided_config:
        app.config['REMEMBER_COOKIE_SECURE'] = is_production_like
    app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(minutes=30))

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

    @app.before_request
    def attach_request_id():
        from flask import g, request

        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.after_request
    def log_response(response):
        from flask import g, request

        logger.info(
            'request.completed',
            extra={
                'status_code': response.status_code,
                'request_id': getattr(g, 'request_id', None),
                'path': request.path,
            },
        )
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        return response

    @app.errorhandler(Exception)
    def handle_exception(error):
        if isinstance(error, HTTPException):
            logger.warning('request.http_error', exc_info=error)
            return error

        logger.exception('request.unhandled_exception')
        return 'An unexpected error occurred. Please try again later.', 500
    
    @login_manager.user_loader
    def load_user(id):
        return db.session.get(User, int(id))
    
    return app

# Function to create a new database if one does not exist
def create_database(app):
    from seed_db import ensure_departments_exist, seed_database

    if not app.config.get('DB_INIT_ON_STARTUP', True):
        app.logger.info('database.init_skipped')
        return

    with app.app_context():
        db.create_all()
        ensure_user_security_columns()
        ensure_departments_exist()
        should_seed = app.config.get('AUTO_SEED_DB', False) and app.config.get('APP_ENV') != 'production'
        if should_seed and is_database_empty():
            seed_database()
        elif should_seed:
            app.logger.info('database.seed_skipped_existing_data')
        else:
            app.logger.info('database.seed_disabled')


def is_database_empty():
    """Returns True if core tables are all empty."""
    from .models import Department, User, Ticket
    return (
        Department.query.first() is None
        and User.query.first() is None
        and Ticket.query.first() is None
    )


def ensure_user_security_columns():
    """Adds newly introduced authentication security columns on existing databases."""
    inspector = inspect(db.engine)
    user_columns = inspector.get_columns('user')
    columns = {column['name'] for column in user_columns}
    password_column = next((column for column in user_columns if column['name'] == 'password'), None)

    with db.engine.begin() as connection:
        if 'failed_login_attempts' not in columns:
            connection.execute(
                text('ALTER TABLE "user" ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0')
            )
        if 'lockout_until' not in columns:
            connection.execute(
                text('ALTER TABLE "user" ADD COLUMN lockout_until DATETIME')
            )
        password_length = getattr(password_column.get('type'), 'length', None) if password_column else None
        if password_length is not None and password_length < 255 and db.engine.dialect.name == 'postgresql':
            connection.execute(
                text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(255)')
            )