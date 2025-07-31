from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Notification
from app.services.notification_service import NotificationService

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    """Notifications page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    notifications = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/api/notifications')
@login_required
def api_notifications():
    """API endpoint for notifications"""
    limit = request.args.get('limit', 10, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = Notification.query.filter_by(user_id=current_user.id)

    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': current_user.get_unread_notifications_count()
    })


@notifications_bp.route('/api/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    success = NotificationService.mark_as_read(notification_id, current_user.id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Notification not found'}), 404


@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    NotificationService.mark_all_as_read(current_user.id)
    return jsonify({'success': True})


@notifications_bp.route('/api/delete/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete notification"""
    success = NotificationService.delete_notification(notification_id, current_user.id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Notification not found'}), 404