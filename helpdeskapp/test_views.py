import pytest
from flask import url_for
from flask_login import FlaskLoginClient
from helpdeskapp import create_app, db
from helpdeskapp.models import Ticket, User, Department
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """Creating and configuring a test app with database."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    app.test_client_class = FlaskLoginClient
    with app.app_context():
        db.create_all()
        
        # Creating a department
        dept = Department(name="IT")
        db.session.add(dept)
        db.session.commit()
        
        # Creating users
        user = User(
            username="testuser", 
            first_name="Testuser", 
            password=generate_password_hash("password123"),
            role="User",
            department_id=dept.id
        )
        admin = User(
            username="testadmin", 
            first_name="Testadmin", 
            password=generate_password_hash("password123"),
            role="Admin",
            department_id=dept.id
        )
        db.session.add_all([user, admin])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Creating test client for the app."""
    return app.test_client()

@pytest.fixture
def user(app):
    """Getting the test user from the database."""
    return User.query.filter_by(username="testuser").first()

@pytest.fixture
def admin(app):
    """Getting the test admin user from the database."""
    return User.query.filter_by(username="testadmin").first()

def test_home_get_requires_login(client):
    """Testing that unauthenticated access to home page redirects to login."""
    response = client.get("/")
    assert response.status_code == 302
    assert '/login' in response.location

def test_home_post_ticket_creation(client, user):
    """Testing successful ticket creation from home page when logged in."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    
    response = client.post("/", data={
        "title": "Test Ticket Title", 
        "ticket": "Test description for the ticket"
    }, follow_redirects=True)
    
    assert b"Ticket added successfully" in response.data
    assert Ticket.query.filter_by(title="Test Ticket Title").first() is not None

def test_home_post_ticket_creation_invalid_title(client, user):
    """Testing ticket creation fails with title that's too short."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    response = client.post("/", data={
        "title": "abc", 
        "ticket": "Valid desc"
    }, follow_redirects=True)
    
    assert b"Ticket title must be at least 5 characters long" in response.data

def test_home_post_ticket_creation_invalid_description(client, user):
    """Testing ticket creation fails with description that's too short."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    response = client.post("/", data={
        "title": "Valid title", 
        "ticket": "abc"
    }, follow_redirects=True)
    
    assert b"Ticket description must be at least 5 characters long" in response.data

def test_new_ticket_get(client, user):
    """Testing that new ticket page loads successfully when logged in."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    response = client.get("/new_ticket")
    assert response.status_code == 200
    assert b"Submit a New Ticket" in response.data

def test_new_ticket_post(client, user):
    """Testing successful ticket creation from new ticket page when logged in."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    response = client.post("/new_ticket", data={
        "title": "Ticket Title 2", 
        "ticket": "Description test"
    }, follow_redirects=True)
    
    assert b"Ticket added successfully" in response.data
    assert Ticket.query.filter_by(title="Ticket Title 2").first() is not None

def test_dashboard_user_sees_own_tickets(client, user):
    """Testing that regular users can only see their own tickets on dashboard."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    # Creating a ticket for user
    ticket = Ticket(title="User Ticket", description="User desc", user_id=user.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"User Ticket" in response.data

def test_dashboard_admin_sees_all_tickets(client, admin, user):
    """Testing that admin users can see all tickets on dashboard."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True
    ticket1 = Ticket(title="Admin Ticket", description="Admin desc", user_id=admin.id)
    ticket2 = Ticket(title="User Ticket", description="User desc", user_id=user.id)
    db.session.add_all([ticket1, ticket2])
    db.session.commit()
    
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Admin Ticket" in response.data
    assert b"User Ticket" in response.data

def test_edit_ticket_permission_denied(client, user, admin):
    """Testing that users cannot edit tickets that don't belong to them."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    ticket = Ticket(title="Other Ticket", description="Other desc", user_id=admin.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.get(f"/edit-ticket/{ticket.id}", follow_redirects=True)
    assert b"You don&#39;t have permission to edit this ticket" in response.data

def test_edit_ticket_user_success(client, user):
    """Testing that users can successfully edit their own tickets."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    ticket = Ticket(title="My Ticket", description="Original description", user_id=user.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post(
        f"/edit-ticket/{ticket.id}",
        data={"title": "Edited Title", "description": "Edited description"},
        follow_redirects=True,
    )
    
    assert b"Ticket updated successfully" in response.data
    updated_ticket = Ticket.query.get(ticket.id)
    assert updated_ticket.title == "Edited Title"
    assert updated_ticket.description == "Edited description"

def test_edit_ticket_admin_can_edit_all_fields(client, admin, user):
    """Testing that admin users can edit all fields of any ticket."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True  # Changed from '_new' to '_fresh'
    
    ticket = Ticket(
        title="My Admin Ticket",
        description="Admin original description",
        user_id=user.id,
        priority="Low",
        status="Open"
    )
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post(
        f"/edit-ticket/{ticket.id}",
        data={
            "title": "Admin Edited Title",
            "description": "Admin edited description",
            "priority": "High",
            "status": "Resolved"
        },
        follow_redirects=True,
    )
    
    assert b"Ticket updated successfully" in response.data
    updated_ticket = Ticket.query.get(ticket.id)
    assert updated_ticket.title == "Admin Edited Title"
    assert updated_ticket.priority == "High"
    assert updated_ticket.status == "Resolved"

def test_delete_ticket_user(client, user):
    """Testing that users can delete their own tickets."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    ticket = Ticket(title="Delete ticket", description="Delete ticket description", user_id=user.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post("/delete-ticket", json={"ticketId": ticket.id})
    assert response.status_code == 200
    assert Ticket.query.get(ticket.id) is None

def test_delete_ticket_admin(client, admin, user):
    """Testing that admin users can delete any ticket."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True

    ticket = Ticket(title="Delete Admin", description="Admin delete description", user_id=user.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post("/delete-ticket", json={"ticketId": ticket.id})
    assert response.status_code == 200
    assert Ticket.query.get(ticket.id) is None

def test_delete_ticket_permission_denied(client, user, admin):
    """Testing that users cannot delete tickets that don't belong to them."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    ticket = Ticket(title="Not the user's ticket", description="Not the user's ticket description", user_id=admin.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post("/delete-ticket", json={"ticketId": ticket.id})
    assert response.status_code == 404
    assert Ticket.query.get(ticket.id) is not None

def test_edit_ticket_validation_short_title(client, user):
    """Testing that edit ticket fails with short title."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    ticket = Ticket(title="Original Title", description="Original description", user_id=user.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post(
        f"/edit-ticket/{ticket.id}",
        data={"title": "abc", "description": "Valid description"},
        follow_redirects=True,
    )
    
    assert b"Title must be at least 5 characters" in response.data

def test_edit_ticket_validation_short_description(client, user):
    """Testing that edit ticket fails with short description."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    
    ticket = Ticket(title="Original Title", description="Original description", user_id=user.id)
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post(
        f"/edit-ticket/{ticket.id}",
        data={"title": "Valid Title", "description": "abc"},
        follow_redirects=True,
    )
    
    assert b"Description must be at least 5 characters" in response.data