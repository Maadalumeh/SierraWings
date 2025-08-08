"""
Simple Email Service for SierraWings
Provides console-based email verification for development
"""

import logging
from datetime import datetime

def send_console_email(to_email, subject, content):
    """Send email to console for testing"""
    print("\n" + "="*60)
    print("📧 EMAIL NOTIFICATION")
    print("="*60)
    print(f"TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print(f"TIME: {datetime.now()}")
    print("-"*60)
    print(content)
    print("="*60)
    print()
    logging.info(f"Console email sent to {to_email}: {subject}")
    return True

def send_verification_otp(user_email, user_name, otp_code):
    """Send OTP verification email to console"""
    subject = f"SierraWings Verification Code: {otp_code}"
    content = f"""
Hello {user_name},

Your SierraWings verification code is: {otp_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
SierraWings Team
"""
    return send_console_email(user_email, subject, content)

def send_welcome_email(user_email, user_name, role):
    """Send welcome email to console"""
    subject = f"Welcome to SierraWings, {user_name}!"
    content = f"""
Hello {user_name},

Welcome to SierraWings! Your account has been created successfully.

Role: {role.capitalize()}
Email: {user_email}

You can now log in and start using our medical drone delivery services.

Best regards,
SierraWings Team
"""
    return send_console_email(user_email, subject, content)