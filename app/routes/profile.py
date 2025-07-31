from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db
from app.services.activity_logger import ActivityLogger

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile/profile.html', user=current_user)


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            company = request.form.get('company', '').strip()
            username = request.form.get('username', '').strip()

            # Validate required fields
            if not first_name or not last_name or not username:
                flash('First name, last name, and username are required.', 'error')
                return render_template('profile/edit_profile.html', user=current_user)

            # Check if username is already taken by another user
            from app.models.user import User
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Username already taken. Please choose a different one.', 'error')
                return render_template('profile/edit_profile.html', user=current_user)

            # Update user profile
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.company = company
            current_user.username = username

            db.session.commit()

            # Log activity
            ActivityLogger.log_activity(
                user_id=current_user.id,
                activity_type='profile_update',
                description='Updated profile information'
            )

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return render_template('profile/edit_profile.html', user=current_user)

    return render_template('profile/edit_profile.html', user=current_user)


@profile_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('profile/change_password.html')

            # Validate new password
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'error')
                return render_template('profile/change_password.html')

            # Check password confirmation
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('profile/change_password.html')

            # Update password
            current_user.set_password(new_password)
            db.session.commit()

            # Log activity
            ActivityLogger.log_activity(
                user_id=current_user.id,
                activity_type='password_change',
                description='Changed account password'
            )

            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {str(e)}', 'error')

    return render_template('profile/change_password.html')


@profile_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    preferences = current_user.get_preferences()
    return render_template('profile/settings.html', preferences=preferences)


@profile_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update user settings"""
    try:
        preferences = current_user.get_preferences()

        # Update preferences
        preferences.email_notifications = request.form.get('email_notifications') == 'on'
        preferences.weekly_reports = request.form.get('weekly_reports') == 'on'
        preferences.brand_alerts = request.form.get('brand_alerts') == 'on'
        preferences.dashboard_layout = request.form.get('dashboard_layout', 'default')
        preferences.items_per_page = int(request.form.get('items_per_page', 20))
        preferences.theme = request.form.get('theme', 'light')
        preferences.timezone = request.form.get('timezone', 'UTC')

        db.session.commit()

        # Log activity
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='settings_update',
            description='Updated account settings'
        )

        flash('Settings updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', 'error')

    return redirect(url_for('profile.settings'))


@profile_bp.route('/api/profile/activity')
@login_required
def get_user_activity():
    """Get user activity data for profile"""
    try:
        activities = current_user.get_recent_activities(limit=20)
        return jsonify({
            'success': True,
            'activities': [activity.to_dict() for activity in activities]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500