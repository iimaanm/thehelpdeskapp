from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Department
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, timezone
import re

MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 15


def utc_now():
    return datetime.now(timezone.utc)


def to_utc(dt_value):
    if dt_value is None:
        return None
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc)
    return dt_value.astimezone(timezone.utc)


def validate_password_policy(password, username):
    """Returns a policy error message or None when password is compliant."""
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

# Blueprint for authentication routes (login, signup, logout)
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Login route: handles user authentication
    entered_username = ""
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        entered_username = username
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        # Validation and authentication logic
        if not username or not password:
            flash('Username and password are required', category='danger')
            return render_template("login.html", user=current_user, entered_username=entered_username)
        if user and user.lockout_until and to_utc(user.lockout_until) > utc_now():
            flash('Account locked after too many failed attempts. Try again later.', category='danger')
            return render_template("login.html", user=current_user, entered_username=entered_username)

        if user:
            if check_password_hash(user.password, password):
                user.failed_login_attempts = 0
                user.lockout_until = None
                db.session.commit()
                flash('Login successful', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.failed_login_attempts = 0
                    user.lockout_until = utc_now() + timedelta(minutes=LOCKOUT_MINUTES)
                    db.session.commit()
                    flash('Account locked after too many failed attempts. Try again later.', category='danger')
                else:
                    db.session.commit()
                    flash('Invalid username or password', category='danger')
        else:
            flash('Invalid username or password', category='danger')
    return render_template("login.html", user=current_user, entered_username=entered_username)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    # Signup route: handles new user registration and validation
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        first_name = str(request.form.get('first_name')).strip()
        password = request.form.get('password')
        passwordConfirm = request.form.get('passwordConfirm')
        role = str(request.form.get('role')).strip()
        department_name = str(request.form.get('department_name')).strip()
        resolved_department_id = None
        # Form validation
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', category='danger')
        elif not username:
            flash('Username is required', category='danger')
        elif len(username) < 6:
            flash('Username must be at least 6 characters long', category='danger')
        elif not password:
            flash('Password is required', category='danger')
        elif len(password) < 12:
            flash('Password must be at least 12 characters long', category='danger')
        elif not passwordConfirm:
            flash('Password confirmation is required', category='danger')
        elif password != passwordConfirm:
            flash('Passwords must match', category='danger')
        elif not role or role == "None":
            flash('Role is required', category='danger')
        else:
            if department_name:
                selected_department = Department.query.filter_by(name=department_name).first()
                if not selected_department:
                    flash('Selected department is invalid', category='danger')
                    return render_template("signup.html", user=current_user)
                resolved_department_id = selected_department.id

            password_policy_error = validate_password_policy(password, username)
            if password_policy_error:
                flash(password_policy_error, category='danger')
                return render_template("signup.html", user=current_user)
            # Creates new user and adds to database
            new_user = User(
                username=username,
                first_name=first_name,
                password=generate_password_hash(password),
                role=role,
                department_id=resolved_department_id,
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created successfully', category='success')
            return redirect(url_for('views.home'))
    return render_template("signup.html", user=current_user)

@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    # Logout route: logs out the current user
    logout_user()
    flash('You have been logged out', category='success')
    return redirect(url_for('auth.login'))