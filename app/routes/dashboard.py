from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Brand, AnalyticsData
from app.services.activity_logger import ActivityLogger
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # Get user's brands
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()

    # Get current brand (first active brand or None)
    current_brand = brands[0] if brands else None

    # Get basic metrics for current brand
    metrics = None
    if current_brand:
        metrics = get_brand_metrics(current_brand.id)

    return render_template('dashboard/index.html',
                           brands=brands,
                           current_brand=current_brand,
                           metrics=metrics)


@dashboard_bp.route('/brand/new', methods=['GET', 'POST'])
@login_required
def new_brand():
    if request.method == 'POST':
        data = request.form

        name = data.get('name')
        domain = data.get('domain')
        description = data.get('description')
        industry = data.get('industry')
        keywords = data.get('keywords', '').split(',') if data.get('keywords') else []
        competitors = data.get('competitors', '').split(',') if data.get('competitors') else []

        # Clean up lists
        keywords = [k.strip() for k in keywords if k.strip()]
        competitors = [c.strip() for c in competitors if c.strip()]

        if not name:
            flash('Brand name is required.', 'error')
            return render_template('dashboard/new_brand.html')

        try:
            brand = Brand(
                name=name,
                domain=domain,
                description=description,
                industry=industry,
                keywords=keywords,
                competitors=competitors,
                user_id=current_user.id
            )

            db.session.add(brand)
            db.session.commit()

            # Log brand creation - FIXED: use extra_data instead of metadata
            ActivityLogger.log_activity(
                user_id=current_user.id,
                activity_type='brand_created',
                description=f'Created brand "{name}"',
                extra_data={'brand_id': brand.id, 'brand_name': name}
            )

            flash(f'Brand "{name}" created successfully!', 'success')
            return redirect(url_for('dashboard.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating brand: {str(e)}', 'error')

    return render_template('dashboard/new_brand.html')


@dashboard_bp.route('/brands')
@login_required
def my_brands():
    """User's brand management page"""
    brands = Brand.query.filter_by(user_id=current_user.id).order_by(Brand.created_at.desc()).all()
    return render_template('dashboard/my_brands.html', brands=brands)


@dashboard_bp.route('/brand/<int:brand_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_brand(brand_id):
    """Edit brand"""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        data = request.form

        brand.name = data.get('name')
        brand.domain = data.get('domain')
        brand.description = data.get('description')
        brand.industry = data.get('industry')

        keywords = data.get('keywords', '').split(',') if data.get('keywords') else []
        competitors = data.get('competitors', '').split(',') if data.get('competitors') else []

        brand.keywords = [k.strip() for k in keywords if k.strip()]
        brand.competitors = [c.strip() for c in competitors if c.strip()]
        brand.updated_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log brand update - FIXED: use extra_data instead of metadata
            ActivityLogger.log_activity(
                user_id=current_user.id,
                activity_type='brand_updated',
                description=f'Updated brand "{brand.name}"',
                extra_data={'brand_id': brand.id, 'brand_name': brand.name}
            )

            flash(f'Brand "{brand.name}" updated successfully!', 'success')
            return redirect(url_for('dashboard.my_brands'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating brand: {str(e)}', 'error')

    return render_template('dashboard/edit_brand.html', brand=brand)


@dashboard_bp.route('/api/brand/<int:brand_id>/delete', methods=['DELETE'])
@login_required
def delete_brand(brand_id):
    """Delete brand (user)"""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    brand_name = brand.name

    try:
        db.session.delete(brand)
        db.session.commit()

        # Log brand deletion - FIXED: use extra_data instead of metadata
        ActivityLogger.log_activity(
            user_id=current_user.id,
            activity_type='brand_deleted',
            description=f'Deleted brand "{brand_name}"',
            extra_data={'brand_id': brand_id, 'brand_name': brand_name}
        )

        return jsonify({'success': True, 'message': f'Brand "{brand_name}" deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def get_brand_metrics(brand_id):
    """Get basic metrics for a brand"""
    # Get recent analytics data (last 7 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    analytics = AnalyticsData.query.filter(
        AnalyticsData.brand_id == brand_id,
        AnalyticsData.date.between(start_date, end_date)
    ).all()

    if not analytics:
        return {
            'visibility_score': 0,
            'total_mentions': 0,
            'sentiment_score': 0.0,
            'share_of_voice': 0.0
        }

    # Calculate aggregated metrics
    total_mentions = sum(a.total_mentions for a in analytics)
    avg_visibility = sum(a.visibility_score for a in analytics) / len(analytics)
    avg_sentiment = sum(a.avg_sentiment_score for a in analytics) / len(analytics)
    avg_share_of_voice = sum(a.share_of_voice for a in analytics) / len(analytics)

    return {
        'visibility_score': round(avg_visibility, 1),
        'total_mentions': total_mentions,
        'sentiment_score': round(avg_sentiment, 2),
        'share_of_voice': round(avg_share_of_voice, 1)
    }