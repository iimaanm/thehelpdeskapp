from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

# Blueprint for authentication routes (login, signup, logout)
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Login route: handles user authentication
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        # Validation and authentication logic
        if not username or not password:
            flash('Username and password are required', category='danger')
            return render_template("login.html")
        if user:
            if check_password_hash(user.password, password):
                flash('Login successful', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again', category='danger')
        else:
            flash('User not found, please sign up', category='danger')
    return render_template("login.html", user=current_user)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    # Signup route: handles new user registration and validation
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        first_name = str(request.form.get('first_name')).strip()
        password = request.form.get('password')
        passwordConfirm = request.form.get('passwordConfirm')
        role = str(request.form.get('role')).strip()
        departmentId = str(request.form.get('departmentId')).strip()
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
        elif len(password) < 6:
            flash('Password must be at least 6 characters long', category='danger')
        elif not passwordConfirm:
            flash('Password confirmation is required', category='danger')
        elif password != passwordConfirm:
            flash('Passwords must match', category='danger')
        elif role == "None":
            flash('Role is required', category='danger')
        else:
            # Create new user and add to database
            new_user = User(username=username, first_name=first_name, password=generate_password_hash(password), role=role, department_id=departmentId)
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