import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import db, User


def test_app():
    app = create_app('default')

    with app.app_context():
        # Create tables
        db.create_all()

        # Test creating a user
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('testpassword')

        try:
            db.session.add(user)
            db.session.commit()
            print("✅ User created successfully")
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            db.session.rollback()

        # Test routes
        with app.test_client() as client:
            # Test basic routes
            response = client.get('/auth/login')
            print(f"✅ Login page: {response.status_code}")

            response = client.get('/auth/register')
            print(f"✅ Register page: {response.status_code}")

            response = client.get('/api/test')
            print(f"✅ API test: {response.status_code}")

    print("✅ All tests passed!")


if __name__ == '__main__':
    test_app()