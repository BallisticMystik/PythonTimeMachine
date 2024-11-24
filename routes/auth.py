from flask import render_template, request, redirect, url_for, flash, jsonify
from app_init import app, db
from models import User
from forms import LoginForm, RegistrationForm
from sqlalchemy.exc import IntegrityError

@app.route('/')
@app.route('/home')
def home_route():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            print(f"Login status: Success for user {user.username}")
            for field in ['username', 'password']:
                print(f"Login {field}: {getattr(form, field).data}")
            # Always redirect to dashboard after successful login
            return redirect(url_for('dashboard'))
        else:
            print(f"Login status: Failed for username {form.username.data}")
            flash('Invalid username or password')
    return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            print(f"Registration status: Success for user {user.username}")
            for field in ['username', 'email', 'password', 'confirm_password']:
                print(f"Registration {field}: {getattr(form, field).data}")
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard after successful registration
        except IntegrityError:
            db.session.rollback()
            print(f"Registration status: Failed (IntegrityError) for username {form.username.data}")
            flash('Username or email already exists. Please choose a different one.', 'error')
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    # TODO: Implement logout logic
    return redirect(url_for('login'))

@app.route('/connect_wallet', methods=['POST'])
def connect_wallet():
    data = request.json
    wallet_address = data.get('wallet_address')
    if wallet_address:
        # TODO: Implement wallet connection logic
        return jsonify({'message': 'Wallet connected successfully'}), 200
    else:
        return jsonify({'error': 'No wallet address provided'}), 400