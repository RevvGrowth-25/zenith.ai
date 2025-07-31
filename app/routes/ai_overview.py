from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from app.models import AIOverview
import os

ai_overview_bp = Blueprint('ai_overview', __name__)

def get_overview_service():
    """Get overview service instance with proper error handling"""
    try:
        from app.services.ai_overview_service import AIOverviewService

        openai_key = os.environ.get('OPENAI_API_KEY') or current_app.config.get('OPENAI_API_KEY')
        serpapi_key = os.environ.get('SERPAPI_KEY') or current_app.config.get('SERPAPI_KEY')

        if not openai_key:
            raise ValueError("OpenAI API key not configured")
        if not serpapi_key:
            raise ValueError("SerpAPI key not configured")

        return AIOverviewService(openai_key, serpapi_key)
    except Exception as e:
        current_app.logger.error(f"Failed to initialize AI Overview service: {e}")
        return None

@ai_overview_bp.route('/ai-overview')
@login_required
def ai_overview_page():
    """AI Overview main page"""
    # Get recent overviews from database directly
    recent_overviews = AIOverview.query.filter_by(user_id=current_user.id) \
        .order_by(AIOverview.created_at.desc()) \
        .limit(10).all()

    recent_overviews_data = [overview.to_dict() for overview in recent_overviews]

    # Check if service is configured
    service = get_overview_service()
    service_configured = service is not None

    return render_template('ai_overview/index.html',
                           recent_overviews=recent_overviews_data,
                           service_configured=service_configured)

@ai_overview_bp.route('/api/generate-overview', methods=['POST'])
@login_required
def generate_overview():
    """API endpoint to generate AI overview"""
    try:
        # Check if service is available
        service = get_overview_service()
        if not service:
            return jsonify({
                'success': False,
                'error': 'AI Overview service is not configured. Please set OPENAI_API_KEY and SERPAPI_KEY environment variables.'
            }), 503

        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        if len(query) > 500:
            return jsonify({'error': 'Query too long. Maximum 500 characters.'}), 400

        # Generate overview
        result = service.generate_overview(query, current_user.id)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        current_app.logger.error(f"Error generating overview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_overview_bp.route('/api/overview-history')
@login_required
def get_overview_history():
    """Get user's AI overview history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        overviews = AIOverview.query.filter_by(user_id=current_user.id) \
            .order_by(AIOverview.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': {
                'overviews': [overview.to_dict() for overview in overviews.items],
                'total': overviews.total,
                'pages': overviews.pages,
                'current_page': page
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_overview_bp.route('/api/overview/<int:overview_id>')
@login_required
def get_overview_detail(overview_id):
    """Get specific overview details"""
    try:
        overview = AIOverview.query.filter_by(
            id=overview_id,
            user_id=current_user.id
        ).first()

        if not overview:
            return jsonify({'error': 'Overview not found'}), 404

        return jsonify({
            'success': True,
            'data': overview.to_dict()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_overview_bp.route('/api/service-status')
@login_required
def service_status():
    """Check if AI Overview service is properly configured"""
    service = get_overview_service()
    return jsonify({
        'configured': service is not None,
        'openai_key_set': bool(os.environ.get('OPENAI_API_KEY')),
        'serpapi_key_set': bool(os.environ.get('SERPAPI_KEY'))
    })