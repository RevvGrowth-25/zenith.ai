from . import db
from datetime import datetime


class SearchQuery(db.Model):
    __tablename__ = 'search_queries'

    id = db.Column(db.Integer, primary_key=True)
    query_text = db.Column(db.String(500), nullable=False)
    ai_platform = db.Column(db.String(50), nullable=False)  # chatgpt, claude, perplexity, google_ai
    response_text = db.Column(db.Text)
    citations = db.Column(db.JSON)  # List of cited sources
    brand_mentions = db.Column(db.JSON)  # Brands mentioned in response
    sentiment_score = db.Column(db.Float)  # -1 to 1
    relevance_score = db.Column(db.Float)  # 0 to 1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    results = db.relationship('SearchResult', backref='query', lazy=True)


class SearchResult(db.Model):
    __tablename__ = 'search_results'

    id = db.Column(db.Integer, primary_key=True)
    search_query_id = db.Column(db.Integer, db.ForeignKey('search_queries.id'), nullable=False)
    brand_query_id = db.Column(db.Integer, db.ForeignKey('brand_queries.id'))
    position = db.Column(db.Integer)  # Position in AI response
    mention_type = db.Column(db.String(50))  # direct, indirect, citation
    context = db.Column(db.Text)  # Surrounding context of mention
    sentiment = db.Column(db.String(20))  # positive, negative, neutral
    confidence_score = db.Column(db.Float)  # 0 to 1
    url_cited = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)