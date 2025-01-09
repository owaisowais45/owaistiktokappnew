from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from okii import mongo
from okii.models import User
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Check if email format is valid"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """Check if username is valid (alphanumeric and underscore only)"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def is_strong_password(password):
    """Check if password meets minimum requirements"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):  
        return False
    if not re.search(r'[a-z]', password):  
        return False
    if not re.search(r'\d', password):      
        return False
    return True

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role', 'consumer')  # Get role from form

            if role not in ['creator', 'consumer']:
                flash('Invalid role selected.', 'error')
                return render_template('auth/signup.html')
            
            if not all([username, email, password, confirm_password]):
                flash('All fields are required.', 'error')
                return render_template('auth/signup.html')

            
            if not is_valid_email(email):
                flash('Please enter a valid email address.', 'error')
                return render_template('auth/signup.html')

            
            if not is_valid_username(username):
                flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores.', 'error')
                return render_template('auth/signup.html')

            
            if not is_strong_password(password):
                flash('Password must be at least 8 characters long and contain uppercase, lowercase, and numbers.', 'error')
                return render_template('auth/signup.html')

            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('auth/signup.html')
            
            

            
            existing_user = mongo.db.users.find_one({
                "$or": [
                    {"email": email},
                    {"username": username}
                ]
            })

            if existing_user:
                if existing_user.get('email') == email:
                    flash('Email already registered.', 'error')
                else:
                    flash('Username already taken.', 'error')
                return render_template('auth/signup.html')

            
            now = datetime.utcnow()
            new_user = {
                "username": username,
                "email": email,
                "password": generate_password_hash(password),
                "role": role,
                "created_at": now,
                "last_login": now,
                "avatar": None,
                "bio": "",
                "followers": [],
                "following": [],
                "is_active": True,
                "is_admin": False
            }

            
            result = mongo.db.users.insert_one(new_user)
            
            if result.inserted_id:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Please try again.', 'error')

        except Exception as e:
            print(f"Error in signup: {e}")
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password')
            remember = request.form.get('remember', False) == 'on'

            if not email or not password:
                flash('Please enter both email and password.', 'error')
                return render_template('auth/login.html')

            
            print(f"Attempting login for email: {email}")

            
            user_data = mongo.db.users.find_one({'email': email})
            
            if user_data and check_password_hash(user_data['password'], password):
                try:
                    user = User(user_data)
                    if not user.is_active:
                        flash('Your account has been deactivated.', 'error')
                        return render_template('auth/login.html')

                    
                    mongo.db.users.update_one(
                        {'_id': user_data['_id']},
                        {'$set': {'last_login': datetime.utcnow()}}
                    )

                    
                    login_user(user, remember=remember)
                    
                    
                    print(f"Login successful for user: {user.username}")

                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        return redirect(next_page)
                    return redirect(url_for('main.index'))
                except Exception as e:
                    print(f"Error creating user object: {e}")
                    flash('An error occurred during login.', 'error')
            else:
                print("Invalid credentials")
                flash('Invalid email or password.', 'error')

        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))