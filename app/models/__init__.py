from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Import models in order (to avoid circular imports)
from .user import User
from .user_preference import UserPreference
from .user_activity import UserActivity
from .brand import Brand, BrandQuery
from .search_query import SearchQuery, SearchResult
from .analytics import AnalyticsData, CompetitorData
from .ai_overview import AIOverview, SearchCache