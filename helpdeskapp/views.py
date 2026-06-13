from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Ticket
from . import db
import json

# Blueprint for main application views
views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    # Home page: introduces user to the app and handles ticket creation via modal form
    if request.method == 'POST':
        success, message = create_ticket_from_form(request)
        category = 'success' if success else 'danger'
        flash(message, category)
    return render_template("home.html", user=current_user)

@views.route('/new-ticket', methods=['GET', 'POST'])
@login_required
def new_ticket():
    # New ticket page for creating a new ticket
    if request.method == 'POST':
        success, message = create_ticket_from_form(request)
        category = 'success' if success else 'danger'
        flash(message, category)
    return render_template("new_ticket.html", user=current_user)

@views.route('/dashboard')
@login_required
def dashboard():
    # Dashboard: Admins see all tickets, users can only see their own
    if current_user.role == "Admin":
        tickets = Ticket.query.order_by(Ticket.date.desc()).all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.date.desc()).all()
    return render_template("dashboard.html", tickets=tickets)

@views.route('/edit-ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    # Edit ticket: Only Admin or the ticket owner can edit
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "Admin" and ticket.user_id != current_user.id:
        flash("You don't have permission to edit this ticket", "danger")
        return redirect(url_for('views.dashboard'))
    # Updating ticket fields
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if current_user.role == "Admin":
            priority = request.form.get('priority')
            status = request.form.get('status')
        if len(title) < 5:
            flash('Title must be at least 5 characters', 'danger')
        elif len(description) < 5:
            flash('Description must be at least 5 characters', 'danger')
        else:
            ticket.title = title
            ticket.description = description
            if current_user.role == "Admin":
                ticket.priority = priority
                ticket.status = status
            db.session.commit()
            flash('Ticket updated successfully', 'success')
            return redirect(url_for('views.dashboard'))
    return render_template("edit_ticket.html", ticket=ticket)

def create_ticket_from_form(request):
    # Helper function to validate and create a new ticket from form data
    title = request.form.get('title')
    ticket_description = request.form.get('ticket')
    # Form validation
    if len(title) < 5:
        return False, 'Ticket title must be at least 5 characters long'
    elif len(ticket_description) < 5:
        return False, 'Ticket description must be at least 5 characters long'
    new_ticket = Ticket(
        title=title,
        description=ticket_description,
        user_id=current_user.id
    )
    db.session.add(new_ticket)
    db.session.commit()
    return True, 'Ticket added successfully'

@views.route('/delete-ticket', methods=['POST'])
@login_required
def delete_ticket():
    # Delete ticket: User - only ticket owner can delete. Admin - can delete any ticket.
    ticket = json.loads(request.data)
    ticketId = ticket['ticketId']
    ticket = Ticket.query.get(ticketId)
    if ticket and (ticket.user_id == current_user.id or current_user.role == "Admin"):
        db.session.delete(ticket)
        db.session.commit()
        flash('Ticket deleted successfully', 'success')
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    else:
        flash('Ticket not found or you do not have permission to delete this ticket', 'danger')
        return jsonify({'message': 'Ticket not found or you do not have permission to delete this ticket'}), 404

@views.route('/guide')
@login_required
def guide_index():
    """Main guide page with all available guides"""
    return render_template('guide/index.html')

@views.route('/guide/<guide_topic>')
@login_required
def guide_topic(guide_topic):
    """Individual guide topic pages"""
    # Define available guides for security
    admin_guides = [
        'view-all-tickets', 'manage-user-requests', 'delete-tickets'
    ]
    user_guides = [
        'track-your-tickets', 'update-existing-tickets'
    ]
    
    # Check if user has permission to view this guide
    if current_user.role == "Admin" and guide_topic in admin_guides:
        return render_template(f'guide/{guide_topic}.html', guide_topic=guide_topic)
    elif current_user.role == "User" and guide_topic in user_guides:
        return render_template(f'guide/{guide_topic}.html', guide_topic=guide_topic)
    elif guide_topic == 'create-new-tickets':
        return render_template(f'guide/{guide_topic}.html', guide_topic=guide_topic)
    else:
        flash('Guide not found', 'error')
        return redirect(url_for('views.guide_index'))