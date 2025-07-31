from app.models import db, Brand, SearchQuery, SearchResult, AnalyticsData, CompetitorData
from app.services.ai_search import AISearchService
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func, desc, and_
import json


class CompetitorAnalysisService:

    def __init__(self):
        self.ai_service = AISearchService()

    def analyze_competitors(self, brand_id: int) -> Dict:
        """Run comprehensive competitor analysis"""
        brand = Brand.query.get(brand_id)
        if not brand or not brand.competitors:
            return {'error': 'No competitors defined for this brand'}

        analysis_results = {
            'brand_name': brand.name,
            'competitors': [],
            'competitive_queries': [],
            'market_positioning': {},
            'recommendations': []
        }

        # Analyze each competitor
        for competitor in brand.competitors:
            competitor_data = self._analyze_single_competitor(brand, competitor)
            analysis_results['competitors'].append(competitor_data)

        # Run competitive queries
        competitive_queries = self._generate_competitive_queries(brand)
        for query in competitive_queries:
            query_result = self._analyze_competitive_query(brand, query)
            analysis_results['competitive_queries'].append(query_result)

        # Calculate market positioning
        analysis_results['market_positioning'] = self._calculate_market_positioning(brand, analysis_results[
            'competitive_queries'])

        # Generate competitive recommendations
        analysis_results['recommendations'] = self._generate_competitive_recommendations(brand, analysis_results)

        return analysis_results

    def _analyze_single_competitor(self, brand: Brand, competitor_name: str) -> Dict:
        """Analyze a single competitor across AI platforms"""
        competitor_queries = [
            f"What is {competitor_name}?",
            f"Tell me about {competitor_name}",
            f"{competitor_name} features and pricing",
            f"{competitor_name} vs alternatives"
        ]

        competitor_data = {
            'name': competitor_name,
            'visibility_scores': {},
            'mention_frequency': {},
            'sentiment_scores': {},
            'key_features_mentioned': [],
            'positioning_keywords': []
        }

        for query in competitor_queries[:2]:  # Limit to 2 queries per competitor
            results = self.ai_service.search_all_platforms(query, competitor_name)

            for result in results:
                if result['success']:
                    platform = result['platform']
                    analysis = result.get('brand_analysis', {})

                    # Store visibility data
                    if platform not in competitor_data['visibility_scores']:
                        competitor_data['visibility_scores'][platform] = []
                    competitor_data['visibility_scores'][platform].append(analysis.get('visibility_score', 0))

                    # Store mention frequency
                    if platform not in competitor_data['mention_frequency']:
                        competitor_data['mention_frequency'][platform] = 0
                    competitor_data['mention_frequency'][platform] += analysis.get('direct_mentions', 0)

                    # Store sentiment
                    if platform not in competitor_data['sentiment_scores']:
                        competitor_data['sentiment_scores'][platform] = []
                    competitor_data['sentiment_scores'][platform].append(analysis.get('sentiment_score', 0))

                    # Extract key features mentioned
                    self._extract_features_from_response(result['response'], competitor_data['key_features_mentioned'])

        # Calculate averages
        for platform in competitor_data['visibility_scores']:
            scores = competitor_data['visibility_scores'][platform]
            competitor_data['visibility_scores'][platform] = sum(scores) / len(scores) if scores else 0

            sentiment_scores = competitor_data['sentiment_scores'][platform]
            competitor_data['sentiment_scores'][platform] = sum(sentiment_scores) / len(
                sentiment_scores) if sentiment_scores else 0

        return competitor_data

    def _analyze_competitive_query(self, brand: Brand, query: str) -> Dict:
        """Analyze how brand performs against competitors in a specific query"""
        results = self.ai_service.search_all_platforms(query, brand.name)

        query_analysis = {
            'query': query,
            'brand_mentioned': False,
            'competitors_mentioned': [],
            'brand_position': None,
            'platform_results': {}
        }

        for result in results:
            if result['success']:
                platform = result['platform']
                response_text = result['response'].lower()

                # Check if brand is mentioned
                brand_analysis = result.get('brand_analysis', {})
                brand_mentioned = brand_analysis.get('direct_mentions', 0) > 0

                # Check which competitors are mentioned
                competitors_in_response = []
                for competitor in brand.competitors:
                    if competitor.lower() in response_text:
                        competitors_in_response.append(competitor)

                # Determine positioning
                position_info = self._determine_position_in_response(result['response'], brand.name, brand.competitors)

                query_analysis['platform_results'][platform] = {
                    'brand_mentioned': brand_mentioned,
                    'competitors_mentioned': competitors_in_response,
                    'brand_position': position_info['brand_position'],
                    'total_brands_mentioned': position_info['total_brands'],
                    'response_preview': result['response'][:300] + '...'
                }

                if brand_mentioned:
                    query_analysis['brand_mentioned'] = True

                query_analysis['competitors_mentioned'].extend(competitors_in_response)

        # Remove duplicates from competitors mentioned
        query_analysis['competitors_mentioned'] = list(set(query_analysis['competitors_mentioned']))

        return query_analysis

    def _generate_competitive_queries(self, brand: Brand) -> List[str]:
        """Generate queries for competitive analysis"""
        queries = []

        # Direct comparison queries
        for competitor in brand.competitors[:3]:  # Limit to top 3 competitors
            queries.append(f"{brand.name} vs {competitor}")
            queries.append(f"{brand.name} vs {competitor} comparison")
            queries.append(f"Alternative to {competitor}")

        # Category queries
        if brand.industry:
            queries.extend([
                f"Best {brand.industry} platforms",
                f"Top {brand.industry} tools 2024",
                f"Leading {brand.industry} solutions"
            ])

        # Keyword-based competitive queries
        if brand.keywords:
            for keyword in brand.keywords[:2]:  # Limit to 2 keywords
                queries.append(f"Best {keyword} tools")
                queries.append(f"{keyword} software comparison")

        return queries[:8]  # Limit total queries

    def _calculate_market_positioning(self, brand: Brand, competitive_queries: List[Dict]) -> Dict:
        """Calculate market positioning metrics"""
        positioning = {
            'mention_rate': 0,  # Percentage of queries where brand is mentioned
            'average_position': 0,  # Average position when mentioned
            'competitor_dominance': {},  # Which competitors appear most often
            'category_strength': 'unknown',  # Strong/Medium/Weak in category
            'unique_positioning': []  # Areas where brand appears but competitors don't
        }

        total_queries = len(competitive_queries)
        mentions = 0
        positions = []
        competitor_mentions = {}

        for query_result in competitive_queries:
            if query_result['brand_mentioned']:
                mentions += 1

                # Calculate average position across platforms
                platform_positions = []
                for platform_data in query_result['platform_results'].values():
                    if platform_data['brand_position']:
                        platform_positions.append(platform_data['brand_position'])

                if platform_positions:
                    avg_position = sum(platform_positions) / len(platform_positions)
                    positions.append(avg_position)

            # Count competitor mentions
            for competitor in query_result['competitors_mentioned']:
                competitor_mentions[competitor] = competitor_mentions.get(competitor, 0) + 1

        # Calculate metrics
        if total_queries > 0:
            positioning['mention_rate'] = (mentions / total_queries) * 100

        if positions:
            positioning['average_position'] = sum(positions) / len(positions)

        # Sort competitors by mention frequency
        positioning['competitor_dominance'] = dict(
            sorted(competitor_mentions.items(), key=lambda x: x[1], reverse=True)
        )

        # Determine category strength
        if positioning['mention_rate'] >= 70:
            positioning['category_strength'] = 'Strong'
        elif positioning['mention_rate'] >= 40:
            positioning['category_strength'] = 'Medium'
        else:
            positioning['category_strength'] = 'Weak'

        return positioning

    def _generate_competitive_recommendations(self, brand: Brand, analysis_results: Dict) -> List[Dict]:
        """Generate actionable competitive recommendations"""
        recommendations = []
        positioning = analysis_results['market_positioning']

        # Low mention rate recommendation
        if positioning['mention_rate'] < 50:
            recommendations.append({
                'type': 'visibility',
                'priority': 'high',
                'title': 'Improve Category Presence',
                'description': f'Your brand appears in only {positioning["mention_rate"]:.1f}% of relevant searches. Competitors are dominating category queries.',
                'actions': [
                    'Create comprehensive comparison content',
                    'Optimize for category keywords',
                    'Build authority in your industry space',
                    'Increase content marketing around key topics'
                ]
            })

        # Position improvement recommendation
        if positioning['average_position'] > 3:
            recommendations.append({
                'type': 'positioning',
                'priority': 'medium',
                'title': 'Improve Search Positioning',
                'description': f'When mentioned, your brand appears at position {positioning["average_position"]:.1f} on average. Aim for top 3 positions.',
                'actions': [
                    'Enhance unique value proposition content',
                    'Create more authoritative industry content',
                    'Build strategic partnerships and mentions',
                    'Focus on thought leadership'
                ]
            })

        # Competitor dominance recommendation
        if positioning['competitor_dominance']:
            top_competitor = list(positioning['competitor_dominance'].keys())[0]
            recommendations.append({
                'type': 'competitive',
                'priority': 'medium',
                'title': f'Address {top_competitor} Dominance',
                'description': f'{top_competitor} appears most frequently in competitive searches. Focus on differentiation.',
                'actions': [
                    f'Create direct comparison content with {top_competitor}',
                    'Highlight unique features and advantages',
                    'Target keywords where competitors are weak',
                    'Build case studies showing superior results'
                ]
            })

        # Platform-specific recommendations
        platform_performance = self._analyze_platform_performance(analysis_results)
        for platform, performance in platform_performance.items():
            if performance['needs_improvement']:
                recommendations.append({
                    'type': 'platform',
                    'priority': 'low',
                    'title': f'Improve {platform.title()} Performance',
                    'description': f'Underperforming on {platform} compared to other AI platforms.',
                    'actions': [
                        f'Optimize content for {platform} algorithms',
                        'Ensure content is easily discoverable',
                        'Focus on clear, direct answers to common questions'
                    ]
                })

        return recommendations[:6]  # Limit to top 6 recommendations

    def _determine_position_in_response(self, response_text: str, brand_name: str, competitors: List[str]) -> Dict:
        """Determine where brand appears relative to competitors in response"""
        brands_in_response = []

        # Find brand position
        brand_pos = response_text.lower().find(brand_name.lower())
        if brand_pos >= 0:
            brands_in_response.append((brand_name, brand_pos))

        # Find competitor positions
        for competitor in competitors:
            comp_pos = response_text.lower().find(competitor.lower())
            if comp_pos >= 0:
                brands_in_response.append((competitor, comp_pos))

        # Sort by position
        brands_in_response.sort(key=lambda x: x[1])

        # Find brand's position in the sorted list
        brand_position = None
        for i, (brand, pos) in enumerate(brands_in_response, 1):
            if brand.lower() == brand_name.lower():
                brand_position = i
                break

        return {
            'brand_position': brand_position,
            'total_brands': len(brands_in_response),
            'brands_order': [brand for brand, pos in brands_in_response]
        }

    def _extract_features_from_response(self, response_text: str, features_list: List[str]):
        """Extract mentioned features from AI response"""
        # Common feature keywords to look for
        feature_keywords = [
            'automation', 'analytics', 'integration', 'dashboard', 'reporting',
            'CRM', 'email marketing', 'lead generation', 'conversion tracking',
            'A/B testing', 'personalization', 'segmentation', 'workflow',
            'API', 'mobile app', 'real-time', 'machine learning', 'AI-powered'
        ]

        response_lower = response_text.lower()
        for keyword in feature_keywords:
            if keyword in response_lower and keyword not in features_list:
                features_list.append(keyword)

    def _analyze_platform_performance(self, analysis_results: Dict) -> Dict:
        """Analyze performance across different AI platforms"""
        platform_performance = {}

        for query_result in analysis_results['competitive_queries']:
            for platform, data in query_result['platform_results'].items():
                if platform not in platform_performance:
                    platform_performance[platform] = {
                        'mentions': 0,
                        'total_queries': 0,
                        'average_position': []
                    }

                platform_performance[platform]['total_queries'] += 1
                if data['brand_mentioned']:
                    platform_performance[platform]['mentions'] += 1
                    if data['brand_position']:
                        platform_performance[platform]['average_position'].append(data['brand_position'])

        # Calculate final metrics
        for platform, data in platform_performance.items():
            mention_rate = (data['mentions'] / data['total_queries']) * 100 if data['total_queries'] > 0 else 0
            avg_position = sum(data['average_position']) / len(data['average_position']) if data[
                'average_position'] else None

            platform_performance[platform] = {
                'mention_rate': mention_rate,
                'average_position': avg_position,
                'needs_improvement': mention_rate < 30  # Less than 30% mention rate needs improvement
            }

        return platform_performance

    def get_historical_competitor_data(self, brand_id: int, days: int = 30) -> Dict:
        """Get historical competitor performance data"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        brand = Brand.query.get(brand_id)
        if not brand:
            return {}

        # Get competitor data from database
        competitor_data = CompetitorData.query.filter(
            and_(
                CompetitorData.brand_id == brand_id,
                CompetitorData.date >= start_date
            )
        ).all()

        # Organize data by competitor
        historical_data = {}
        for data in competitor_data:
            competitor = data.competitor_name
            if competitor not in historical_data:
                historical_data[competitor] = {
                    'dates': [],
                    'visibility_scores': [],
                    'mentions': [],
                    'sentiment_scores': []
                }

            historical_data[competitor]['dates'].append(data.date.isoformat())
            historical_data[competitor]['visibility_scores'].append(data.visibility_score)
            historical_data[competitor]['mentions'].append(data.mentions)
            historical_data[competitor]['sentiment_scores'].append(data.avg_sentiment)

        return historical_data