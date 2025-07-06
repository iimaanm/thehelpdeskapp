from helpdeskapp import create_app, db
from helpdeskapp.models import User, Ticket, Department
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Add Departments
    if not Department.query.first():
        departments = [
            Department(name="Consulting"),
            Department(name="Business"),
            Department(name="HR"),
            Department(name="Finance"),
            Department(name="Marketing"),
            Department(name="Facilities"),
            Department(name="Resourcing"),
            Department(name="IT"),
            Department(name="Support"),
            Department(name="Admin")
        ]
        db.session.add_all(departments)
        db.session.commit()

    # Add Users
    if not User.query.first():
        for i in range(10):
            user = User(
                username=f"user{i}",
                first_name=f"User{i}",
                password=generate_password_hash("password"),
                role="user",
                department_id=f"{i + 1}",
            )
            db.session.add(user)
        db.session.commit()

    # Add Tickets
    if not Ticket.query.first():
        for i in range(10):
            ticket = Ticket(
                title=f"Test Ticket {i}",
                description=f"This is test ticket {i}.",
                user_id=f"{i + 1}",
                status="Open"
            )
            db.session.add(ticket)
        db.session.commit()

    print("Database seeded with 10 records per table.")