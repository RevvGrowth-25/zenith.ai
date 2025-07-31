import sys
import os

sys.path.insert(0, os.path.abspath('.'))

import sqlite3
from datetime import datetime


def reset_database_complete():
    # Database file path
    db_path = 'ai_analytics.db'

    print(f"Completely resetting database: {db_path}")

    # Remove existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Removed existing database")

    # Create new database with correct schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create users table with all required columns
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                company VARCHAR(100),
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                login_count INTEGER DEFAULT 0
            )
        """)

        # Create user_activities table
        cursor.execute("""
            CREATE TABLE user_activities (
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

        # Create brands table
        cursor.execute("""
            CREATE TABLE brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                domain VARCHAR(255),
                description TEXT,
                industry VARCHAR(100),
                keywords JSON,
                competitors JSON,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create brand_queries table
        cursor.execute("""
            CREATE TABLE brand_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                query_text VARCHAR(500) NOT NULL,
                query_type VARCHAR(50),
                priority INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands(id)
            )
        """)

        # Create search_queries table
        cursor.execute("""
            CREATE TABLE search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text VARCHAR(500) NOT NULL,
                ai_platform VARCHAR(50) NOT NULL,
                response_text TEXT,
                citations JSON,
                brand_mentions JSON,
                sentiment_score FLOAT,
                relevance_score FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create search_results table
        cursor.execute("""
            CREATE TABLE search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_query_id INTEGER NOT NULL,
                brand_query_id INTEGER,
                position INTEGER,
                mention_type VARCHAR(50),
                context TEXT,
                sentiment VARCHAR(20),
                confidence_score FLOAT,
                url_cited VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_query_id) REFERENCES search_queries(id),
                FOREIGN KEY (brand_query_id) REFERENCES brand_queries(id)
            )
        """)

        # Create analytics_data table
        cursor.execute("""
            CREATE TABLE analytics_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                date DATE NOT NULL,
                ai_platform VARCHAR(50) NOT NULL,
                total_mentions INTEGER DEFAULT 0,
                direct_mentions INTEGER DEFAULT 0,
                indirect_mentions INTEGER DEFAULT 0,
                citation_count INTEGER DEFAULT 0,
                visibility_score FLOAT DEFAULT 0.0,
                positive_sentiment INTEGER DEFAULT 0,
                negative_sentiment INTEGER DEFAULT 0,
                neutral_sentiment INTEGER DEFAULT 0,
                avg_sentiment_score FLOAT DEFAULT 0.0,
                avg_position FLOAT,
                top_3_mentions INTEGER DEFAULT 0,
                share_of_voice FLOAT DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands(id),
                UNIQUE(brand_id, date, ai_platform)
            )
        """)

        # Create competitor_data table
        cursor.execute("""
            CREATE TABLE competitor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                competitor_name VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                ai_platform VARCHAR(50) NOT NULL,
                mentions INTEGER DEFAULT 0,
                visibility_score FLOAT DEFAULT 0.0,
                avg_sentiment FLOAT DEFAULT 0.0,
                market_share FLOAT DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands(id)
            )
        """)

        # Insert admin user with hashed password
        from werkzeug.security import generate_password_hash
        admin_password_hash = generate_password_hash('admin123')

        cursor.execute("""
            INSERT INTO users (email, username, password_hash, first_name, last_name, company, role, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('admin@example.com', 'admin', admin_password_hash, 'Admin', 'User', 'AI Search Analytics', 'admin', 0))

        # Commit all changes
        conn.commit()

        print("✅ Database reset completed successfully!")
        print("✅ All tables created with proper schema")
        print("✅ Admin user created:")
        print("   Email: admin@example.com")
        print("   Password: admin123")
        print("⚠️  Please change the admin password after first login!")

    except Exception as e:
        print(f"❌ Error during database reset: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    reset_database_complete()