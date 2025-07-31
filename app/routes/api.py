from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Brand, SearchQuery, AnalyticsData
from app.services.ai_search import AISearchService
from app.services.analytics_service import AnalyticsService
from datetime import datetime, timedelta
import os

api_bp = Blueprint('api', __name__)


@api_bp.route('/dashboard/<int:brand_id>')
@login_required
def dashboard_data(brand_id):
    """Get dashboard data for a specific brand"""
    # Verify brand ownership
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404

    try:
        # Get metrics (using dummy data for now)
        metrics = {
            'visibility_score': 75.5,
            'total_mentions': 24,
            'sentiment_score': 0.65,
            'share_of_voice': 15.2
        }

        # Get trends data (dummy data)
        trends_data = {
            'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'scores': [70, 72, 75, 78, 76]
        }

        # Get platform performance (dummy data)
        platform_data = {
            'chatgpt': 80,
            'claude': 75,
            'perplexity': 65,
            'google_ai': 70
        }

        # Get recent activity (dummy data)
        recent_activity = [
            {
                'icon': 'search',
                'message': f'New mention detected for {brand.name}',
                'time': '2 hours ago'
            },
            {
                'icon': 'trending-up',
                'message': 'Visibility score increased by 5%',
                'time': '4 hours ago'
            }
        ]

        return jsonify({
            'metrics': metrics,
            'trends': trends_data,
            'platform_data': platform_data,
            'recent_activity': recent_activity
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/search', methods=['POST'])
@login_required
def perform_search():
    """Perform AI search across platforms"""
    data = request.get_json()
    query = data.get('query')
    platforms = data.get('platforms', ['chatgpt'])
    brand_id = data.get('brand_id')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    # For now, return mock results
    results = []
    for platform in platforms:
        results.append({
            'platform': platform,
            'query': query,
            'response': f'This is a mock response from {platform} for query: {query}',
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        })

    return jsonify({
        'success': True,
        'results': results
    })


@api_bp.route('/brands', methods=['GET', 'POST'])
@login_required
def manage_brands():
    """Get user brands or create new brand"""
    if request.method == 'GET':
        brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()
        return jsonify([brand.to_dict() for brand in brands])

    elif request.method == 'POST':
        data = request.get_json()

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Brand name is required'}), 400

        try:
            brand = Brand(
                name=data['name'],
                domain=data.get('domain'),
                description=data.get('description'),
                industry=data.get('industry'),
                keywords=data.get('keywords', []),
                competitors=data.get('competitors', []),
                user_id=current_user.id
            )

            db.session.add(brand)
            db.session.commit()

            return jsonify(brand.to_dict()), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


# Add this to your existing api.py file

@api_bp.route('/brand/<int:brand_id>/monitor', methods=['POST'])
@login_required
def monitor_brand(brand_id):
    """Run real-time brand monitoring"""
    # Verify brand ownership
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404

    try:
        from app.services.brand_monitor import BrandMonitoringService

        monitor = BrandMonitoringService()
        results = monitor.monitor_brand(brand_id)

        return jsonify({
            'success': True,
            'message': f'Brand monitoring completed for {brand.name}',
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/brand/<int:brand_id>/quick-test', methods=['POST'])
@login_required
def quick_brand_test(brand_id):
    """Quick test of brand visibility"""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404

    try:
        from app.services.ai_search import AISearchService

        ai_service = AISearchService()

        # Test with a simple query
        test_query = f"What is {brand.name}?"
        results = ai_service.search_all_platforms(test_query, brand.name)

        # Quick analysis
        mentions_found = 0
        platforms_with_mentions = []

        for result in results:
            if result['success'] and result.get('brand_analysis', {}).get('direct_mentions', 0) > 0:
                mentions_found += result['brand_analysis']['direct_mentions']
                platforms_with_mentions.append(result['platform'])

        return jsonify({
            'success': True,
            'test_query': test_query,
            'mentions_found': mentions_found,
            'platforms_with_mentions': platforms_with_mentions,
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'API is working!',
        'timestamp': datetime.utcnow().isoformat(),
        'user_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
    })