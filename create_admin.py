#!/usr/bin/env python3
"""
Create First Administrator Account
This script creates the first admin account for SierraWings production deployment.
"""

import sys
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def create_admin_user():
    """Create first admin user"""
    print("Creating first administrator account for SierraWings...")
    
    # Get admin details
    print("\nEnter administrator details:")
    username = input("Username: ").strip()
    if not username:
        print("Username is required!")
        return False
    
    email = input("Email: ").strip()
    if not email:
        print("Email is required!")
        return False
    
    password = input("Password: ").strip()
    if not password:
        print("Password is required!")
        return False
    
    first_name = input("First Name: ").strip()
    last_name = input("Last Name: ").strip()
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        print(f"User with email {email} already exists!")
        return False
    
    if User.query.filter_by(username=username).first():
        print(f"User with username {username} already exists!")
        return False
    
    # Create admin user
    admin_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role='admin',
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )
    
    try:
        db.session.add(admin_user)
        db.session.commit()
        print(f"\nAdmin user '{username}' created successfully!")
        print(f"Email: {email}")
        print(f"Role: admin")
        print("\nYou can now login to the SierraWings admin panel.")
        return True
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    with app.app_context():
        if not create_admin_user():
            sys.exit(1)