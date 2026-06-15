import pytest
import helpdeskapp
import seed_db
from helpdeskapp import create_app
from helpdeskapp.models import Department, User

@pytest.fixture
def app():
    """Creating and configuring a test app with a database."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    yield app

def test_app_creation(app, monkeypatch):
    """Testing that the Flask app is created with correct configuration."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    assert app is not None
    fresh_app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    assert fresh_app.config['SECRET_KEY'] == 'placeholder-secret-key'
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite://')

def test_redirect_to_login_if_not_authenticated_dashboard(app):
    """Testing that dashboard redirects to login when not authenticated."""
    with app.test_client() as client:
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.location

def test_redirect_to_login_if_not_authenticated_home(app):
    """Testing that home page redirects to login when not authenticated."""
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location

def test_redirect_to_login_if_not_authenticated_logout(app):
    """Testing that logout redirects to login when not authenticated."""
    with app.test_client() as client:
        response = client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location
        
def test_redirect_to_login_if_not_authenticated_newticket(app):
    """Testing that new ticket page redirects to login when not authenticated."""
    with app.test_client() as client:
        response = client.get('/new-ticket')
        assert response.status_code == 302
        assert '/login' in response.location

def test_create_app_with_config():
    """Testing that app creation with custom config works correctly."""
    config = {'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}
    app = create_app(config)
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    
def test_create_app_without_config(monkeypatch):   
    """Testing that app creation without config uses default values."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    app = create_app()
    assert app.config['TESTING'] is False
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///database.db'
    
def test_create_app_with_custom_secret_key():
    """Testing that app creation with custom secret key works correctly."""
    config = {'SECRET_KEY': 'helpdeskapp_secret_key'}
    app = create_app(config)
    assert app.config['SECRET_KEY'] == 'helpdeskapp_secret_key'
    
def test_create_app_with_default_secret_key(monkeypatch):
    """Testing that app creation uses default secret key when none provided."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    app = create_app()
    assert app.config['SECRET_KEY'] == 'placeholder-secret-key'
    
def test_create_app_with_sqlalchemy_uri():
    """Testing that app creation with custom database URI works correctly."""
    config = {'SQLALCHEMY_DATABASE_URI': 'sqlite:///:test.db'}
    app = create_app(config)
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:test.db'


def test_secure_cookie_defaults_in_production_mode():
    """Testing that secure cookie flags default to True outside testing/debug."""
    app = create_app()
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['SESSION_COOKIE_SECURE'] is True
    assert app.config['REMEMBER_COOKIE_HTTPONLY'] is True
    assert app.config['REMEMBER_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['REMEMBER_COOKIE_SECURE'] is True


def test_secure_cookie_defaults_in_testing_mode():
    """Testing that secure transport flags are relaxed in tests/local non-HTTPS flows."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['SESSION_COOKIE_SECURE'] is False
    assert app.config['REMEMBER_COOKIE_HTTPONLY'] is True
    assert app.config['REMEMBER_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['REMEMBER_COOKIE_SECURE'] is False


def test_production_requires_secret_key(monkeypatch):
    """Testing that production mode does not allow insecure default secret keys."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError):
        create_app({'APP_ENV': 'production', 'SECRET_KEY': 'placeholder-secret-key'})


def test_department_lookup_rows_are_bootstrapped(app):
    """Testing that required department lookup rows exist after app initialization."""
    with app.app_context():
        department_names = {department.name for department in Department.query.all()}
    assert {'Consulting', 'Business', 'HR', 'Finance', 'Marketing', 'Facilities', 'Resourcing'}.issubset(department_names)


def test_database_url_is_normalized_for_psycopg():
    assert helpdeskapp.normalize_database_url('postgres://user:pass@host/db') == 'postgresql+psycopg://user:pass@host/db'
    assert helpdeskapp.normalize_database_url('postgresql://user:pass@host/db') == 'postgresql+psycopg://user:pass@host/db'


def test_sqlite_fallback_when_database_unavailable(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@host/db')
    monkeypatch.setenv('ALLOW_SQLITE_FALLBACK', 'true')
    monkeypatch.setattr(helpdeskapp, 'can_connect_to_database', lambda _: False)

    app = create_app({'TESTING': True})
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///database.db'


def test_no_sqlite_fallback_when_database_available(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@host/db')
    monkeypatch.setattr(helpdeskapp, 'can_connect_to_database', lambda _: True)

    resolved_uri, used_fallback = helpdeskapp.resolve_database_uri(True)
    assert resolved_uri == 'postgresql+psycopg://user:pass@host/db'
    assert used_fallback is False


def test_fallback_admin_creation_runs_only_on_startup_fallback(monkeypatch):
    call_count = {'value': 0}

    def fake_admin_bootstrap():
        call_count['value'] += 1

    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@host/db')
    monkeypatch.setenv('ALLOW_SQLITE_FALLBACK', 'true')
    monkeypatch.setattr(helpdeskapp, 'can_connect_to_database', lambda _: False)
    monkeypatch.setattr(seed_db, 'ensure_admin_user_exists', fake_admin_bootstrap)

    create_app({'TESTING': True})

    assert call_count['value'] == 1


def test_fallback_admin_creation_not_run_for_regular_sqlite(monkeypatch):
    call_count = {'value': 0}

    def fake_admin_bootstrap():
        call_count['value'] += 1

    monkeypatch.setattr(seed_db, 'ensure_admin_user_exists', fake_admin_bootstrap)

    create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})

    assert call_count['value'] == 0


def test_fallback_admin_is_created_from_env_vars(monkeypatch, tmp_path):
    fallback_db_path = tmp_path / 'fallback-admin.db'

    monkeypatch.setattr(helpdeskapp, 'DB_NAME', str(fallback_db_path))
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@host/db')
    monkeypatch.setenv('ALLOW_SQLITE_FALLBACK', 'true')
    monkeypatch.setenv('DEFAULT_ADMIN_USERNAME', 'test_admin')
    monkeypatch.setenv('DEFAULT_ADMIN_PASSWORD', 'StrongAdminPass123!')
    monkeypatch.setenv('DEFAULT_ADMIN_FIRST_NAME', 'Marker')
    monkeypatch.setenv('DEFAULT_ADMIN_DEPARTMENT', 'Consulting')
    monkeypatch.setattr(helpdeskapp, 'can_connect_to_database', lambda _: False)

    app = create_app({'TESTING': True})

    with app.app_context():
        admin_user = User.query.filter_by(username='test_admin').first()

    assert app.config['USING_SQLITE_FALLBACK'] is True
    assert admin_user is not None
    assert admin_user.role == 'Admin'
    assert admin_user.first_name == 'Marker'