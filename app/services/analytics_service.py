from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models import db, Brand, SearchQuery, SearchResult, AnalyticsData, CompetitorData


class AnalyticsService:
    @staticmethod
    def calculate_visibility_score(brand_id: int, ai_platform: str, date_range: int = 30) -> float:
        """Calculate brand visibility score for a specific platform"""
        # For now, return a dummy score
        return 0.0

    @staticmethod
    def get_brand_performance_trends(brand_id: int, days: int = 30) -> Dict:
        """Get brand performance trends over time"""
        # Return dummy data for now
        return {}

    @staticmethod
    def get_competitor_analysis(brand_id: int, ai_platform: str = None) -> Dict:
        """Get competitor analysis data"""
        # Return dummy data for now
        return {}

    @staticmethod
    def generate_optimization_recommendations(brand_id: int) -> List[Dict]:
        """Generate AI search optimization recommendations"""
        # Return dummy recommendations for now
        return [
            {
                'type': 'getting_started',
                'priority': 'high',
                'title': 'Welcome to AI Search Analytics',
                'description': 'Start by setting up your brand monitoring and keywords.',
                'action_items': [
                    'Add relevant keywords for your brand',
                    'Set up competitor tracking',
                    'Configure monitoring frequency'
                ]
            }
        ]

    @staticmethod
    def calculate_visibility_score(brand_id: int, ai_platform: str, date_range: int = 30) -> float:
        """Calculate brand visibility score for a specific platform"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=date_range)

        # Get all search results for the brand in the date range
        results = db.session.query(SearchResult).join(SearchQuery).filter(
            and_(
                SearchResult.brand_query_id.in_(
                    db.session.query(BrandQuery.id).filter(BrandQuery.brand_id == brand_id)
                ),
                SearchQuery.ai_platform == ai_platform,
                SearchQuery.created_at.between(start_date, end_date)
            )
        ).all()

        if not results:
            return 0.0

        # Calculate weighted score based on position and mention type
        total_score = 0
        max_possible_score = 0

        for result in results:
            # Position weight (higher positions get more weight)
            position_weight = 1.0 / (result.position or 1) if result.position else 0.5

            # Mention type weight
            mention_weights = {
                'direct': 1.0,
                'indirect': 0.7,
                'citation': 0.9
            }
            mention_weight = mention_weights.get(result.mention_type, 0.5)

            # Confidence weight
            confidence_weight = result.confidence_score or 0.5

            score = position_weight * mention_weight * confidence_weight
            total_score += score
            max_possible_score += 1.0  # Maximum possible score per result

        # Normalize to 0-100 scale
        if max_possible_score > 0:
            visibility_score = (total_score / max_possible_score) * 100
            return min(100.0, visibility_score)

        return 0.0

    @staticmethod
    def get_brand_performance_trends(brand_id: int, days: int = 30) -> Dict:
        """Get brand performance trends over time"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get analytics data for the date range
        analytics_data = db.session.query(AnalyticsData).filter(
            and_(
                AnalyticsData.brand_id == brand_id,
                AnalyticsData.date.between(start_date, end_date)
            )
        ).order_by(AnalyticsData.date.asc()).all()

        # Group by date and platform
        trends = {}
        for data in analytics_data:
            date_str = data.date.isoformat()
            if date_str not in trends:
                trends[date_str] = {}

            trends[date_str][data.ai_platform] = {
                'visibility_score': data.visibility_score,
                'total_mentions': data.total_mentions,
                'avg_sentiment': data.avg_sentiment_score,
                'share_of_voice': data.share_of_voice
            }

        return trends

    @staticmethod
    def get_competitor_analysis(brand_id: int, ai_platform: str = None) -> Dict:
        """Get competitor analysis data"""
        brand = Brand.query.get(brand_id)
        if not brand or not brand.competitors:
            return {}

        query = db.session.query(CompetitorData).filter(
            and_(
                CompetitorData.brand_id == brand_id,
                CompetitorData.competitor_name.in_(brand.competitors)
            )
        )

        if ai_platform:
            query = query.filter(CompetitorData.ai_platform == ai_platform)

        # Get recent data (last 7 days)
        recent_date = datetime.now().date() - timedelta(days=7)
        competitor_data = query.filter(CompetitorData.date >= recent_date).all()

        # Aggregate competitor metrics
        competitor_metrics = {}
        for data in competitor_data:
            comp_name = data.competitor_name
            if comp_name not in competitor_metrics:
                competitor_metrics[comp_name] = {
                    'total_mentions': 0,
                    'avg_visibility': 0,
                    'avg_sentiment': 0,
                    'platforms': set()
                }

            competitor_metrics[comp_name]['total_mentions'] += data.mentions
            competitor_metrics[comp_name]['avg_visibility'] += data.visibility_score
            competitor_metrics[comp_name]['avg_sentiment'] += data.avg_sentiment
            competitor_metrics[comp_name]['platforms'].add(data.ai_platform)

        # Calculate averages
        for comp_name, metrics in competitor_metrics.items():
            platform_count = len(metrics['platforms'])
            if platform_count > 0:
                metrics['avg_visibility'] /= platform_count
                metrics['avg_sentiment'] /= platform_count
            metrics['platforms'] = list(metrics['platforms'])

        return competitor_metrics

    @staticmethod
    def generate_optimization_recommendations(brand_id: int) -> List[Dict]:
        """Generate AI search optimization recommendations"""
        recommendations = []

        # Get brand data
        brand = Brand.query.get(brand_id)
        if not brand:
            return recommendations

        # Get recent analytics
        recent_date = datetime.now().date() - timedelta(days=7)
        analytics = db.session.query(AnalyticsData).filter(
            and_(
                AnalyticsData.brand_id == brand_id,
                AnalyticsData.date >= recent_date
            )
        ).all()

        if not analytics:
            recommendations.append({
                'type': 'data_collection',
                'priority': 'high',
                'title': 'Start Data Collection',
                'description': 'Begin tracking your brand mentions across AI platforms to establish baseline metrics.',
                'action_items': [
                    'Set up automated brand monitoring',
                    'Define key search queries for your industry',
                    'Configure competitor tracking'
                ]
            })
            return recommendations

        # Analyze performance by platform
        platform_performance = {}
        for data in analytics:
            if data.ai_platform not in platform_performance:
                platform_performance[data.ai_platform] = {
                    'avg_visibility': 0,
                    'total_mentions': 0,
                    'avg_sentiment': 0,
                    'count': 0
                }

            perf = platform_performance[data.ai_platform]
            perf['avg_visibility'] += data.visibility_score
            perf['total_mentions'] += data.total_mentions
            perf['avg_sentiment'] += data.avg_sentiment_score
            perf['count'] += 1

        # Calculate averages and generate recommendations
        for platform, perf in platform_performance.items():
            if perf['count'] > 0:
                perf['avg_visibility'] /= perf['count']
                perf['avg_sentiment'] /= perf['count']

            # Low visibility recommendation
            if perf['avg_visibility'] < 30:
                recommendations.append({
                    'type': 'visibility',
                    'priority': 'high',
                    'platform': platform,
                    'title': f'Improve {platform.title()} Visibility',
                    'description': f'Your brand visibility on {platform} is below average ({perf["avg_visibility"]:.1f}/100).',
                    'action_items': [
                        'Create more authoritative content in your domain',
                        'Optimize content for AI search queries',
                        'Build high-quality backlinks to your content'
                    ]
                })

            # Negative sentiment recommendation
            if perf['avg_sentiment'] < -0.2:
                recommendations.append({
                    'type': 'sentiment',
                    'priority': 'medium',
                    'platform': platform,
                    'title': f'Address Negative Sentiment on {platform.title()}',
                    'description': f'Your brand sentiment on {platform} is negative ({perf["avg_sentiment"]:.2f}).',
                    'action_items': [
                        'Review and address customer concerns',
                        'Create positive content and case studies',
                        'Engage with community discussions'
                    ]
                })

            # Low mention volume recommendation
            if perf['total_mentions'] < 5:
                recommendations.append({
                    'type': 'mentions',
                    'priority': 'medium',
                    'platform': platform,
                    'title': f'Increase Brand Mentions on {platform.title()}',
                    'description': f'Your brand has low mention volume on {platform} ({perf["total_mentions"]} mentions).',
                    'action_items': [
                        'Create more searchable content',
                        'Participate in industry discussions',
                        'Develop thought leadership content'
                    ]
                })

        # Sort recommendations by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return recommendations[:10]  # Return top 10 recommendations