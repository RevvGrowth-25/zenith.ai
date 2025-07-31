from app.models import db, Brand, SearchQuery, SearchResult, AnalyticsData
from app.services.ai_search import AISearchService
from datetime import datetime, date
from typing import List, Dict
import json


class BrandMonitoringService:

    def __init__(self):
        self.ai_service = AISearchService()

    def monitor_brand(self, brand_id: int, custom_queries: List[str] = None) -> Dict:
        """Monitor a brand across AI platforms"""
        brand = Brand.query.get(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID {brand_id} not found")

        # Generate search queries for the brand
        queries = custom_queries or self.generate_brand_queries(brand)

        results = []
        total_mentions = 0
        total_visibility = 0
        sentiment_scores = []

        print(f"Monitoring brand: {brand.name}")
        print(f"Queries to test: {queries}")

        for query in queries[:3]:  # Limit to 3 queries to avoid API costs
            print(f"Testing query: {query}")

            # Search across platforms
            search_results = self.ai_service.search_all_platforms(query, brand.name)

            for result in search_results:
                if result['success']:
                    # Store search query
                    search_query = SearchQuery(
                        query_text=query,
                        ai_platform=result['platform'],
                        response_text=result['response'],
                        brand_mentions=result.get('brand_analysis', {}),
                        sentiment_score=result.get('brand_analysis', {}).get('sentiment_score', 0),
                        user_id=brand.user_id
                    )

                    db.session.add(search_query)
                    db.session.flush()  # Get the ID

                    # Analyze brand mentions
                    analysis = result.get('brand_analysis', {})
                    if analysis and analysis.get('direct_mentions', 0) > 0:
                        # Store search result
                        search_result = SearchResult(
                            search_query_id=search_query.id,
                            position=1,  # Simplified for now
                            mention_type=analysis.get('mention_type', 'none'),
                            context=analysis.get('contexts', [''])[0] if analysis.get('contexts') else '',
                            sentiment=self._sentiment_to_label(analysis.get('sentiment_score', 0)),
                            confidence_score=0.8,  # Default confidence
                            url_cited=None
                        )

                        db.session.add(search_result)

                        total_mentions += analysis.get('direct_mentions', 0)
                        total_visibility += analysis.get('visibility_score', 0)
                        sentiment_scores.append(analysis.get('sentiment_score', 0))

                    results.append(result)

        # Calculate aggregate metrics
        avg_visibility = (total_visibility / len(results)) if results else 0
        avg_sentiment = (sum(sentiment_scores) / len(sentiment_scores)) if sentiment_scores else 0

        # Store analytics data
        today = date.today()
        for platform in ['chatgpt', 'claude', 'perplexity']:
            platform_results = [r for r in results if r['platform'] == platform]
            platform_mentions = sum(
                r.get('brand_analysis', {}).get('direct_mentions', 0) for r in platform_results if r['success'])
            platform_visibility = sum(
                r.get('brand_analysis', {}).get('visibility_score', 0) for r in platform_results if r['success'])
            platform_visibility_avg = (platform_visibility / len(platform_results)) if platform_results else 0

            # Update or create analytics data
            analytics = AnalyticsData.query.filter_by(
                brand_id=brand_id,
                date=today,
                ai_platform=platform
            ).first()

            if not analytics:
                analytics = AnalyticsData(
                    brand_id=brand_id,
                    date=today,
                    ai_platform=platform
                )
                db.session.add(analytics)

            analytics.total_mentions = platform_mentions
            analytics.direct_mentions = platform_mentions
            analytics.visibility_score = platform_visibility_avg
            analytics.avg_sentiment_score = avg_sentiment
            analytics.positive_sentiment = len([s for s in sentiment_scores if s > 0.1])
            analytics.negative_sentiment = len([s for s in sentiment_scores if s < -0.1])
            analytics.neutral_sentiment = len([s for s in sentiment_scores if -0.1 <= s <= 0.1])

        try:
            db.session.commit()
            print(f"✅ Successfully monitored brand {brand.name}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving monitoring data: {e}")
            raise

        return {
            'brand_name': brand.name,
            'queries_tested': len(queries),
            'total_mentions': total_mentions,
            'average_visibility': avg_visibility,
            'average_sentiment': avg_sentiment,
            'results': results
        }

    def generate_brand_queries(self, brand: Brand) -> List[str]:
        """Generate relevant search queries for a brand"""
        queries = []

        # Basic brand query
        queries.append(f"What is {brand.name}?")
        queries.append(f"Tell me about {brand.name}")

        # Industry-specific queries
        if brand.industry:
            queries.append(f"Best {brand.industry} companies")
            queries.append(f"Top {brand.industry} solutions")
            queries.append(f"Leading {brand.industry} platforms")

        # Keyword-based queries
        if brand.keywords:
            for keyword in brand.keywords[:2]:  # Limit to 2 keywords
                queries.append(f"Best {keyword} solutions")
                queries.append(f"{keyword} companies")

        # Competitive queries
        if brand.competitors:
            queries.append(f"Compare {brand.name} vs {brand.competitors[0]}")
            queries.append(f"Alternatives to {brand.competitors[0]}")

        return queries[:5]  # Limit to 5 queries

    def _sentiment_to_label(self, sentiment_score: float) -> str:
        """Convert sentiment score to label"""
        if sentiment_score > 0.1:
            return 'positive'
        elif sentiment_score < -0.1:
            return 'negative'
        else:
            return 'neutral'