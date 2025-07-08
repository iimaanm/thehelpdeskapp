import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from flask_login import FlaskLoginClient
from helpdeskapp.auth import auth
from helpdeskapp.models import User
from helpdeskapp import db, create_app

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    app.test_client_class = FlaskLoginClient
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def user(app):
    user = User(
        username="test_helpdesk_user",
        first_name="Test",
        password=generate_password_hash("password123"),
        role="User",
        department_id="1"
    )
    db.session.add(user)
    db.session.commit()
    return user

def test_login_get(client):
    """Testing that the login page loads successfully."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower()

def test_login_post_success(client, user):
    """Testing successful login with correct credentials."""
    response = client.post("/login", data={
        "username": "test_helpdesk_user",
        "password": "password123"
    }, follow_redirects=True)
    assert b"login successful" in response.data.lower()

def test_login_post_wrong_password(client, user):
    """Testing login fails with incorrect password."""
    response = client.post("/login", data={
        "username": "test_helpdesk_user",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"incorrect password" in response.data.lower()

def test_login_user_not_found(client):
    """Testing login fails when username does not exist."""
    response = client.post("/login", data={
        "username": "nouser",
        "password": "password123"
    }, follow_redirects=True)
    assert b"user not found" in response.data.lower()

def test_login_post_missing_fields(client):
    """Testing login fails when username and password are missing."""
    response = client.post("/login", data={
        "username": "",
        "password": ""
    }, follow_redirects=True)
    assert b"username and password are required" in response.data.lower()

def test_signup_get(client):
    """Testing that the signup page loads successfully."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"signup" in response.data.lower()

def test_signup_post_success(client):
    """Testing successful signup with valid data."""
    response = client.post("/signup", data={
        "username": "newuser",
        "first_name": "New",
        "password": "newpassword123",
        "passwordConfirm": "newpassword123",
        "role": "User",
        "department_id": "1"
    }, follow_redirects=True)
    assert b"account created successfully" in response.data.lower()

def test_signup_post_existing_username(client, user):
    """Testing signup fails when username already exists."""
    response = client.post("/signup", data={
        "username": "test_helpdesk_user",
        "first_name": "Test",
        "password": "password123",
        "passwordConfirm": "password123",
        "role": "User",
        "department_id": "1"
    }, follow_redirects=True)
    assert b"username already exists" in response.data.lower()

@pytest.mark.parametrize("data,expected", [
    ({"username": "", "first_name": "A", "password": "pass123", "passwordConfirm": "pass123", "role": "user", "department_id": "1"}, b"username is required"),
    ({"username": "short", "first_name": "A", "password": "pass123", "passwordConfirm": "pass123", "role": "User", "department_id": "1"}, b"username must be at least 6 characters long"),
    ({"username": "validuser", "first_name": "A", "password": "", "passwordConfirm": "", "role": "User", "department_id": "1"}, b"password is required"),
    ({"username": "validuser", "first_name": "A", "password": "short", "passwordConfirm": "short", "role": "User", "department_id": "1"}, b"password must be at least 6 characters long"),
    ({"username": "validuser", "first_name": "A", "password": "password", "passwordConfirm": "", "role": "User", "department_id": "1"}, b"password confirmation is required"),
    ({"username": "validuser", "first_name": "A", "password": "password", "passwordConfirm": "different", "role": "User", "department_id": "1"}, b"passwords must match"),
    ({"username": "validuser", "first_name": "A", "password": "password", "passwordConfirm": "password", "role": "None", "department_id": "1"}, b"role is required")
])
def test_signup_post_validation(client, data, expected):
    """Testing signup validation for invalid input scenarios."""
    response = client.post("/signup", data=data, follow_redirects=True)
    assert expected in response.data.lower()

def test_logout_requires_login(client):
    """Testing that logout redirects to login if user not authenticated."""
    response = client.get("/logout", follow_redirects=True)
    assert b"login" in response.data.lower()

def test_logout_get(client, user):
    """Testing that logout works and redirects to login."""
    response = client.get("/logout", follow_redirects=True)
    assert b"login" in response.data.lower()