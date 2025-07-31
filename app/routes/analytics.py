from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Brand, SearchQuery, SearchResult, AnalyticsData, CompetitorData, UserActivity
from app.services.analytics_service import AnalyticsService
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc, and_

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/overview')
@login_required
def overview():
    """Analytics overview page"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()

    # Get selected brand
    brand_id = request.args.get('brand_id', type=int)
    if brand_id:
        current_brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    else:
        current_brand = brands[0] if brands else None

    # Get analytics data
    analytics_data = {}
    recent_searches = []
    platform_breakdown = {}
    sentiment_analysis = {}

    if current_brand:
        analytics_data = get_brand_analytics_data(current_brand.id)
        recent_searches = get_recent_searches(current_brand.id)
        platform_breakdown = get_platform_breakdown(current_brand.id)
        sentiment_analysis = get_sentiment_analysis(current_brand.id)

    return render_template('analytics/overview.html',
                           brands=brands,
                           current_brand=current_brand,
                           analytics_data=analytics_data,
                           recent_searches=recent_searches,
                           platform_breakdown=platform_breakdown,
                           sentiment_analysis=sentiment_analysis)


@analytics_bp.route('/search-results')
@login_required
def search_results():
    """Detailed search results page"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()

    # Get selected brand
    brand_id = request.args.get('brand_id', type=int)
    if brand_id:
        current_brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    else:
        current_brand = brands[0] if brands else None

    # Get search results with pagination
    page = request.args.get('page', 1, type=int)
    platform_filter = request.args.get('platform', '')
    date_filter = request.args.get('date_range', '7')  # days

    if current_brand:
        search_results = get_paginated_search_results(
            current_brand.id, page, platform_filter, int(date_filter)
        )
    else:
        search_results = None

    return render_template('analytics/search_results.html',
                           brands=brands,
                           current_brand=current_brand,
                           search_results=search_results,
                           platform_filter=platform_filter,
                           date_filter=date_filter)


@analytics_bp.route('/competitors')
@login_required
def competitors():
    """Competitor analysis page"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()

    # Get selected brand
    brand_id = request.args.get('brand_id', type=int)
    if brand_id:
        current_brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    else:
        current_brand = brands[0] if brands else None

    competitor_data = {}
    competitive_analysis = {}
    historical_data = {}

    if current_brand and current_brand.competitors:
        # Get recent competitor data
        competitor_data = get_competitor_performance_data(current_brand.id)

        # Get competitive positioning
        competitive_analysis = get_competitive_positioning(current_brand.id)

    return render_template('analytics/competitors.html',
                           brands=brands,
                           current_brand=current_brand,
                           competitor_data=competitor_data,
                           competitive_analysis=competitive_analysis,
                           historical_data=historical_data)


@analytics_bp.route('/recommendations')
@login_required
def recommendations():
    """Optimization recommendations page"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()

    # Get selected brand
    brand_id = request.args.get('brand_id', type=int)
    if brand_id:
        current_brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    else:
        current_brand = brands[0] if brands else None

    recommendations = []
    if current_brand:
        recommendations = AnalyticsService.generate_optimization_recommendations(current_brand.id)

    return render_template('analytics/recommendations.html',
                           brands=brands,
                           current_brand=current_brand,
                           recommendations=recommendations)


@analytics_bp.route('/search')
@login_required
def search():
    """AI Search testing page"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('analytics/search.html', brands=brands)


# API endpoints for analytics
@analytics_bp.route('/api/brand/<int:brand_id>/analytics')
@login_required
def api_brand_analytics(brand_id):
    """API endpoint for brand analytics data"""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404

    days = request.args.get('days', 30, type=int)

    # Get trends data
    trends = get_visibility_trends(brand_id, days)
    platform_data = get_platform_performance_trends(brand_id, days)

    return jsonify({
        'visibility_trends': trends,
        'platform_performance': platform_data
    })


@analytics_bp.route('/api/competitors/<int:brand_id>/analyze', methods=['POST'])
@login_required
def run_competitor_analysis(brand_id):
    """Run live competitor analysis"""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404

    if not brand.competitors:
        return jsonify({'error': 'No competitors defined for this brand'}), 400

    try:
        from app.services.competitor_analysis import CompetitorAnalysisService
        competitor_service = CompetitorAnalysisService()

        # Run analysis
        results = competitor_service.analyze_competitors(brand_id)

        # Store results in database for historical tracking
        store_competitor_analysis_results(brand_id, results)

        return jsonify({
            'success': True,
            'message': 'Competitor analysis completed',
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Helper functions
def get_brand_analytics_data(brand_id):
    """Get comprehensive analytics data for a brand"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    # Get recent analytics data
    analytics = AnalyticsData.query.filter(
        and_(
            AnalyticsData.brand_id == brand_id,
            AnalyticsData.date >= start_date
        )
    ).all()

    if not analytics:
        return {
            'total_mentions': 0,
            'avg_visibility': 0,
            'avg_sentiment': 0,
            'total_queries': 0,
            'platforms_active': 0,
            'trend_direction': 'neutral'
        }

    # Calculate metrics
    total_mentions = sum(a.total_mentions for a in analytics)
    avg_visibility = sum(a.visibility_score for a in analytics) / len(analytics)
    avg_sentiment = sum(a.avg_sentiment_score for a in analytics) / len(analytics)

    # Get unique platforms
    platforms_active = len(set(a.ai_platform for a in analytics))

    # Get total queries
    total_queries = SearchQuery.query.filter(
        and_(
            SearchQuery.user_id == current_user.id,
            SearchQuery.created_at >= start_date
        )
    ).count()

    # Calculate trend direction
    recent_week = [a for a in analytics if a.date >= end_date - timedelta(days=7)]
    previous_week = [a for a in analytics if start_date <= a.date < end_date - timedelta(days=7)]

    trend_direction = 'neutral'
    if recent_week and previous_week:
        recent_avg = sum(a.visibility_score for a in recent_week) / len(recent_week)
        previous_avg = sum(a.visibility_score for a in previous_week) / len(previous_week)

        if recent_avg > previous_avg * 1.1:
            trend_direction = 'up'
        elif recent_avg < previous_avg * 0.9:
            trend_direction = 'down'

    return {
        'total_mentions': total_mentions,
        'avg_visibility': round(avg_visibility, 1),
        'avg_sentiment': round(avg_sentiment, 2),
        'total_queries': total_queries,
        'platforms_active': platforms_active,
        'trend_direction': trend_direction
    }


def get_recent_searches(brand_id, limit=10):
    """Get recent search queries for a brand"""
    queries = db.session.query(SearchQuery).filter(
        SearchQuery.user_id == current_user.id
    ).order_by(desc(SearchQuery.created_at)).limit(limit).all()

    results = []
    for query in queries:
        # Check if this query mentions the brand
        brand_mentions = query.brand_mentions or {}
        if isinstance(brand_mentions, dict) and brand_mentions.get('direct_mentions', 0) > 0:
            results.append({
                'id': query.id,
                'query_text': query.query_text,
                'platform': query.ai_platform,
                'created_at': query.created_at,
                'mentions': brand_mentions.get('direct_mentions', 0),
                'sentiment': query.sentiment_score or 0,
                'response_preview': query.response_text[:200] + '...' if len(
                    query.response_text) > 200 else query.response_text
            })

    return results


def get_platform_breakdown(brand_id):
    """Get platform performance breakdown"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    analytics = AnalyticsData.query.filter(
        and_(
            AnalyticsData.brand_id == brand_id,
            AnalyticsData.date >= start_date
        )
    ).all()

    platform_data = {}
    for data in analytics:
        platform = data.ai_platform
        if platform not in platform_data:
            platform_data[platform] = {
                'mentions': 0,
                'visibility_scores': [],
                'sentiment_scores': []
            }

        platform_data[platform]['mentions'] += data.total_mentions
        platform_data[platform]['visibility_scores'].append(data.visibility_score)
        platform_data[platform]['sentiment_scores'].append(data.avg_sentiment_score)

    # Calculate averages
    for platform, data in platform_data.items():
        data['avg_visibility'] = sum(data['visibility_scores']) / len(data['visibility_scores']) if data[
            'visibility_scores'] else 0
        data['avg_sentiment'] = sum(data['sentiment_scores']) / len(data['sentiment_scores']) if data[
            'sentiment_scores'] else 0
        data['avg_visibility'] = round(data['avg_visibility'], 1)
        data['avg_sentiment'] = round(data['avg_sentiment'], 2)

    return platform_data


def get_sentiment_analysis(brand_id):
    """Get sentiment analysis breakdown"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    analytics = AnalyticsData.query.filter(
        and_(
            AnalyticsData.brand_id == brand_id,
            AnalyticsData.date >= start_date
        )
    ).all()

    total_positive = sum(a.positive_sentiment for a in analytics)
    total_negative = sum(a.negative_sentiment for a in analytics)
    total_neutral = sum(a.neutral_sentiment for a in analytics)
    total_all = total_positive + total_negative + total_neutral

    if total_all == 0:
        return {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'positive_percent': 0,
            'negative_percent': 0,
            'neutral_percent': 0
        }

    return {
        'positive': total_positive,
        'negative': total_negative,
        'neutral': total_neutral,
        'positive_percent': round((total_positive / total_all) * 100, 1),
        'negative_percent': round((total_negative / total_all) * 100, 1),
        'neutral_percent': round((total_neutral / total_all) * 100, 1)
    }


def get_visibility_trends(brand_id, days=30):
    """Get visibility trends over time"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Get daily analytics data
    daily_data = db.session.query(
        AnalyticsData.date,
        func.avg(AnalyticsData.visibility_score).label('avg_visibility')
    ).filter(
        and_(
            AnalyticsData.brand_id == brand_id,
            AnalyticsData.date >= start_date
        )
    ).group_by(AnalyticsData.date).order_by(AnalyticsData.date).all()

    # Fill missing dates with 0
    result = []
    current_date = start_date
    data_dict = {row.date: row.avg_visibility for row in daily_data}

    while current_date <= end_date:
        result.append({
            'date': current_date.isoformat(),
            'visibility': round(data_dict.get(current_date, 0), 1)
        })
        current_date += timedelta(days=1)

    return result


def get_platform_performance_trends(brand_id, days=30):
    """Get platform performance trends"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    analytics = AnalyticsData.query.filter(
        and_(
            AnalyticsData.brand_id == brand_id,
            AnalyticsData.date >= start_date
        )
    ).all()

    platform_trends = {}
    for data in analytics:
        platform = data.ai_platform
        date_str = data.date.isoformat()

        if platform not in platform_trends:
            platform_trends[platform] = {}

        if date_str not in platform_trends[platform]:
            platform_trends[platform][date_str] = []

        platform_trends[platform][date_str].append(data.visibility_score)

    # Calculate daily averages for each platform
    result = {}
    for platform, dates in platform_trends.items():
        result[platform] = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in dates:
                avg_score = sum(dates[date_str]) / len(dates[date_str])
            else:
                avg_score = 0

            result[platform].append({
                'date': date_str,
                'visibility': round(avg_score, 1)
            })
            current_date += timedelta(days=1)

    return result


def get_paginated_search_results(brand_id, page, platform_filter, date_range):
    """Get paginated search results"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=date_range)

    query = SearchQuery.query.filter(
        and_(
            SearchQuery.user_id == current_user.id,
            SearchQuery.created_at >= start_date
        )
    )

    if platform_filter:
        query = query.filter(SearchQuery.ai_platform == platform_filter)

    # Only include queries that mention the brand
    brand = Brand.query.get(brand_id)
    if brand:
        # This is a simplified filter - in a real implementation, you'd want to
        # properly filter based on brand mentions in the stored data
        query = query.filter(SearchQuery.response_text.contains(brand.name))

    results = query.order_by(desc(SearchQuery.created_at)).paginate(
        page=page, per_page=10, error_out=False
    )

    return results


def get_competitor_performance_data(brand_id):
    """Get competitor performance summary"""
    brand = Brand.query.get(brand_id)
    if not brand or not brand.competitors:
        return {}

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    # Get recent competitor data
    competitor_data = CompetitorData.query.filter(
        and_(
            CompetitorData.brand_id == brand_id,
            CompetitorData.date >= start_date
        )
    ).all()

    # Organize by competitor
    performance_data = {}
    for data in competitor_data:
        competitor = data.competitor_name
        if competitor not in performance_data:
            performance_data[competitor] = {
                'total_mentions': 0,
                'avg_visibility': 0,
                'avg_sentiment': 0,
                'data_points': 0
            }

        performance_data[competitor]['total_mentions'] += data.mentions
        performance_data[competitor]['avg_visibility'] += data.visibility_score
        performance_data[competitor]['avg_sentiment'] += data.avg_sentiment
        performance_data[competitor]['data_points'] += 1

    # Calculate averages
    for competitor, data in performance_data.items():
        if data['data_points'] > 0:
            data['avg_visibility'] = round(data['avg_visibility'] / data['data_points'], 1)
            data['avg_sentiment'] = round(data['avg_sentiment'] / data['data_points'], 2)

    return performance_data


def get_competitive_positioning(brand_id):
    """Get competitive positioning analysis"""
    # This would typically come from stored analysis results
    # For now, return mock data structure
    return {
        'market_share': {
            'brand_mention_rate': 25.5,
            'category_strength': 'Medium',
            'avg_position': 2.8
        },
        'competitor_dominance': {
            'HubSpot': 65,
            'Marketo': 45,
            'Pardot': 30
        },
        'opportunities': [
            'Lead generation queries show gap',
            'Marketing automation comparisons underperforming',
            'Strong in conversion optimization category'
        ]
    }


def store_competitor_analysis_results(brand_id, results):
    """Store competitor analysis results for historical tracking"""
    today = date.today()

    for competitor_info in results['competitors']:
        competitor_name = competitor_info['name']

        # Calculate aggregated metrics
        all_visibility_scores = []
        all_mentions = 0
        all_sentiment_scores = []

        for platform, scores in competitor_info['visibility_scores'].items():
            if isinstance(scores, list):
                all_visibility_scores.extend(scores)
            else:
                all_visibility_scores.append(scores)

        for platform, mentions in competitor_info['mention_frequency'].items():
            all_mentions += mentions

        for platform, scores in competitor_info['sentiment_scores'].items():
            if isinstance(scores, list):
                all_sentiment_scores.extend(scores)
            else:
                all_sentiment_scores.append(scores)

        avg_visibility = sum(all_visibility_scores) / len(all_visibility_scores) if all_visibility_scores else 0
        avg_sentiment = sum(all_sentiment_scores) / len(all_sentiment_scores) if all_sentiment_scores else 0

        # Store in database
        competitor_data = CompetitorData.query.filter_by(
            brand_id=brand_id,
            competitor_name=competitor_name,
            date=today,
            ai_platform='aggregated'
        ).first()

        if not competitor_data:
            competitor_data = CompetitorData(
                brand_id=brand_id,
                competitor_name=competitor_name,
                date=today,
                ai_platform='aggregated'
            )
            db.session.add(competitor_data)

        competitor_data.mentions = all_mentions
        competitor_data.visibility_score = avg_visibility
        competitor_data.avg_sentiment = avg_sentiment
        competitor_data.market_share = 0  # Calculate based on relative performance

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error storing competitor analysis: {e}")