from app.models import db
from datetime import datetime

class AIOverview(db.Model):
    __tablename__ = 'ai_overviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    search_query = db.Column(db.String(500), nullable=False)  # Changed from 'query' to 'search_query'
    overview_text = db.Column(db.Text, nullable=False)
    sources_used = db.Column(db.JSON)  # List of source URLs and titles
    search_results = db.Column(db.JSON)  # Original search results
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processing_time = db.Column(db.Float)  # Time taken to generate

    def to_dict(self):
        return {
            'id': self.id,
            'query': self.search_query,  # Return as 'query' for API compatibility
            'overview_text': self.overview_text,
            'sources_used': self.sources_used or [],
            'search_results': self.search_results or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processing_time': self.processing_time
        }

class SearchCache(db.Model):
    __tablename__ = 'search_cache'

    id = db.Column(db.Integer, primary_key=True)
    query_hash = db.Column(db.String(64), unique=True, nullable=False)
    search_query = db.Column(db.String(500), nullable=False)  # Changed from 'query' to 'search_query'
    results = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)