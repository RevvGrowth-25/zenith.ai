from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from app.models import db
from app.services.notification_service import NotificationService
from datetime import datetime
import json

support_bp = Blueprint('support', __name__, url_prefix='/support')


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # technical, billing, general
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='support_tickets')


@support_bp.route('/')
@login_required
def index():
    """Help & Support main page"""
    # FAQ data
    faqs = [
        {
            'category': 'Getting Started',
            'questions': [
                {
                    'question': 'How do I add my first brand for monitoring?',
                    'answer': 'Navigate to "My Brands" in the dashboard and click "Add Brand". Fill in your brand details, keywords, and competitors you want to track.'
                },
                {
                    'question': 'What AI platforms do you monitor?',
                    'answer': 'We monitor ChatGPT, Claude, Perplexity AI, Google AI Overviews, and Bing Chat across various search queries and contexts.'
                },
                {
                    'question': 'How often is the data updated?',
                    'answer': 'Data is updated in real-time for premium plans and every 6 hours for standard plans. You can also trigger manual updates.'
                }
            ]
        },
        {
            'category': 'Analytics & Reporting',
            'questions': [
                {
                    'question': 'What metrics do you track?',
                    'answer': 'We track brand mentions, sentiment analysis, citation frequency, competitor comparisons, market share, and visibility scores across AI platforms.'
                },
                {
                    'question': 'Can I export my analytics data?',
                    'answer': 'Yes, you can export data in CSV, PDF, and JSON formats. Premium users get additional export options and automated reporting.'
                },
                {
                    'question': 'How is the visibility score calculated?',
                    'answer': 'Visibility score is calculated based on mention frequency, position in AI responses, citation quality, and sentiment analysis across all monitored platforms.'
                }
            ]
        },
        {
            'category': 'Account & Billing',
            'questions': [
                {
                    'question': 'How do I upgrade my plan?',
                    'answer': 'Go to Account Settings > Billing to view and upgrade your plan. Changes take effect immediately with prorated billing.'
                },
                {
                    'question': 'Can I change my billing cycle?',
                    'answer': 'Yes, you can switch between monthly and annual billing in your account profile. Annual plans include significant discounts.'
                },
                {
                    'question': 'What payment methods do you accept?',
                    'answer': 'We accept all major credit cards, PayPal, and wire transfers for enterprise accounts.'
                }
            ]
        }
    ]

    return render_template('support/index.html', faqs=faqs)


@support_bp.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    """Contact support form"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        try:
            # Create support ticket
            ticket = SupportTicket(
                user_id=current_user.id,
                subject=data.get('subject'),
                message=data.get('message'),
                category=data.get('category', 'general'),
                priority=data.get('priority', 'medium')
            )

            db.session.add(ticket)
            db.session.commit()

            # Create notification for user
            NotificationService.create_notification(
                user_id=current_user.id,
                title="Support Ticket Created",
                message=f"Your support ticket #{ticket.id} has been created. We'll respond within 24 hours.",
                notification_type='info',
                category='support',
                action_url=f"/support/tickets/{ticket.id}",
                action_text="View Ticket"
            )

            flash('Support ticket created successfully. We\'ll respond within 24 hours.', 'success')

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Ticket created successfully',
                    'ticket_id': ticket.id
                })

        except Exception as e:
            db.session.rollback()
            flash('Error creating support ticket', 'error')

            if request.is_json:
                return jsonify({'success': False, 'message': 'Error creating ticket'}), 500

    return render_template('support/contact.html')


@support_bp.route('/tickets')
@login_required
def my_tickets():
    """User's support tickets"""
    tickets = SupportTicket.query.filter_by(user_id=current_user.id) \
        .order_by(SupportTicket.created_at.desc()).all()

    return render_template('support/tickets.html', tickets=tickets)


@support_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    """Support ticket details"""
    ticket = SupportTicket.query.filter_by(
        id=ticket_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template('support/ticket_detail.html', ticket=ticket)


@support_bp.route('/documentation')
@login_required
def documentation():
    """Documentation page"""
    docs = {
        'getting_started': [
            {'title': 'Quick Start Guide', 'url': '#quickstart'},
            {'title': 'Adding Your First Brand', 'url': '#first-brand'},
            {'title': 'Understanding the Dashboard', 'url': '#dashboard'},
        ],
        'features': [
            {'title': 'Brand Monitoring', 'url': '#monitoring'},
            {'title': 'Competitor Analysis', 'url': '#competitors'},
            {'title': 'Analytics & Reporting', 'url': '#analytics'},
            {'title': 'AI Search Optimization', 'url': '#optimization'},
        ],
        'api': [
            {'title': 'API Authentication', 'url': '#api-auth'},
            {'title': 'Endpoints Reference', 'url': '#api-endpoints'},
            {'title': 'Rate Limits', 'url': '#rate-limits'},
            {'title': 'Webhooks', 'url': '#webhooks'},
        ]
    }

    return render_template('support/documentation.html', docs=docs)


@support_bp.route('/api-reference')
@login_required
def api_reference():
    """API Reference page"""
    return render_template('support/api_reference.html')