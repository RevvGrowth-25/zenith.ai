import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import db, User
from app.services.activity_logger import ActivityLogger


def reset_database():
    app = create_app('default')

    with app.app_context():
        # Get the database path
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            print("❌ This script is for SQLite databases only")
            return

        print(f"Resetting database: {db_path}")

        # Remove existing database file
        if os.path.exists(db_path):
            os.remove(db_path)
            print("✅ Removed existing database")

        # Create all tables
        db.create_all()
        print("✅ Created new database with all tables")

        # Create an admin user
        admin = User(
            email='admin@example.com',
            username='admin',
            first_name='Admin',
            last_name='User',
            role='admin',
            company='AI Search Analytics',
            login_count=0
        )
        admin.set_password('admin123')

        # Create a test user
        test_user = User(
            email='user@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            role='user',
            company='Test Company',
            login_count=0
        )
        test_user.set_password('user123')

        try:
            db.session.add(admin)
            db.session.add(test_user)
            db.session.commit()

            # Log initial activities
            ActivityLogger.log_registration(admin.id, admin.username)
            ActivityLogger.log_registration(test_user.id, test_user.username)

            print("✅ Created users successfully!")
            print("\n👤 Admin User:")
            print("   Email: admin@example.com")
            print("   Password: admin123")
            print("\n👤 Test User:")
            print("   Email: user@example.com")
            print("   Password: user123")
            print("\n⚠️  Please change these passwords after first login!")

        except Exception as e:
            print(f"❌ Error creating users: {e}")
            db.session.rollback()


if __name__ == '__main__':
    print("🔄 Resetting AI Search Analytics Database")
    print("=" * 50)

    confirm = input("This will delete all existing data. Continue? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        reset_database()
    else:
        print("❌ Database reset cancelled")