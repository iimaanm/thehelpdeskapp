from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Department
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, timezone
import re
import logging

MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 15
logger = logging.getLogger('helpdeskapp')


def utc_now():
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)


def to_utc(dt_value):
    """Converts a datetime value to UTC."""
    if dt_value is None:
        return None
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc)
    return dt_value.astimezone(timezone.utc)


def validate_password_policy(password, username):
    """Returns an error message if the password breaks the rules."""
    if len(password) < 12:
        return 'Password must be at least 12 characters long'
    if not re.search(r'[A-Z]', password):
        return 'Password must include at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return 'Password must include at least one lowercase letter'
    if not re.search(r'\d', password):
        return 'Password must include at least one number'
    if not re.search(r'[^A-Za-z0-9]', password):
        return 'Password must include at least one special character'
    if username and username.lower() in password.lower():
        return 'Password cannot contain your username'
    return None

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Logs a user in and applies lockout after repeated failures."""
    entered_username = ""
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        entered_username = username
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        # Stop early if the form is incomplete.
        if not username or not password:
            logger.warning('auth.login.missing_fields', extra={'attempted_username': username or None})
            flash('Username and password are required', category='danger')
            return render_template("login.html", user=current_user, entered_username=entered_username)

        if user and user.lockout_until and to_utc(user.lockout_until) > utc_now():
            logger.warning(
                'auth.login.locked_out',
                extra={'attempted_username': username, 'lockout_until': to_utc(user.lockout_until).isoformat()},
            )
            flash('Account locked after too many failed attempts. Try again later.', category='danger')
            return render_template("login.html", user=current_user, entered_username=entered_username)

        if user:
            if check_password_hash(user.password, password):
                user.failed_login_attempts = 0
                user.lockout_until = None
                db.session.commit()
                logger.info('auth.login.success', extra={'authenticated_user_id': user.id})
                flash('Login successful', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.failed_login_attempts = 0
                    user.lockout_until = utc_now() + timedelta(minutes=LOCKOUT_MINUTES)
                    db.session.commit()
                    logger.warning(
                        'auth.login.lockout_triggered',
                        extra={
                            'attempted_username': username,
                            'user_id': user.id,
                            'lockout_until': user.lockout_until.isoformat(),
                        },
                    )
                    flash('Account locked after too many failed attempts. Try again later.', category='danger')
                else:
                    db.session.commit()
                    logger.warning(
                        'auth.login.invalid_password',
                        extra={
                            'attempted_username': username,
                            'user_id': user.id,
                            'remaining_attempts': MAX_LOGIN_ATTEMPTS - user.failed_login_attempts,
                        },
                    )
                    flash('Invalid username or password', category='danger')
        else:
            logger.warning('auth.login.unknown_username', extra={'attempted_username': username})
            flash('Invalid username or password', category='danger')
    return render_template("login.html", user=current_user, entered_username=entered_username)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """Registers a normal user account after validation."""
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        first_name = str(request.form.get('first_name')).strip()
        password = request.form.get('password')
        passwordConfirm = request.form.get('passwordConfirm')
        department_name = str(request.form.get('department_name')).strip()
        resolved_department_id = None

        # Public signup only creates a normal user account.
        user = User.query.filter_by(username=username).first()
        if user:
            logger.warning('auth.signup.duplicate_username', extra={'attempted_username': username})
            flash('Username already exists', category='danger')
        elif not username:
            logger.warning('auth.signup.missing_username')
            flash('Username is required', category='danger')
        elif len(username) < 6:
            logger.warning('auth.signup.short_username', extra={'attempted_username': username})
            flash('Username must be at least 6 characters long', category='danger')
        elif not password:
            logger.warning('auth.signup.missing_password', extra={'attempted_username': username})
            flash('Password is required', category='danger')
        elif len(password) < 12:
            logger.warning('auth.signup.short_password', extra={'attempted_username': username})
            flash('Password must be at least 12 characters long', category='danger')
        elif not passwordConfirm:
            logger.warning('auth.signup.missing_password_confirmation', extra={'attempted_username': username})
            flash('Password confirmation is required', category='danger')
        elif password != passwordConfirm:
            logger.warning('auth.signup.password_mismatch', extra={'attempted_username': username})
            flash('Passwords must match', category='danger')
        else:
            if department_name:
                selected_department = Department.query.filter_by(name=department_name).first()
                if not selected_department:
                    logger.warning(
                        'auth.signup.invalid_department',
                        extra={'attempted_username': username, 'department_name': department_name},
                    )
                    flash('Selected department is invalid', category='danger')
                    return render_template("signup.html", user=current_user)
                resolved_department_id = selected_department.id

            password_policy_error = validate_password_policy(password, username)
            if password_policy_error:
                logger.warning(
                    'auth.signup.password_policy_rejected',
                    extra={'attempted_username': username, 'policy_error': password_policy_error},
                )
                flash(password_policy_error, category='danger')
                return render_template("signup.html", user=current_user)

            new_user = User(
                username=username,
                first_name=first_name,
                password=generate_password_hash(password),
                role='User',
                department_id=resolved_department_id,
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(
                'auth.signup.success',
                extra={'created_user_id': new_user.id, 'department_id': resolved_department_id},
            )
            login_user(new_user, remember=True)
            flash('Account created successfully', category='success')
            return redirect(url_for('views.home'))
    return render_template("signup.html", user=current_user)

@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    """Logs the current user out."""
    logger.info('auth.logout', extra={'authenticated_user_id': current_user.id})
    logout_user()
    flash('You have been logged out', category='success')
    return redirect(url_for('auth.login'))