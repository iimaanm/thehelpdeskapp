from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Ticket
from . import db
from .permissions import can_access_guide, can_delete_ticket, can_edit_ticket, is_admin
import json
import logging

# Blueprint for main application views
views = Blueprint('views', __name__)
logger = logging.getLogger('helpdeskapp')

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    """Displays the home page and handle ticket submissions."""
    if request.method == 'POST':
        success, message = create_ticket_from_form(request)
        category = 'success' if success else 'danger'
        flash(message, category)
    return render_template("home.html", user=current_user)

@views.route('/new-ticket', methods=['GET', 'POST'])
@login_required
def new_ticket():
    """Displays the new ticket page and save valid tickets."""
    if request.method == 'POST':
        success, message = create_ticket_from_form(request)
        category = 'success' if success else 'danger'
        flash(message, category)
    return render_template("new_ticket.html", user=current_user)

@views.route('/dashboard')
@login_required
def dashboard():
    """Displays the tickets this user is allowed to view."""
    if is_admin(current_user):
        tickets = Ticket.query.order_by(Ticket.date.desc()).all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.date.desc()).all()
    logger.info('ticket.dashboard.view', extra={'role': current_user.role, 'ticket_count': len(tickets)})
    return render_template("dashboard.html", tickets=tickets)

@views.route('/edit-ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    """Updates a ticket if the user is allowed to edit it."""
    ticket = db.get_or_404(Ticket, ticket_id)
    if not can_edit_ticket(current_user, ticket):
        logger.warning(
            'ticket.edit.unauthorized',
            extra={'ticket_id': ticket.id, 'ticket_owner_id': ticket.user_id, 'role': current_user.role},
        )
        flash("You don't have permission to edit this ticket", "danger")
        return redirect(url_for('views.dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if is_admin(current_user):
            priority = request.form.get('priority')
            status = request.form.get('status')
        if len(title) < 5:
            logger.warning('ticket.edit.invalid_title', extra={'ticket_id': ticket.id, 'title_length': len(title)})
            flash('Title must be at least 5 characters', 'danger')
        elif len(description) < 5:
            logger.warning(
                'ticket.edit.invalid_description',
                extra={'ticket_id': ticket.id, 'description_length': len(description)},
            )
            flash('Description must be at least 5 characters', 'danger')
        else:
            ticket.title = title
            ticket.description = description
            if is_admin(current_user):
                ticket.priority = priority
                ticket.status = status
            db.session.commit()
            logger.info('ticket.edit.success', extra={'ticket_id': ticket.id, 'role': current_user.role})
            flash('Ticket updated successfully', 'success')
            return redirect(url_for('views.dashboard'))
    return render_template("edit_ticket.html", ticket=ticket)

def create_ticket_from_form(request):
    """Checks ticket form data and creates a ticket."""
    title = request.form.get('title')
    ticket_description = request.form.get('ticket')

    if len(title) < 5:
        logger.warning('ticket.create.invalid_title', extra={'title_length': len(title)})
        return False, 'Ticket title must be at least 5 characters long'
    elif len(ticket_description) < 5:
        logger.warning('ticket.create.invalid_description', extra={'description_length': len(ticket_description)})
        return False, 'Ticket description must be at least 5 characters long'
    new_ticket = Ticket(
        title=title,
        description=ticket_description,
        user_id=current_user.id
    )
    db.session.add(new_ticket)
    db.session.commit()
    logger.info('ticket.create.success', extra={'ticket_id': new_ticket.id})
    return True, 'Ticket added successfully'

@views.route('/delete-ticket', methods=['POST'])
@login_required
def delete_ticket():
    """Deletes a ticket if the user owns it or is an admin."""
    ticket = json.loads(request.data)
    ticketId = ticket['ticketId']
    ticket = db.session.get(Ticket, ticketId)
    if ticket and can_delete_ticket(current_user, ticket):
        db.session.delete(ticket)
        db.session.commit()
        logger.info('ticket.delete.success', extra={'ticket_id': ticketId, 'role': current_user.role})
        flash('Ticket deleted successfully', 'success')
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    else:
        logger.warning(
            'ticket.delete.unauthorized_or_missing',
            extra={'ticket_id': ticketId, 'role': current_user.role},
        )
        flash('Ticket not found or you do not have permission to delete this ticket', 'danger')
        return jsonify({'message': 'Ticket not found or you do not have permission to delete this ticket'}), 404

@views.route('/guide')
@login_required
def guide_index():
    """Displays the guide index."""
    return render_template('guide/index.html')

@views.route('/guide/<guide_topic>')
@login_required
def guide_topic(guide_topic):
    """Displays a guide page only if the user can access it."""

    if can_access_guide(current_user, guide_topic):
        logger.info('guide.access.granted', extra={'guide_topic': guide_topic, 'role': current_user.role})
        return render_template(f'guide/{guide_topic}.html', guide_topic=guide_topic)

    logger.warning('guide.access.denied_or_missing', extra={'guide_topic': guide_topic, 'role': current_user.role})
    flash('Guide not found', 'error')
    return redirect(url_for('views.guide_index'))