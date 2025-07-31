from app.models import db, Notification, User
from datetime import datetime, timedelta
from typing import List, Optional


class NotificationService:

    @staticmethod
    def create_notification(user_id: int, title: str, message: str,
                            notification_type: str = 'info',
                            category: str = None,
                            action_url: str = None,
                            action_text: str = None,
                            metadata: dict = None,
                            expires_at: datetime = None):
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            action_url=action_url,
            action_text=action_text,
            metadata=metadata,
            expires_at=expires_at
        )

        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def create_brand_alert(user_id: int, brand_name: str, alert_type: str, details: str):
        """Create brand-specific alert"""
        return NotificationService.create_notification(
            user_id=user_id,
            title=f"Brand Alert: {brand_name}",
            message=f"{alert_type}: {details}",
            notification_type='warning',
            category='brand_alert',
            action_url=f"/dashboard/brands",
            action_text="View Brands"
        )

    @staticmethod
    def create_competitor_alert(user_id: int, competitor_name: str, message: str):
        """Create competitor alert"""
        return NotificationService.create_notification(
            user_id=user_id,
            title=f"Competitor Update: {competitor_name}",
            message=message,
            notification_type='info',
            category='competitor',
            action_url="/analytics/competitors",
            action_text="View Analysis"
        )

    @staticmethod
    def create_system_notification(title: str, message: str,
                                   notification_type: str = 'info',
                                   target_users: List[int] = None):
        """Create system-wide notification"""
        if target_users is None:
            # Send to all users
            users = User.query.filter_by(is_active=True).all()
            target_users = [user.id for user in users]

        notifications = []
        for user_id in target_users:
            notification = NotificationService.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                category='system'
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int):
        """Mark notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if notification:
            notification.mark_as_read()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id: int):
        """Mark all notifications as read for user"""
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True, 'read_at': datetime.utcnow()})

        db.session.commit()

    @staticmethod
    def delete_notification(notification_id: int, user_id: int):
        """Delete notification"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False

    @staticmethod
    def cleanup_expired_notifications():
        """Clean up expired notifications"""
        expired = Notification.query.filter(
            Notification.expires_at < datetime.utcnow()
        ).all()

        for notification in expired:
            db.session.delete(notification)

        db.session.commit()
        return len(expired)