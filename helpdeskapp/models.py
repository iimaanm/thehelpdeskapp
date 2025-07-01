from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

#Creating database models for users, admins and tickets
class User(db.Model, UserMixin):
    #User model with role based access (admin/regular)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    tickets = db.relationship('Ticket', backref='user')

class Ticket(db.Model):
    # Ticket model for user reported issues
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.String(150), nullable=False, default="Open")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    priority = db.Column(db.String(50), nullable=True, default="Medium")


class Department(db.Model):
    # Department model for organising users and tickets
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    users = db.relationship('User', backref='department')