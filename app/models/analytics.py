from . import db
from datetime import datetime


class AnalyticsData(db.Model):
    __tablename__ = 'analytics_data'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    ai_platform = db.Column(db.String(50), nullable=False)

    # Visibility Metrics
    total_mentions = db.Column(db.Integer, default=0)
    direct_mentions = db.Column(db.Integer, default=0)
    indirect_mentions = db.Column(db.Integer, default=0)
    citation_count = db.Column(db.Integer, default=0)
    visibility_score = db.Column(db.Float, default=0.0)

    # Sentiment Metrics
    positive_sentiment = db.Column(db.Integer, default=0)
    negative_sentiment = db.Column(db.Integer, default=0)
    neutral_sentiment = db.Column(db.Integer, default=0)
    avg_sentiment_score = db.Column(db.Float, default=0.0)

    # Performance Metrics
    avg_position = db.Column(db.Float)
    top_3_mentions = db.Column(db.Integer, default=0)
    share_of_voice = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('brand_id', 'date', 'ai_platform'),)


class CompetitorData(db.Model):
    __tablename__ = 'competitor_data'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    competitor_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    ai_platform = db.Column(db.String(50), nullable=False)

    mentions = db.Column(db.Integer, default=0)
    visibility_score = db.Column(db.Float, default=0.0)
    avg_sentiment = db.Column(db.Float, default=0.0)
    market_share = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)