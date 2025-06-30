from flask import Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        userName = request.form.get('userName')
        firstName = request.form.get('firstName')
        password = request.form.get('password')
        passwordConfirm = request.form.get('passwordConfirm')
        role = request.form.get('role')
        departmentId = request.form.get('departmentId')

    
    # Form validation
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', category='e')
        elif len(userName) < 6:
            flash('Username must be at least 6 characters long.', category='e')
        elif password != passwordConfirm:
            flash('Passwords must match.', category='e')
        else:
            flash('Account created successfully', category='s')

    return render_template("signup.html")

@auth.route('/logout', methods=[''])
def logout():
    return render_template("logout.html")