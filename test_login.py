#!/usr/bin/env python3
"""
Test script to create a test user and verify login functionality
"""

from app import app, db
from models import User

def create_test_user():
    """Create a test patient user"""
    with app.app_context():
        # Check if test user already exists
        test_user = User.query.filter_by(email='test@patient.com').first()
        if test_user:
            print("Test user already exists")
            return

        # Create test patient user
        user = User(
            username='testpatient',
            email='test@patient.com',
            role='patient',
            first_name='Test',
            last_name='Patient',
            is_active=True
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        print("Test patient user created successfully:")
        print(f"Email: test@patient.com")
        print(f"Password: password123")

if __name__ == '__main__':
    create_test_user()