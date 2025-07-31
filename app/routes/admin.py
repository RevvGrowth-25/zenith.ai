from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.models import db, User, Brand, UserActivity, AnalyticsData
from app.services.activity_logger import ActivityLogger
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
import json

admin_bp = Blueprint('admin', __name__)
from functools import wraps


def admin_required(f):
    """Decorator to require admin access"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview statistics"""
    # Get basic statistics
    stats = get_admin_stats()

    # Get recent activities
    recent_activities = UserActivity.query.order_by(desc(UserActivity.timestamp)).limit(10).all()

    # Get user growth data for chart
    user_growth = get_user_growth_data()

    # Get brand creation data
    brand_growth = get_brand_growth_data()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_activities=recent_activities,
                           user_growth=user_growth,
                           brand_growth=brand_growth)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search),
                User.username.contains(search)
            )
        )

    if role_filter:
        query = query.filter(User.role == role_filter)

    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('admin/users.html', users=users, search=search, role_filter=role_filter)


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Detailed user view"""
    user = User.query.get_or_404(user_id)

    # Get user's brands
    brands = Brand.query.filter_by(user_id=user_id).all()

    # Get user's recent activities
    activities = UserActivity.query.filter_by(user_id=user_id) \
        .order_by(desc(UserActivity.timestamp)).limit(50).all()

    # Get user's login statistics
    login_stats = get_user_login_stats(user_id)

    return render_template('admin/user_detail.html',
                           user=user,
                           brands=brands,
                           activities=activities,
                           login_stats=login_stats)


@admin_bp.route('/brands')
@login_required
@admin_required
def brands():
    """Brand management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    industry_filter = request.args.get('industry', '')

    query = db.session.query(Brand).join(User)

    if search:
        query = query.filter(
            db.or_(
                Brand.name.contains(search),
                Brand.domain.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )

    if industry_filter:
        query = query.filter(Brand.industry == industry_filter)

    brands = query.order_by(desc(Brand.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )

    # Get industries for filter
    industries = db.session.query(Brand.industry).distinct().filter(Brand.industry.isnot(None)).all()
    industries = [i[0] for i in industries if i[0]]

    return render_template('admin/brands.html',
                           brands=brands,
                           search=search,
                           industry_filter=industry_filter,
                           industries=industries)


@admin_bp.route('/activities')
@login_required
@admin_required
def activities():
    """User activity logs"""
    page = request.args.get('page', 1, type=int)
    activity_type = request.args.get('type', '')
    user_id = request.args.get('user_id', type=int)

    query = db.session.query(UserActivity).join(User)

    if activity_type:
        query = query.filter(UserActivity.activity_type == activity_type)

    if user_id:
        query = query.filter(UserActivity.user_id == user_id)

    activities = query.order_by(desc(UserActivity.timestamp)).paginate(
        page=page, per_page=50, error_out=False
    )

    # Get activity types for filter
    activity_types = db.session.query(UserActivity.activity_type).distinct().all()
    activity_types = [a[0] for a in activity_types]

    # Get users for filter
    users = User.query.order_by(User.first_name, User.last_name).all()

    return render_template('admin/activities.html',
                           activities=activities,
                           activity_types=activity_types,
                           users=users,
                           selected_type=activity_type,
                           selected_user_id=user_id)


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Admin analytics page"""
    # Get various analytics data
    user_analytics = get_user_analytics()
    brand_analytics = get_brand_analytics()
    activity_analytics = get_activity_analytics()

    return render_template('admin/analytics.html',
                           user_analytics=user_analytics,
                           brand_analytics=brand_analytics,
                           activity_analytics=activity_analytics)


# API Routes for Admin
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for admin statistics"""
    stats = get_admin_stats()
    return jsonify(stats)


@admin_bp.route('/api/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400

    user.is_active = not user.is_active
    db.session.commit()

    # Log the activity
    ActivityLogger.log_activity(
        user_id=current_user.id,
        activity_type='user_status_changed',
        description=f'{"Activated" if user.is_active else "Deactivated"} user {user.username}',
        extra_data={'target_user_id': user.id, 'new_status': user.is_active}
    )

    return jsonify({'success': True, 'is_active': user.is_active})


@admin_bp.route('/api/user/<int:user_id>/change-role', methods=['POST'])
@login_required
@admin_required
def change_user_role(user_id):
    """Change user role"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_role = data.get('role')

    if new_role not in ['user', 'admin', 'manager']:
        return jsonify({'error': 'Invalid role'}), 400

    if user.id == current_user.id and new_role != 'admin':
        return jsonify({'error': 'Cannot change your own admin role'}), 400

    old_role = user.role
    user.role = new_role
    db.session.commit()

    # Log the activity
    ActivityLogger.log_activity(
        user_id=current_user.id,
        activity_type='user_role_changed',
        description=f'Changed user {user.username} role from {old_role} to {new_role}',
        extra_data={'target_user_id': user.id, 'old_role': old_role, 'new_role': new_role}
    )

    return jsonify({'success': True, 'role': user.role})


@admin_bp.route('/api/brand/<int:brand_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_brand_admin(brand_id):
    """Admin delete brand"""
    brand = Brand.query.get_or_404(brand_id)
    brand_name = brand.name
    owner_id = brand.user_id

    try:
        db.session.delete(brand)
        db.session.commit()

        # Log the activity
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='brand_deleted_by_admin',
            description=f'Admin deleted brand "{brand_name}"',
            extra_data={'brand_id': brand_id, 'brand_name': brand_name, 'owner_id': owner_id}
        )

        return jsonify({'success': True, 'message': 'Brand deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Helper functions
def get_admin_stats():
    """Get basic admin statistics"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    total_brands = Brand.query.count()
    active_brands = Brand.query.filter_by(is_active=True).count()

    # Recent registrations (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    recent_brands = Brand.query.filter(Brand.created_at >= thirty_days_ago).count()

    # Login activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_logins = UserActivity.query.filter(
        and_(UserActivity.activity_type == 'login', UserActivity.timestamp >= seven_days_ago)
    ).count()

    # AI Overview stats (if you have the model)
    try:
        from app.models.ai_overview import AIOverview
        total_overviews = AIOverview.query.count()
        recent_overviews = AIOverview.query.filter(AIOverview.created_at >= seven_days_ago).count()

        # Average response time
        avg_response_time = db.session.query(func.avg(AIOverview.processing_time)).scalar() or 0
    except ImportError:
        total_overviews = 0
        recent_overviews = 0
        avg_response_time = 0

    # Search queries stats
    try:
        from app.models.search_query import SearchQuery
        total_queries = SearchQuery.query.count()
    except ImportError:
        total_queries = 0

    return {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'total_brands': total_brands,
        'active_brands': active_brands,
        'recent_users': recent_users,
        'recent_brands': recent_brands,
        'recent_logins': recent_logins,
        'total_overviews': total_overviews,
        'recent_overviews': recent_overviews,
        'total_queries': total_queries,
        'avg_response_time': avg_response_time
    }


def get_user_growth_data(days=30):
    """Get user growth data for charts"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Get daily user registrations
    daily_users = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_date
    ).group_by(func.date(User.created_at)).all()

    # Fill missing dates with 0
    result = []
    current_date = start_date
    user_dict = {str(row.date): row.count for row in daily_users}

    while current_date <= end_date:
        result.append({
            'date': current_date.isoformat(),
            'count': user_dict.get(str(current_date), 0)
        })
        current_date += timedelta(days=1)

    return result


def get_brand_growth_data(days=30):
    """Get brand creation data for charts"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Get daily brand creations
    daily_brands = db.session.query(
        func.date(Brand.created_at).label('date'),
        func.count(Brand.id).label('count')
    ).filter(
        Brand.created_at >= start_date
    ).group_by(func.date(Brand.created_at)).all()

    # Fill missing dates with 0
    result = []
    current_date = start_date
    brand_dict = {str(row.date): row.count for row in daily_brands}

    while current_date <= end_date:
        result.append({
            'date': current_date.isoformat(),
            'count': brand_dict.get(str(current_date), 0)
        })
        current_date += timedelta(days=1)

    return result


def get_user_login_stats(user_id):
    """Get login statistics for a specific user"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    logins_7d = UserActivity.query.filter(
        and_(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'login',
            UserActivity.timestamp >= seven_days_ago
        )
    ).count()

    logins_30d = UserActivity.query.filter(
        and_(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'login',
            UserActivity.timestamp >= thirty_days_ago
        )
    ).count()

    return {
        'logins_7d': logins_7d,
        'logins_30d': logins_30d
    }


def get_user_analytics():
    """Get user analytics data"""
    # User distribution by role
    role_distribution = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()

    return {
        'role_distribution': [{'role': r.role, 'count': r.count} for r in role_distribution]
    }


def get_brand_analytics():
    """Get brand analytics data"""
    # Brands by industry
    industry_distribution = db.session.query(
        Brand.industry,
        func.count(Brand.id).label('count')
    ).filter(Brand.industry.isnot(None)).group_by(Brand.industry).all()

    return {
        'industry_distribution': [{'industry': r.industry, 'count': r.count} for r in industry_distribution]
    }


def get_activity_analytics():
    """Get user activity analytics"""
    # Activity types distribution
    activity_distribution = db.session.query(
        UserActivity.activity_type,
        func.count(UserActivity.id).label('count')
    ).group_by(UserActivity.activity_type).all()

    # Daily activity for last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_activity = db.session.query(
        func.date(UserActivity.timestamp).label('date'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.timestamp >= seven_days_ago
    ).group_by(func.date(UserActivity.timestamp)).all()

    return {
        'activity_types': [{'type': r.activity_type, 'count': r.count} for r in activity_distribution],
        'daily_activity': [{'date': str(r.date), 'count': r.count} for r in daily_activity]
    }
@admin_bp.route('/test-access')
@login_required
def test_access():
    """Test admin access - for debugging"""
    return jsonify({
        'user_id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'is_admin': current_user.is_admin(),
        'is_authenticated': current_user.is_authenticated
    })


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_form(user_id):
    """Delete user via form submission"""
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)

    try:
        # Store user info before deletion
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'brands_count': len(user.brands) if user.brands else 0,
            'activities_count': len(user.activities) if user.activities else 0
        }

        # Delete user (this will cascade delete related records)
        db.session.delete(user)
        db.session.commit()

        # Log the deletion activity
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='user_deleted',
            description=f'Deleted user {user_info["full_name"]} ({user_info["username"]})',
            extra_data=user_info
        )

        flash(f'User {user_info["full_name"]} has been deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')

    return redirect(url_for('admin.users'))



@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user_api(user_id):
    """Delete user via API"""
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400

    user = User.query.get_or_404(user_id)

    try:
        # Store user info before deletion
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'brands_count': len(user.brands),
            'activities_count': len(user.activities)
        }

        # Delete user (this will cascade delete related records)
        db.session.delete(user)
        db.session.commit()

        # Log the deletion activity
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='user_deleted',
            description=f'Deleted user {user_info["full_name"]} ({user_info["username"]})',
            extra_data=user_info
        )

        return jsonify({
            'success': True,
            'message': f'User {user_info["full_name"]} has been deleted successfully.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status_api(user_id):
    """Toggle user active status via API"""
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot deactivate your own account'}), 400

    user = User.query.get_or_404(user_id)

    try:
        old_status = user.is_active
        user.is_active = not user.is_active
        db.session.commit()

        # Log the activity
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='user_status_changed',
            description=f'{"Activated" if user.is_active else "Deactivated"} user {user.get_full_name()}',
            extra_data={
                'target_user_id': user.id,
                'old_status': old_status,
                'new_status': user.is_active
            }
        )

        return jsonify({
            'success': True,
            'is_active': user.is_active,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/users/<int:user_id>/password-reset', methods=['POST'])
@login_required
@admin_required
def send_password_reset_api(user_id):
    """Send password reset email via API"""
    user = User.query.get_or_404(user_id)

    try:
        # Generate a temporary password (in production, you'd send an email)
        import secrets
        import string

        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        user.set_password(temp_password)
        db.session.commit()

        # Log the activity
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='password_reset',
            description=f'Reset password for user {user.get_full_name()}',
            extra_data={'target_user_id': user.id}
        )

        # In production, you would send an email here
        # For now, we'll return the temporary password
        return jsonify({
            'success': True,
            'message': f'Password reset for {user.email}',
            'temp_password': temp_password  # Remove this in production
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/impersonate')
@login_required
@admin_required
def impersonate_user(user_id):
    """Impersonate a user (for debugging/support)"""
    if user_id == current_user.id:
        flash('You cannot impersonate yourself.', 'error')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)

    # Store original admin user ID in session
    from flask import session
    session['impersonating_user_id'] = user_id
    session['original_admin_id'] = current_user.id

    # Log the impersonation
    ActivityLogger.log_activity(
        user_id=current_user.id,
        activity_type='user_impersonation',
        description=f'Started impersonating user {user.get_full_name()}',
        extra_data={'target_user_id': user.id}
    )

    # In a real implementation, you'd switch the user session
    # For now, just redirect to user detail with a message
    flash(f'Impersonation started for user {user.get_full_name()}', 'info')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/bulk-actions', methods=['POST'])
@login_required
@admin_required
def bulk_user_actions():
    """Handle bulk user actions"""
    data = request.get_json()
    action = data.get('action')
    user_ids = data.get('user_ids', [])

    if not action or not user_ids:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    # Remove current user from bulk actions
    user_ids = [uid for uid in user_ids if uid != current_user.id]

    try:
        results = []

        if action == 'delete':
            for user_id in user_ids:
                user = User.query.get(user_id)
                if user:
                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'full_name': user.get_full_name()
                    }

                    db.session.delete(user)
                    results.append(f"Deleted {user_info['full_name']}")

                    # Log the deletion
                    ActivityLogger.log_activity(
                        user_id=current_user.id,
                        activity_type='user_bulk_deleted',
                        description=f'Bulk deleted user {user_info["full_name"]}',
                        extra_data=user_info
                    )

        elif action == 'activate':
            users = User.query.filter(User.id.in_(user_ids)).all()
            for user in users:
                user.is_active = True
                results.append(f"Activated {user.get_full_name()}")

        elif action == 'deactivate':
            users = User.query.filter(User.id.in_(user_ids)).all()
            for user in users:
                user.is_active = False
                results.append(f"Deactivated {user.get_full_name()}")

        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Bulk action completed: {len(results)} users processed',
            'results': results
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/brands/<int:brand_id>')
@login_required
@admin_required
def brand_detail(brand_id):
    """Detailed brand view"""
    brand = Brand.query.get_or_404(brand_id)
    return render_template('admin/brand_detail.html', brand=brand)
