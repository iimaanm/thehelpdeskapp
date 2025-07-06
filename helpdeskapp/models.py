from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)  # Unique username
    first_name = db.Column(db.String(150), nullable=False)  # User's first name
    password = db.Column(db.String(150), nullable=False)  # Hashed password
    role = db.Column(db.String(150), nullable=False)  # 'Admin' or 'User'
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)  # Foreign key to Department
    tickets = db.relationship('Ticket', backref='user')  # Relationship to tickets

# Ticket model for helpdesk tickets
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)  # Ticket title
    description = db.Column(db.Text, nullable=False)  # Ticket description
    date = db.Column(db.DateTime(timezone=True), default=func.now())  # Date created
    status = db.Column(db.String(150), nullable=False, default="Open")  # Ticket status
    priority = db.Column(db.String(50), nullable=True, default="Medium")  # Ticket priority
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User


# Department model for organising users
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)  # Department name
    users = db.relationship('User', backref='department')  # Relationship to users