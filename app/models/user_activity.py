from . import db
from datetime import datetime


class UserActivity(db.Model):
    __tablename__ = 'user_activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    extra_data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = db.relationship('User', backref='activities')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'extra_data': self.extra_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_name': self.user.get_full_name() if self.user else 'Unknown User'
        }