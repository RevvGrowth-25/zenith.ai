import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import db, User
import sqlite3


def reset_database():
    app = create_app('default')

    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

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

        try:
            db.session.add(admin)
            db.session.commit()
            print("✅ Created admin user")
            print("Email: admin@example.com")
            print("Password: admin123")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            db.session.rollback()


if __name__ == '__main__':
    reset_database()