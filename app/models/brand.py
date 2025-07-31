from . import db
from datetime import datetime


class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(255))
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    keywords = db.Column(db.JSON)  # List of keywords to track
    competitors = db.Column(db.JSON)  # List of competitor brands
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    queries = db.relationship('BrandQuery', backref='brand', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('AnalyticsData', backref='brand', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'description': self.description,
            'industry': self.industry,
            'keywords': self.keywords or [],
            'competitors': self.competitors or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BrandQuery(db.Model):
    __tablename__ = 'brand_queries'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    query_text = db.Column(db.String(500), nullable=False)
    query_type = db.Column(db.String(50))  # informational, commercial, navigational
    priority = db.Column(db.Integer, default=1)  # 1-5 priority scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    search_results = db.relationship('SearchResult', backref='brand_query', lazy=True)