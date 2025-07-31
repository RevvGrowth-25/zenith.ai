from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create tables if they don't exist
    db.create_all()

    # Create admin user
    admin_email = input("Enter admin email: ")
    admin_password = input("Enter admin password: ")
    admin_username = input("Enter admin username: ")
    admin_first_name = input("Enter admin first name: ")
    admin_last_name = input("Enter admin last name: ")

    # Check if user already exists
    existing_user = User.query.filter_by(email=admin_email).first()
    if existing_user:
        existing_user.role = 'admin'
        print(f"Updated existing user {admin_email} to admin role")
    else:
        admin_user = User(
            email=admin_email,
            username=admin_username,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role='admin'
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        print(f"Created new admin user: {admin_email}")

    db.session.commit()
    print("Admin user created/updated successfully!")