from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # user, admin, manager
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    brands = db.relationship('Brand', backref='owner', lazy=True)
    # activities = db.relationship('UserActivity', backref='user', lazy=True)
    ai_overviews = db.relationship('AIOverview', backref='user', lazy=True)
    preferences = db.relationship('UserPreference', backref='user', uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_manager(self):
        """Check if user is manager or admin"""
        return self.role in ['admin', 'manager']

    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def get_login_count(self):
        """Get login count from activity logs"""
        try:
            return len([a for a in self.activities if a.activity_type == 'login'])
        except Exception:
            return 0

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_preferences(self):
        """Get or create user preferences"""
        if self.preferences:
            return self.preferences

        # Create default preferences if they don't exist
        from app.models.user_preference import UserPreference
        preferences = UserPreference(user_id=self.id)
        db.session.add(preferences)
        db.session.commit()
        return preferences

    def get_recent_activities(self, limit=10):
        """Get user's recent activities"""
        try:
            return sorted(self.activities, key=lambda x: x.timestamp, reverse=True)[:limit]
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'company': self.company,
            'role': self.role,
            'is_active': self.is_active,
            'login_count': self.get_login_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }