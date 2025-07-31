from . import db
from datetime import datetime


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    # Email preferences
    email_notifications = db.Column(db.Boolean, default=True)
    weekly_reports = db.Column(db.Boolean, default=True)
    brand_alerts = db.Column(db.Boolean, default=True)

    # Dashboard preferences
    dashboard_layout = db.Column(db.String(20), default='default')
    items_per_page = db.Column(db.Integer, default=20)

    # Theme preferences
    theme = db.Column(db.String(10), default='light')  # light, dark

    # Timezone
    timezone = db.Column(db.String(50), default='UTC')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_notifications': self.email_notifications,
            'weekly_reports': self.weekly_reports,
            'brand_alerts': self.brand_alerts,
            'dashboard_layout': self.dashboard_layout,
            'items_per_page': self.items_per_page,
            'theme': self.theme,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }