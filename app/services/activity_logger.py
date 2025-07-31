from app.models import db
from app.models.user_activity import UserActivity
from datetime import datetime
from flask import request
import json


class ActivityLogger:
    @staticmethod
    def log_activity(user_id, activity_type, description=None, extra_data=None):
        """Log user activity"""
        try:
            # Get request info if available
            ip_address = None
            user_agent = None

            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent')

            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data=extra_data
            )

            db.session.add(activity)
            db.session.commit()

            return True

        except Exception as e:
            print(f"Error logging activity: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def log_login(user_id):
        """Log user login"""
        return ActivityLogger.log_activity(
            user_id=user_id,
            activity_type='login',
            description='User logged in'
        )

    @staticmethod
    def log_logout(user_id):
        """Log user logout"""
        return ActivityLogger.log_activity(
            user_id=user_id,
            activity_type='logout',
            description='User logged out'
        )

    @staticmethod
    def log_brand_created(user_id, brand_name):
        """Log brand creation"""
        return ActivityLogger.log_activity(
            user_id=user_id,
            activity_type='brand_created',
            description=f'Created brand: {brand_name}',
            extra_data={'brand_name': brand_name}
        )

    @staticmethod
    def log_brand_updated(user_id, brand_name):
        """Log brand update"""
        return ActivityLogger.log_activity(
            user_id=user_id,
            activity_type='brand_updated',
            description=f'Updated brand: {brand_name}',
            extra_data={'brand_name': brand_name}
        )

    @staticmethod
    def log_brand_deleted(user_id, brand_name):
        """Log brand deletion"""
        return ActivityLogger.log_activity(
            user_id=user_id,
            activity_type='brand_deleted',
            description=f'Deleted brand: {brand_name}',
            extra_data={'brand_name': brand_name}
        )