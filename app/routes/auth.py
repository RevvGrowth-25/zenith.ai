from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.services.activity_logger import ActivityLogger
import re

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')

            login_user(user)
            user.update_last_login()

            # Log the login activity
            try:
                ActivityLogger.log_login(user.id)
            except:
                pass  # Don't break login if logging fails

            # Redirect to admin if user is admin
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            username = request.form.get('username', '').strip()
            company = request.form.get('company', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            # Validation
            errors = []

            # Required fields
            if not first_name:
                errors.append('First name is required')
            if not last_name:
                errors.append('Last name is required')
            if not email:
                errors.append('Email is required')
            if not username:
                errors.append('Username is required')
            if not password:
                errors.append('Password is required')

            # Email validation
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append('Please enter a valid email address')

            # Password validation
            if password:
                if len(password) < 6:
                    errors.append('Password must be at least 6 characters long')
                if password != confirm_password:
                    errors.append('Passwords do not match')

            # Username validation
            if username:
                if len(username) < 3:
                    errors.append('Username must be at least 3 characters long')
                if not re.match(r'^[a-zA-Z0-9_]+$', username):
                    errors.append('Username can only contain letters, numbers, and underscores')

            # Check if user already exists
            if email:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    errors.append('An account with this email already exists')

            if username:
                existing_username = User.query.filter_by(username=username).first()
                if existing_username:
                    errors.append('This username is already taken')

            # If there are errors, show them
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('auth/register.html')

            # Create new user
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                company=company,
                role='user',
                is_active=True
            )
            new_user.set_password(password)

            # Save to database
            db.session.add(new_user)
            db.session.commit()

            # Log the registration activity
            try:
                ActivityLogger.log_registration(new_user.id)
            except:
                pass  # Don't break registration if logging fails

            # Log the user in automatically
            login_user(new_user)
            new_user.update_last_login()

            flash('Account created successfully! Welcome to Zenith.ai!', 'success')
            return redirect(url_for('dashboard.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating your account: {str(e)}', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    try:
        ActivityLogger.log_logout(current_user.id)
    except:
        pass  # Don't break logout if logging fails

    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# API endpoint for AJAX registration (for modal)
@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()

        # Get form data
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        company = data.get('company', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # Validation
        errors = []

        # Required fields
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        if not email:
            errors.append('Email is required')
        if not username:
            errors.append('Username is required')
        if not password:
            errors.append('Password is required')

        # Email validation
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address')

        # Password validation
        if password:
            if len(password) < 6:
                errors.append('Password must be at least 6 characters long')
            if password != confirm_password:
                errors.append('Passwords do not match')

        # Username validation
        if username:
            if len(username) < 3:
                errors.append('Username must be at least 3 characters long')
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                errors.append('Username can only contain letters, numbers, and underscores')

        # Check if user already exists
        if email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('An account with this email already exists')

        if username:
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                errors.append('This username is already taken')

        # If there are errors, return them
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400

        # Create new user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            company=company,
            role='user',
            is_active=True
        )
        new_user.set_password(password)

        # Save to database
        db.session.add(new_user)
        db.session.commit()

        # Log the registration activity
        try:
            ActivityLogger.log_registration(new_user.id)
        except:
            pass

        return jsonify({
            'success': True,
            'message': 'Account created successfully!',
            'user_id': new_user.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'errors': [f'An error occurred while creating your account: {str(e)}']
        }), 500


# Check if email/username is available
@auth_bp.route('/api/check-availability', methods=['POST'])
def check_availability():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()

        result = {
            'email_available': True,
            'username_available': True
        }

        if email:
            existing_user = User.query.filter_by(email=email).first()
            result['email_available'] = not existing_user

        if username:
            existing_username = User.query.filter_by(username=username).first()
            result['username_available'] = not existing_username

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500