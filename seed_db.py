from helpdeskapp import create_app, db
from helpdeskapp.models import User, Ticket, Department
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Clearing existing records to avoid duplicates
    Ticket.query.delete()
    User.query.delete()
    Department.query.delete()
    db.session.commit()

    # Seeding Departments
    dept_names = ["IT", "HR", "Finance", "Support", "Sales", "Marketing", "Admin", "Legal", "Development", "Operations"]
    departments = [Department(name=name) for name in dept_names]
    db.session.add_all(departments)
    db.session.commit()
    dept_by_name = {dept.name: dept for dept in Department.query.all()}

    # Seeding Users (id's are auto incremented)
    for i in range(10):
        dept_name = dept_names[i % len(dept_names)]
        user = User(
            username=f"user{i}",
            first_name=f"User{i}",
            password=generate_password_hash("password"),
            role="User",
            department_id=dept_by_name[dept_name].id
        )
        db.session.add(user)
    db.session.commit()

    # Seeding Tickets
    users = User.query.all()
    for i in range(10):
        ticket = Ticket(
            title=f"Test Ticket {i}",
            description=f"This is test ticket {i}.",
            user_id=users[i % len(users)].id,
            status="Open",
            priority="Medium"
        )
        db.session.add(ticket)
    db.session.commit()

    print("Database seeded with 10 records per table.")