import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from helpdeskapp.models import User
from helpdeskapp import db, create_app

@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    user = User(
        username="testuser",
        first_name="Test",
        password=generate_password_hash("testpass"),
        role="user",
        department_id="1"
    )
    db.session.add(user)
    db.session.commit()
    return user

def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"login" in response.data.lower()

def test_login_missing_fields(client):
    response = client.post('/login', data={})
    assert b'Username and password are required' in response.data

def test_login_user_not_found(client):
    response = client.post('/login', data={'username': 'nouser', 'password': 'nopass'})
    assert b'User not found' in response.data or b'please sign up' in response.data

def test_login_incorrect_password(client, user):
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'})
    assert b'Incorrect password' in response.data

def test_login_success(client, user):
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Login successful' in response.data or b'home' in response.data.lower()
