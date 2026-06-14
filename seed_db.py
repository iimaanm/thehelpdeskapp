from helpdeskapp import db
from helpdeskapp.constants import ROLE_ADMIN, ROLE_USER, TICKET_PRIORITY_MEDIUM, TICKET_STATUS_OPEN
from helpdeskapp.models import User, Ticket, Department
from werkzeug.security import generate_password_hash
import os

DEFAULT_DEPARTMENTS = [
    "Consulting",
    "Business",
    "HR",
    "Finance",
    "Marketing",
    "Facilities",
    "Resourcing",
]
def ensure_departments_exist():
    """Creates required lookup departments if they are missing."""
    existing_departments = {department.name for department in Department.query.all()}
    missing_departments = [
        Department(name=name) for name in DEFAULT_DEPARTMENTS if name not in existing_departments
    ]
    if missing_departments:
        db.session.add_all(missing_departments)
        db.session.commit()


def ensure_admin_user_exists():
    """Creates a single controlled admin account for SQLite fallback mode."""
    admin_username = str(os.getenv('DEFAULT_ADMIN_USERNAME', 'demo_admin')).strip()
    admin_first_name = str(os.getenv('DEFAULT_ADMIN_FIRST_NAME', 'Demo')).strip()
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
    admin_department_name = str(os.getenv('DEFAULT_ADMIN_DEPARTMENT', 'Consulting')).strip()

    if not admin_username or not admin_password:
        print('SQLite fallback admin credentials are incomplete. Skipping admin bootstrap.')
        return

    if User.query.filter_by(username=admin_username).first() is not None:
        return

    department = Department.query.filter_by(name=admin_department_name).first()
    if department is None:
        department = Department(name=admin_department_name)
        db.session.add(department)
        db.session.flush()

    admin_user = User(
        username=admin_username,
        first_name=admin_first_name,
        password=generate_password_hash(admin_password, method="pbkdf2:sha256"),
        role=ROLE_ADMIN,
        department_id=department.id,
    )
    db.session.add(admin_user)
    db.session.commit()

def seed_database():
    # Check if the database is already seeded
    if Department.query.first() is not None:
        print("Database already contains data. Skipping seeding.")
        return

    # Seeding Departments
    dept_names = ["IT", "HR", "Finance", "Support", "Sales", "Marketing", "Admin", "Legal", "Development", "Operations"]
    departments = [Department(name=name) for name in dept_names]
    db.session.add_all(departments)
    db.session.commit()
    dept_by_name = {dept.name: dept for dept in Department.query.all()}

    # Seeding Users (id's are auto incremented)
    default_seed_password = os.getenv('SEED_DEFAULT_PASSWORD', 'TempPass123!')
    for i in range(10):
        dept_name = dept_names[i % len(dept_names)]
        user = User(
            username=f"user{i}",
            first_name=f"User{i}",
            password=generate_password_hash(default_seed_password, method="pbkdf2:sha256"),
            role=ROLE_USER,
            department_id=dept_by_name[dept_name].id
        )
        db.session.add(user)

    seeded_admin_username = os.getenv('SEED_ADMIN_USERNAME', 'admin_demo')
    seeded_admin_password = os.getenv('SEED_ADMIN_PASSWORD', default_seed_password)
    seeded_admin_department = dept_by_name.get('Admin')
    admin_user = User(
        username=seeded_admin_username,
        first_name='Admin',
        password=generate_password_hash(seeded_admin_password, method="pbkdf2:sha256"),
        role=ROLE_ADMIN,
        department_id=seeded_admin_department.id if seeded_admin_department else None,
    )
    db.session.add(admin_user)
    db.session.commit()

    # Seeding Tickets
    users = User.query.all()
    for i in range(10):
        ticket = Ticket(
            title=f"Test Ticket {i}",
            description=f"This is test ticket {i}.",
            user_id=users[i % len(users)].id,
            status=TICKET_STATUS_OPEN,
            priority=TICKET_PRIORITY_MEDIUM
        )
        db.session.add(ticket)
    db.session.commit()

    print("Database seeded with 10 records per table.")