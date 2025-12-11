"""
Authentication Routes
Handles user registration, login, and logout
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint"""
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check for duplicate username
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists. Please choose a different one.')
        
        # Check for duplicate email
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered. Please use a different email.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', username=username, email=email)
        
        # Create new user
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html', username=username, email=email)
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html', username=username)
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Update online status
            user.is_online = True
            user.last_seen = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember)
            flash(f'Welcome back, {username}!', 'success')
            
            # Redirect to requested page or chat
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('chat.index'))
        else:
            flash('Invalid username or password.', 'error')
            return render_template('login.html', username=username)
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout endpoint"""
    # Update online status
    if current_user.is_authenticated:
        current_user.is_online = False
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

