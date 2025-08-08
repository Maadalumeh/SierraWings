# Gmail App-Specific Password Setup Guide

## Why App-Specific Password is Needed
Gmail requires app-specific passwords for third-party applications when 2-factor authentication is enabled. This provides better security than using your regular Gmail password.

## Steps to Generate App-Specific Password

### 1. Enable 2-Factor Authentication (if not already enabled)
- Go to your Google Account settings
- Navigate to "Security" → "2-Step Verification"
- Follow the setup process

### 2. Generate App-Specific Password
- In Google Account settings, go to "Security"
- Under "2-Step Verification", click "App passwords"
- Select "Mail" as the app type
- Choose "Other (Custom name)" and enter "SierraWings"
- Click "Generate"
- Copy the 16-character password (format: xxxx xxxx xxxx xxxx)

### 3. Update SierraWings Configuration
Replace the current password in `.env` file:
```
MAIL_PASSWORD=your-16-character-app-password
```

### 4. Test the Configuration
Run the test script to verify OTP emails are working:
```bash
python test_otp_system.py
```

## Alternative Solutions
If app-specific passwords don't work, consider:
1. Using Gmail OAuth2 (more complex but more secure)
2. Using a different SMTP service (SendGrid, Mailgun, etc.)
3. Using a business Gmail account with less restrictive settings

## Current Status
- Email: ramandhandumbuya01@gmail.com
- Password: Using regular password (needs app-specific password)
- SMTP Server: smtp.gmail.com
- Port: 587
- TLS: Enabled

## Test Results
The system is configured correctly but fails authentication due to Gmail's security requirements.