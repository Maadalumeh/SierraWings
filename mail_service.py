"""
Flask-Mail Service for SierraWings
Handles email verification, OTP, and notifications using Flask-Mail
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string
from flask_mail import Mail, Message
import logging

# Initialize Flask-Mail
mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', '1', 'yes']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'sierrawingsofficial@gmail.com')
    
    mail.init_app(app)
    logging.info("Flask-Mail initialized successfully")

def send_email(to_email, subject, html_content=None, text_content=None):
    """Send email using Flask-Mail"""
    try:
        if not current_app.config.get('MAIL_USERNAME'):
            logging.warning("Email not sent: MAIL_USERNAME not configured")
            return False
            
        msg = Message(
            subject=subject,
            recipients=[to_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        if html_content:
            msg.html = html_content
        if text_content:
            msg.body = text_content
            
        mail.send(msg)
        logging.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_otp_email(user_email, user_name, otp_code, purpose="email verification"):
    """Send OTP email for verification"""
    subject = f"Your SierraWings Verification Code - {otp_code}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SierraWings - Email Verification</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #3498DB 0%, #5DADE2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
            }
            .content {
                padding: 30px;
            }
            .otp-code {
                background: linear-gradient(135deg, #F8F9FA 0%, #F1F3F4 100%);
                border: 2px solid #3498DB;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }
            .otp-number {
                font-size: 32px;
                font-weight: bold;
                color: #3498DB;
                letter-spacing: 8px;
                margin: 10px 0;
            }
            .footer {
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
            .medical-icon {
                color: #3498DB;
                font-size: 20px;
                margin-right: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚁 SierraWings Medical Delivery</h1>
                <p>Emergency Medical Drone Services</p>
            </div>
            
            <div class="content">
                <h2>Hello {{ user_name }}!</h2>
                <p>Thank you for using SierraWings emergency medical delivery service. To complete your {{ purpose }}, please use the verification code below:</p>
                
                <div class="otp-code">
                    <p><strong>Your Verification Code:</strong></p>
                    <div class="otp-number">{{ otp_code }}</div>
                    <p><small>This code expires in 10 minutes</small></p>
                </div>
                
                <p>If you didn't request this verification, please ignore this email.</p>
                
                <div style="margin-top: 30px; padding: 20px; background: #e8f4f8; border-radius: 8px;">
                    <p><strong>🏥 About SierraWings:</strong></p>
                    <p>We provide life saving medical drone deliveries across Sierra Leone, connecting patients with critical medications and medical supplies when they need them most.</p>
                </div>
            </div>
            
            <div class="footer">
                <p>SierraWings Medical Delivery Service</p>
                <p>📞 +232 34 994 803 | ✉️ sierrawingsofficial@gmail.com</p>
                <p>Reducing hospital paperwork through digital innovation</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_template = """
    SierraWings - Email Verification
    
    Hello {{ user_name }}!
    
    Thank you for using SierraWings emergency medical delivery service.
    
    Your verification code for {{ purpose }} is: {{ otp_code }}
    
    This code expires in 10 minutes.
    
    If you didn't request this verification, please ignore this email.
    
    SierraWings Medical Delivery Service
    Phone: +232 34 994 803
    Email: sierrawingsofficial@gmail.com
    """
    
    html_content = render_template_string(html_template, user_name=user_name, otp_code=otp_code, purpose=purpose)
    text_content = render_template_string(text_template, user_name=user_name, otp_code=otp_code, purpose=purpose)
    
    return send_email(user_email, subject, html_content, text_content)

def send_welcome_email(user_email, user_name, role):
    """Send role-specific welcome email to new users"""
    if role == 'patient':
        subject = "Welcome to SierraWings - Your Medical Delivery Partner"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to SierraWings</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #2980B9 0%, #3498DB 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .benefits {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .benefit-item {{
                    margin: 10px 0;
                    padding: 5px 0;
                }}
                .footer {{
                    background-color: #1A252F;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚁 Welcome to SierraWings!</h1>
                    <p>Thank you for joining our medical delivery revolution</p>
                </div>
                <div class="content">
                    <h2>Hello {user_name},</h2>
                    <p>Welcome to SierraWings, Sierra Leone's premier medical drone delivery service! We're thrilled to have you as part of our community.</p>
                    
                    <div class="benefits">
                        <h3>🎯 Benefits of SierraWings for Patients:</h3>
                        <div class="benefit-item">⚡ <strong>Emergency Medical Deliveries:</strong> Get life saving medications delivered within minutes</div>
                        <div class="benefit-item">🏥 <strong>Hospital Network Access:</strong> Connect with verified hospitals and clinics across Sierra Leone</div>
                        <div class="benefit-item">📱 <strong>Real Time Tracking:</strong> Monitor your delivery in real time with GPS tracking</div>
                        <div class="benefit-item">🔒 <strong>Secure & Private:</strong> Your medical information is protected with advanced encryption</div>
                        <div class="benefit-item">💰 <strong>Affordable Healthcare:</strong> Reduced costs compared to traditional delivery methods</div>
                        <div class="benefit-item">📞 <strong>24/7 Support:</strong> Emergency medical delivery available round the clock</div>
                        <div class="benefit-item">🌍 <strong>Rural Access:</strong> Reach remote areas where traditional transport is challenging</div>
                    </div>
                    
                    <p><strong>What's Next?</strong></p>
                    <ul>
                        <li>Complete your profile with emergency contact information</li>
                        <li>Request your first medical delivery</li>
                        <li>Connect with hospitals in your area</li>
                        <li>Experience the future of healthcare delivery</li>
                    </ul>
                    
                    <p>Our mission is to save lives by providing fast, reliable medical deliveries to every corner of Sierra Leone. With SierraWings, help is always just minutes away.</p>
                    
                    <p>Best regards,<br>
                    The SierraWings Team<br>
                    Revolutionizing Healthcare Delivery in Sierra Leone</p>
                </div>
                <div class="footer">
                    <p>📧 sierrawingsofficial@gmail.com | 📞 +232 34 994 803</p>
                    <p>© 2025 SierraWings. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
    elif role == 'clinic':
        subject = "Welcome to SierraWings - Hospital Partnership Program"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to SierraWings</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .benefits {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .benefit-item {{
                    margin: 10px 0;
                    padding: 5px 0;
                }}
                .footer {{
                    background-color: #1A252F;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Welcome to SierraWings!</h1>
                    <p>Join our network of healthcare providers</p>
                </div>
                <div class="content">
                    <h2>Hello {user_name},</h2>
                    <p>Welcome to SierraWings Hospital Partnership Program! Thank you for joining our mission to revolutionize healthcare delivery in Sierra Leone.</p>
                    
                    <div class="benefits">
                        <h3>🎯 Benefits of SierraWings for Hospitals:</h3>
                        <div class="benefit-item">👥 <strong>Patient Management:</strong> Streamlined digital patient registration and record keeping</div>
                        <div class="benefit-item">🚁 <strong>Drone Delivery Network:</strong> Send medications and supplies to patients instantly</div>
                        <div class="benefit-item">📊 <strong>Analytics Dashboard:</strong> Track delivery performance and patient outcomes</div>
                        <div class="benefit-item">💼 <strong>Reduced Paperwork:</strong> Digital forms and automated documentation</div>
                        <div class="benefit-item">🌐 <strong>Extended Reach:</strong> Serve patients in remote areas effectively</div>
                        <div class="benefit-item">⚡ <strong>Emergency Response:</strong> Immediate deployment for critical cases</div>
                        <div class="benefit-item">🔗 <strong>Network Integration:</strong> Connect with other healthcare providers</div>
                    </div>
                    
                    <p><strong>Getting Started:</strong></p>
                    <ul>
                        <li>Complete your hospital profile and certification</li>
                        <li>Add your medical services and specialties</li>
                        <li>Start managing patient records digitally</li>
                        <li>Begin processing delivery requests</li>
                    </ul>
                    
                    <p>Together, we're building a healthcare system that reaches every person in Sierra Leone, no matter how remote their location.</p>
                    
                    <p>Best regards,<br>
                    The SierraWings Team<br>
                    Transforming Healthcare Access</p>
                </div>
                <div class="footer">
                    <p>📧 sierrawingsofficial@gmail.com | 📞 +232 34 994 803</p>
                    <p>© 2025 SierraWings. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
    elif role == 'admin':
        subject = "Welcome to SierraWings - Administrator Access"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to SierraWings</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .benefits {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .benefit-item {{
                    margin: 10px 0;
                    padding: 5px 0;
                }}
                .footer {{
                    background-color: #1A252F;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Welcome to SierraWings!</h1>
                    <p>Administrator Access Granted</p>
                </div>
                <div class="content">
                    <h2>Hello {user_name},</h2>
                    <p>Welcome to SierraWings Administration Panel! You now have full access to manage our medical drone delivery platform.</p>
                    
                    <div class="benefits">
                        <h3>🎯 Administrator Capabilities:</h3>
                        <div class="benefit-item">👥 <strong>User Management:</strong> Oversee all patient, hospital, and admin accounts</div>
                        <div class="benefit-item">🚁 <strong>Drone Fleet Control:</strong> Monitor and manage the entire drone network</div>
                        <div class="benefit-item">📊 <strong>System Analytics:</strong> Access comprehensive platform statistics</div>
                        <div class="benefit-item">⚙️ <strong>System Configuration:</strong> Modify platform settings and parameters</div>
                        <div class="benefit-item">🔒 <strong>Security Oversight:</strong> Monitor system security and access logs</div>
                        <div class="benefit-item">📈 <strong>Performance Monitoring:</strong> Track system health and performance metrics</div>
                        <div class="benefit-item">🆘 <strong>Emergency Management:</strong> Handle critical system events and responses</div>
                    </div>
                    
                    <p><strong>Administrative Responsibilities:</strong></p>
                    <ul>
                        <li>Ensure system security and data protection</li>
                        <li>Monitor drone fleet performance and maintenance</li>
                        <li>Manage user accounts and access permissions</li>
                        <li>Oversee platform operations and troubleshooting</li>
                    </ul>
                    
                    <p>As an administrator, you play a crucial role in maintaining the platform that saves lives across Sierra Leone. Thank you for your dedication to this mission.</p>
                    
                    <p>Best regards,<br>
                    The SierraWings Team<br>
                    System Operations</p>
                </div>
                <div class="footer">
                    <p>📧 sierrawingsofficial@gmail.com | 📞 +232 34 994 803</p>
                    <p>© 2025 SierraWings. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return send_email(user_email, subject, html_content)
    subject = f"Welcome to SierraWings Medical Delivery - {role.title()} Account Created"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Welcome to SierraWings</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #3498DB 0%, #5DADE2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .content {
                padding: 30px;
            }
            .feature-box {
                background: linear-gradient(135deg, #F8F9FA 0%, #F1F3F4 100%);
                border: 1px solid rgba(52, 152, 219, 0.2);
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            .footer {
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚁 Welcome to SierraWings!</h1>
                <p>Emergency Medical Drone Services</p>
            </div>
            
            <div class="content">
                <h2>Hello {{ user_name }}!</h2>
                <p>Welcome to SierraWings medical delivery platform. Your {{ role }} account has been successfully created.</p>
                
                <div class="feature-box">
                    <h3>🏥 What You Can Do:</h3>
                    {% if role == 'patient' %}
                    <ul>
                        <li>Request emergency medical deliveries</li>
                        <li>Track your deliveries in real time</li>
                        <li>Search for nearby hospitals and clinics</li>
                        <li>View your delivery history</li>
                    </ul>
                    {% elif role == 'clinic' %}
                    <ul>
                        <li>Manage patient delivery requests</li>
                        <li>Register and manage patient records</li>
                        <li>Monitor drone fleet operations</li>
                        <li>Process emergency medical requests</li>
                    </ul>
                    {% elif role == 'admin' %}
                    <ul>
                        <li>Manage entire drone fleet</li>
                        <li>Monitor system wide operations</li>
                        <li>Handle user management</li>
                        <li>Access system analytics</li>
                    </ul>
                    {% endif %}
                </div>
                
                <div class="feature-box">
                    <h3>🚀 Get Started:</h3>
                    <p>Log in to your account to start using SierraWings medical delivery services.</p>
                    <p><strong>Need help?</strong> Contact our support team at sierrawingsofficial@gmail.com</p>
                </div>
            </div>
            
            <div class="footer">
                <p>SierraWings Medical Delivery Service</p>
                <p>📞 +232 34 994 803 | ✉️ sierrawingsofficial@gmail.com</p>
                <p>Reducing hospital paperwork through digital innovation</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to SierraWings Medical Delivery!
    
    Hello {user_name}!
    
    Welcome to SierraWings medical delivery platform. Your {role} account has been successfully created.
    
    Log in to your account to start using our services.
    
    Need help? Contact our support team at sierrawingsofficial@gmail.com
    
    SierraWings Medical Delivery Service
    Phone: +232 34 994 803
    Email: sierrawingsofficial@gmail.com
    """
    
    html_content = render_template_string(html_template, user_name=user_name, role=role)
    
    return send_email(user_email, subject, html_content, text_content)

def send_password_reset_email(user_email, user_name, reset_token):
    """Send password reset email"""
    subject = "SierraWings - Password Reset Request"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SierraWings - Password Reset</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #3498DB 0%, #5DADE2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .content {
                padding: 30px;
            }
            .reset-button {
                background: linear-gradient(135deg, #3498DB 0%, #5DADE2 100%);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 8px;
                display: inline-block;
                margin: 20px 0;
                font-weight: bold;
            }
            .footer {
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 Password Reset</h1>
                <p>SierraWings Medical Delivery</p>
            </div>
            
            <div class="content">
                <h2>Hello {{ user_name }}!</h2>
                <p>We received a request to reset your password for your SierraWings account.</p>
                
                <p>Click the button below to reset your password:</p>
                
                <a href="{{ reset_url }}" class="reset-button">Reset Password</a>
                
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #3498DB;">{{ reset_url }}</p>
                
                <p><strong>This link expires in 1 hour.</strong></p>
                
                <p>If you didn't request this password reset, please ignore this email.</p>
            </div>
            
            <div class="footer">
                <p>SierraWings Medical Delivery Service</p>
                <p>📞 +232 34 994 803 | ✉️ sierrawingsofficial@gmail.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    from flask import url_for, request
    reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
    
    html_content = render_template_string(html_template, user_name=user_name, reset_url=reset_url)
    text_content = f"""
    SierraWings - Password Reset Request
    
    Hello {user_name}!
    
    We received a request to reset your password for your SierraWings account.
    
    Click this link to reset your password: {reset_url}
    
    This link expires in 1 hour.
    
    If you didn't request this password reset, please ignore this email.
    
    SierraWings Medical Delivery Service
    Phone: +232 34 994 803
    Email: sierrawingsofficial@gmail.com
    """
    
    return send_email(user_email, subject, html_content, text_content)

def send_emergency_notification(clinic_email, clinic_name, emergency_data):
    """Send emergency notification to clinics"""
    subject = f"🚨 URGENT: Emergency Medical Delivery Request - {emergency_data.get('patient_name', 'Unknown')}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Emergency Medical Delivery Request</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #DC3545 0%, #E74C3C 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .content {
                padding: 30px;
            }
            .emergency-box {
                background: linear-gradient(135deg, #FDEDEC 0%, #F8D7DA 100%);
                border: 2px solid #DC3545;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            .info-box {
                background: linear-gradient(135deg, #F8F9FA 0%, #F1F3F4 100%);
                border: 1px solid rgba(52, 152, 219, 0.2);
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
            .footer {
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 EMERGENCY REQUEST</h1>
                <p>SierraWings Medical Delivery</p>
            </div>
            
            <div class="content">
                <h2>Hello {{ clinic_name }}!</h2>
                
                <div class="emergency-box">
                    <h3>🚑 Emergency Medical Delivery Request</h3>
                    <p><strong>URGENT ACTION REQUIRED</strong></p>
                </div>
                
                <div class="info-box">
                    <h4>Patient Information:</h4>
                    <p><strong>Name:</strong> {{ emergency_data.patient_name }}</p>
                    <p><strong>Location:</strong> {{ emergency_data.delivery_address }}</p>
                    <p><strong>Contact:</strong> {{ emergency_data.patient_contact }}</p>
                </div>
                
                <div class="info-box">
                    <h4>Medical Request:</h4>
                    <p><strong>Items Needed:</strong> {{ emergency_data.medical_items }}</p>
                    <p><strong>Priority:</strong> {{ emergency_data.priority }}</p>
                    <p><strong>Request Time:</strong> {{ emergency_data.request_time }}</p>
                </div>
                
                <p><strong>Please log in to your dashboard to review and respond to this emergency request immediately.</strong></p>
            </div>
            
            <div class="footer">
                <p>SierraWings Medical Delivery Service</p>
                <p>📞 +232 34 994 803 | ✉️ sierrawingsofficial@gmail.com</p>
                <p>Every second counts in emergency medical care</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    html_content = render_template_string(html_template, clinic_name=clinic_name, emergency_data=emergency_data)
    text_content = f"""
    🚨 EMERGENCY MEDICAL DELIVERY REQUEST
    
    Hello {clinic_name}!
    
    URGENT ACTION REQUIRED
    
    Patient Information:
    Name: {emergency_data.get('patient_name', 'Unknown')}
    Location: {emergency_data.get('delivery_address', 'Unknown')}
    Contact: {emergency_data.get('patient_contact', 'Unknown')}
    
    Medical Request:
    Items Needed: {emergency_data.get('medical_items', 'Unknown')}
    Priority: {emergency_data.get('priority', 'Unknown')}
    Request Time: {emergency_data.get('request_time', 'Unknown')}
    
    Please log in to your dashboard to review and respond to this emergency request immediately.
    
    SierraWings Medical Delivery Service
    Phone: +232 34 994 803
    Email: sierrawingsofficial@gmail.com
    """
    
    return send_email(clinic_email, subject, html_content, text_content)