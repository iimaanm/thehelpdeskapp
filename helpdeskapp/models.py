from . import db
from .constants import ROLE_ADMIN, ROLE_USER, TICKET_PRIORITY_MEDIUM, TICKET_STATUS_OPEN
from flask_login import UserMixin
from sqlalchemy.sql import func

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)  # Unique username
    first_name = db.Column(db.String(150), nullable=False)  # User's first name
    password = db.Column(db.String(255), nullable=False)  # Hashed password
    role = db.Column(db.String(150), nullable=False)  # ROLE_ADMIN or ROLE_USER
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)  # Foreign key to Department
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)  # Failed login counter for lockout
    lockout_until = db.Column(db.DateTime(timezone=True), nullable=True)  # Lock expiry timestamp
    tickets = db.relationship('Ticket', backref='user')  # Relationship to tickets

# Ticket model for helpdesk tickets
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)  # Ticket title
    description = db.Column(db.Text, nullable=False)  # Ticket description
    date = db.Column(db.DateTime(timezone=True), default=func.now())  # Date created
    status = db.Column(db.String(150), nullable=False, default=TICKET_STATUS_OPEN)  # Ticket status
    priority = db.Column(db.String(50), nullable=True, default=TICKET_PRIORITY_MEDIUM)  # Ticket priority
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User


# Department model for organising users
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)  # Department name
    users = db.relationship('User', backref='department')  # Relationship to users