from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

settings_bp = Blueprint('profile', __name__)

@settings_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        return render_template('profile/profile.html')
    except Exception as e:
        # Fallback to simple HTML if template fails
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Profile</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 p-8">
            <div class="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
                <h1 class="text-2xl font-bold mb-4">Profile</h1>
                <div class="space-y-2">
                    <p><strong>Username:</strong> {current_user.username}</p>
                    <p><strong>Email:</strong> {current_user.email}</p>
                    <p><strong>Name:</strong> {current_user.first_name} {current_user.last_name}</p>
                    <p><strong>Company:</strong> {current_user.company or 'Not specified'}</p>
                    <p><strong>Role:</strong> {current_user.role}</p>
                </div>
                <div class="mt-6">
                    <a href="/" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        Back to Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

@settings_bp.route('/account')
@login_required
def account():
    """Account profile"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Account Settings</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
            <h1 class="text-2xl font-bold mb-4">Account Settings</h1>
            <p>Account profile page - Coming soon!</p>
            <div class="mt-6">
                <a href="/profile/profile" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Back to Profile
                </a>
            </div>
        </div>
    </body>
    </html>
    """

@settings_bp.route('/test')
@login_required
def test():
    """Test route"""
    return {
        'message': 'Settings blueprint is working!',
        'user': current_user.username,
        'email': current_user.email
    }