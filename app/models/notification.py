from . import db
from datetime import datetime


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # info, success, warning, error
    category = db.Column(db.String(50))  # brand_alert, system, competitor, analysis
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500))  # Optional URL for action button
    action_text = db.Column(db.String(100))  # Text for action button
    metadata = db.Column(db.JSON)  # Additional data (brand_id, query_id, etc.)
    expires_at = db.Column(db.DateTime)  # Optional expiry
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref='notifications')

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'category': self.category,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Notification Preferences
    email_notifications = db.Column(db.Boolean, default=True)
    brand_alerts = db.Column(db.Boolean, default=True)
    competitor_alerts = db.Column(db.Boolean, default=True)
    system_notifications = db.Column(db.Boolean, default=True)
    weekly_reports = db.Column(db.Boolean, default=True)

    # Display Preferences
    theme = db.Column(db.String(20), default='light')  # light, dark
    timezone = db.Column(db.String(50), default='UTC')
    date_format = db.Column(db.String(20), default='MM/DD/YYYY')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='preferences', uselist=False)