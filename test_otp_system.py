#!/usr/bin/env python3
"""
Test OTP system manually to verify it works
"""

import os
from app import app, db
from models import User
from mail_service import send_otp_email
import random
from datetime import datetime, timedelta

def test_otp_system():
    """Test the OTP system end-to-end"""
    
    print("=== SierraWings OTP System Test ===\n")
    
    with app.app_context():
        # Check email configuration
        print("1. Checking email configuration...")
        mail_username = os.environ.get('MAIL_USERNAME')
        mail_password = os.environ.get('MAIL_PASSWORD')
        mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = os.environ.get('MAIL_PORT', 587)
        
        print(f"   MAIL_USERNAME: {mail_username}")
        print(f"   MAIL_PASSWORD: {'*' * len(mail_password) if mail_password else 'Not set'}")
        print(f"   MAIL_SERVER: {mail_server}")
        print(f"   MAIL_PORT: {mail_port}")
        
        if not mail_username or not mail_password:
            print("   ❌ Email credentials not properly set!")
            return False
        
        # Test OTP generation
        print("\n2. Testing OTP generation...")
        otp_code = str(random.randint(100000, 999999))
        print(f"   Generated OTP: {otp_code}")
        
        # Create test user
        print("\n3. Creating test user...")
        test_user = User(
            username='testuser123',
            email='maadalumeh25@gmail.com',
            role='patient',
            first_name='Test',
            last_name='User',
            email_verification_token=otp_code,
            email_verification_expires=datetime.utcnow() + timedelta(minutes=15),
            email_verified=False
        )
        
        # Test email sending
        print("\n4. Testing email sending...")
        try:
            result = send_otp_email(test_user.email, test_user.first_name, otp_code)
            if result:
                print(f"   ✅ Email sent successfully to {test_user.email}")
                print(f"   📧 OTP Code: {otp_code}")
                print("   📱 Check your email for the verification code")
            else:
                print(f"   ❌ Failed to send email to {test_user.email}")
                
        except Exception as e:
            print(f"   ❌ Error sending email: {str(e)}")
            return False
        
        # Test OTP verification flow
        print("\n5. Testing OTP verification flow...")
        print("   To complete the test:")
        print(f"   1. Check email: {test_user.email}")
        print(f"   2. Enter OTP code: {otp_code}")
        print("   3. Verify the code matches what was sent")
        
        return result

if __name__ == "__main__":
    # Set environment variables if not already set
    if not os.environ.get('MAIL_USERNAME'):
        os.environ['MAIL_USERNAME'] = 'ramandhandumbuya01@gmail.com'
    if not os.environ.get('MAIL_PASSWORD'):
        os.environ['MAIL_PASSWORD'] = 'Rema~drex@01'
    if not os.environ.get('MAIL_SERVER'):
        os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
    if not os.environ.get('MAIL_PORT'):
        os.environ['MAIL_PORT'] = '587'
    
    test_otp_system()