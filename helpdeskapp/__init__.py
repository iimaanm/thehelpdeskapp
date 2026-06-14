from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
import os
import uuid
from flask_login import LoginManager
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from werkzeug.exceptions import HTTPException

from .logging_config import configure_logging

# Setting up the database instance for the app
db = SQLAlchemy()
csrf = CSRFProtect()
DB_NAME = "database.db"


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def normalize_database_url(database_url):
    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    if database_url.startswith('postgresql://') and not database_url.startswith('postgresql+psycopg://'):
        return database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return database_url


def can_connect_to_database(database_url):
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect():
            pass
        engine.dispose()
        return True
    except SQLAlchemyError:
        return False


def resolve_database_uri(app_env, allow_sqlite_fallback):
    fallback_uri = f'sqlite:///{DB_NAME}'
    database_url = normalize_database_url(os.getenv('DATABASE_URL', fallback_uri))

    if database_url.startswith('sqlite://'):
        return database_url, False

    if can_connect_to_database(database_url):
        return database_url, False

    if allow_sqlite_fallback:
        return fallback_uri, True

    return database_url, False

def create_app(config=None):
    # Set up the Flask app.
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'placeholder-secret-key')
    app.config['APP_ENV'] = os.getenv('APP_ENV', 'development').lower()
    app.config['ALLOW_SQLITE_FALLBACK'] = parse_bool(os.getenv('ALLOW_SQLITE_FALLBACK'), default=True)
    resolved_database_url, using_sqlite_fallback = resolve_database_uri(
        app.config['APP_ENV'],
        app.config['ALLOW_SQLITE_FALLBACK'],
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = resolved_database_url
    app.config['USING_SQLITE_FALLBACK'] = using_sqlite_fallback
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['AUTO_SEED_DB'] = parse_bool(os.getenv('AUTO_SEED_DB'), default=False)
    app.config['DB_INIT_ON_STARTUP'] = parse_bool(
        os.getenv('DB_INIT_ON_STARTUP'),
        default=app.config['APP_ENV'] != 'production',
    )
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')

    provided_config = config or {}
    if provided_config:
        app.config.update(provided_config)

    # CSRF protection is enabled by default and only disabled in tests.
    app.config.setdefault('WTF_CSRF_ENABLED', not app.config.get('TESTING', False))

    if app.config.get('APP_ENV') == 'production' and app.config.get('SECRET_KEY') == 'placeholder-secret-key':
        raise RuntimeError('SECRET_KEY must be set in production')

    logger = configure_logging(app)
    logger.info(
        'app.startup.configured',
        extra={
            'app_env': app.config['APP_ENV'],
            'using_sqlite_fallback': using_sqlite_fallback,
            'db_init_on_startup': app.config['DB_INIT_ON_STARTUP'],
        },
    )
    if using_sqlite_fallback:
        logger.warning('database.sqlite_fallback_activated', extra={'database_backend': 'sqlite'})

    # Use secure cookies outside debug and tests.
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
    csrf.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User
    create_database(app)

    @app.before_request
    def attach_request_id():
        from flask import g, request

        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.route('/favicon.ico')
    def favicon():
        from flask import Response

        return Response(status=204)

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

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        logger.warning('request.csrf_rejected', extra={'csrf_error': error.description})
        return 'CSRF validation failed. Please refresh and try again.', 400
    
    @login_manager.user_loader
    def load_user(id):
        return db.session.get(User, int(id))
    
    return app

def create_database(app):
    """Create tables and run startup database tasks."""
    from seed_db import ensure_admin_user_exists, ensure_departments_exist, seed_database

    if not app.config.get('DB_INIT_ON_STARTUP', True):
        app.logger.info('database.init_skipped')
        return

    with app.app_context():
        db.create_all()
        ensure_user_security_columns()
        ensure_departments_exist()
        if app.config.get('USING_SQLITE_FALLBACK', False):
            ensure_admin_user_exists()
            app.logger.warning('database.fallback_admin_bootstrap_attempted')
        should_seed = app.config.get('AUTO_SEED_DB', False) and app.config.get('APP_ENV') != 'production'
        if should_seed and is_database_empty():
            app.logger.info('database.seed_started')
            seed_database()
        elif should_seed:
            app.logger.info('database.seed_skipped_existing_data')
        else:
            app.logger.info('database.seed_disabled')


def is_database_empty():
    """Return True if the main tables are empty."""
    from .models import Department, User, Ticket
    return (
        Department.query.first() is None
        and User.query.first() is None
        and Ticket.query.first() is None
    )


def ensure_user_security_columns():
    """Add missing security columns to older databases."""
    inspector = inspect(db.engine)
    user_columns = inspector.get_columns('user')
    columns = {column['name'] for column in user_columns}
    password_column = next((column for column in user_columns if column['name'] == 'password'), None)

    with db.engine.begin() as connection:
        if 'failed_login_attempts' not in columns:
            logging.getLogger('helpdeskapp').info('database.schema.adding_failed_login_attempts')
            connection.execute(
                text('ALTER TABLE "user" ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0')
            )
        if 'lockout_until' not in columns:
            logging.getLogger('helpdeskapp').info('database.schema.adding_lockout_until')
            connection.execute(
                text('ALTER TABLE "user" ADD COLUMN lockout_until DATETIME')
            )
        password_length = getattr(password_column.get('type'), 'length', None) if password_column else None
        if password_length is not None and password_length < 255 and db.engine.dialect.name == 'postgresql':
            logging.getLogger('helpdeskapp').warning(
                'database.schema.expanding_password_column',
                extra={'existing_length': password_length},
            )
            connection.execute(
                text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(255)')
            )