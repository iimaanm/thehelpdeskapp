from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import User

from helpdeskapp.test_auth import user
from .models import Ticket
from . import db
import json
from flask_login import current_user

views = Blueprint('views', __name__)



@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        title = request.form.get('title')
        ticket = request.form.get('ticket')
        if len(title) < 5:
            
            print(f"Username: {current_user.username}, Role: {current_user.role}, Department ID: {current_user.department_id}")
            
            flash('Ticket title must be at least 5 characters long', category='danger')
        elif len(ticket) < 5:
            flash('Ticket description must be at least 5 characters long', category='danger')
        else:
            new_ticket = Ticket(description=ticket, title=title, user_id=current_user.id)
            db.session.add(new_ticket)
            db.session.commit()
            flash('Ticket added successfully', category='success')
            
    return render_template("home.html", user=current_user)

@views.route('/dashboard')
@login_required
def dashboard():
    # Check if the current user is an admin
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin

    if is_admin:
        tickets = Ticket.query.all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "dashboard.html",
        tickets=tickets,
        is_admin=is_admin,
        user=current_user
    )


@views.route('/delete-ticket', methods=['POST'])
@login_required
def delete_ticket():
    ticket = json.loads(request.data)
    ticketId = ticket['ticketId']
    ticket = Ticket.query.get(ticketId)
    if ticket and ticket.user_id == current_user.id:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    else:
        return jsonify({'message': 'Ticket not found'}), 404
        