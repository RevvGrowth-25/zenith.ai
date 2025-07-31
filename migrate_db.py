import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import db
import sqlite3


def migrate_database():
    app = create_app('default')

    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        print(f"Migrating database: {db_path}")

        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Check if login_count column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]

            # Add missing columns to users table
            if 'login_count' not in columns:
                print("Adding login_count column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0")

            # Create user_activities table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    description VARCHAR(255),
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(255),
                    extra_data JSON,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Commit changes
            conn.commit()
            print("✅ Database migration completed successfully!")

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
        finally:
            conn.close()


if __name__ == '__main__':
    migrate_database()