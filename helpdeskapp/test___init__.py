from flask import config
import pytest
from helpdeskapp import create_app

@pytest.fixture
def app():
    """Creating and configuring a test app with a database."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    yield app

def test_app_creation(app):
    """Testing that the Flask app is created with correct configuration."""
    assert app is not None
    assert app.config['SECRET_KEY'] == 'softwareandagile'
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
        response = client.get('/new_ticket')
        assert response.status_code == 302
        assert '/login' in response.location

def test_create_app_with_config():
    """Testing that app creation with custom config works correctly."""
    config = {'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}
    app = create_app(config)
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    
def test_create_app_without_config():   
    """Testing that app creation without config uses default values."""
    app = create_app()
    assert app.config['TESTING'] is False
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///database.db'
    
def test_create_app_with_custom_secret_key():
    """Testing that app creation with custom secret key works correctly."""
    config = {'SECRET_KEY': 'helpdeskapp_secret_key'}
    app = create_app(config)
    assert app.config['SECRET_KEY'] == 'helpdeskapp_secret_key'
    
def test_create_app_with_default_secret_key():
    """Testing that app creation uses default secret key when none provided."""
    app = create_app()
    assert app.config['SECRET_KEY'] == 'softwareandagile'
    
def test_create_app_with_sqlalchemy_uri():
    """Testing that app creation with custom database URI works correctly."""
    config = {'SQLALCHEMY_DATABASE_URI': 'sqlite:///:test.db'}
    app = create_app(config)
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:test.db'