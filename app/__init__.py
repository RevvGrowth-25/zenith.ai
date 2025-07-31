from flask import Flask
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_caching import Cache
from flask_cors import CORS
from app.routes.ai_overview import ai_overview_bp
from app.models import db, User

from config import config

login_manager = LoginManager()
jwt = JWTManager()
migrate = Migrate()
cache = Cache()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    CORS(app)

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user: {e}")
            return None

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ai_overview_bp, url_prefix='/ai-overview')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    # Try to register admin blueprint if it exists
    try:
        from app.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        print("Admin blueprint not found - skipping")

    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    # Add a simple route for testing
    @app.route('/test')
    def test_route():
        return {'message': 'Flask app is working!', 'status': 'success'}

    # Health check route
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'database': 'connected'}

    # Create tables if they don't exist
    with app.app_context():
        try:
            # Only create tables if database file doesn't exist or is empty
            import os
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if not os.path.exists(db_path):
                db.create_all()
                print("✅ Database tables created")
        except Exception as e:
            print(f"Note: Database tables may already exist: {e}")

    return app