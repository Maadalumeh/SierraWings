import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import url_for, current_app

sendgrid_key = os.environ.get('SENDGRID_API_KEY')
if not sendgrid_key:
    print('Warning: SENDGRID_API_KEY environment variable not set')

def send_email(to_email, from_email, subject, text_content=None, html_content=None):
    """Send email using SendGrid"""
    if not sendgrid_key:
        print(f"Email not sent (no API key): {subject} to {to_email}")
        return False
    
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(to_email),
            subject=subject
        )
        
        if html_content:
            message.content = Content("text/html", html_content)
        elif text_content:
            message.content = Content("text/plain", text_content)
        
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_welcome_email(user_email, user_name, role):
    from datetime import datetime
    """Send welcome email to new users"""
    subject = "Welcome to SierraWings Emergency Drone Delivery"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Welcome to SierraWings</h1>
            <p style="color: #e3f2fd; margin: 10px 0 0 0;">Emergency Medical Drone Delivery System</p>
        </div>
        
        <div style="padding: 30px; background: #ffffff;">
            <h2 style="color: #1e3c72;">Hello {user_name},</h2>
            
            <p>Welcome to SierraWings! Your account has been successfully created as a <strong>{role.title()}</strong>.</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e3c72; margin-top: 0;">What's Next?</h3>
                {"<p>• Complete your clinic profile to appear in our directory</p><p>• Review incoming delivery requests</p><p>• Access live operations dashboard</p>" if role == 'clinic' else "<p>• Request emergency medical deliveries</p><p>• Track your missions in real time</p><p>• View available medical facilities</p>" if role == 'patient' else "<p>• Manage system operations</p><p>• Monitor all drone activities</p><p>• Oversee user management</p>"}
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{url_for('auth.login', _external=True)}" 
                   style="background: #1e3c72; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Access Your Dashboard
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                If you have any questions, please contact our support team.<br>
                This is an automated message from SierraWings Emergency Medical Services.
            </p>
        </div>
    </div>
    """
    
    return send_email(user_email, "noreply@sierrawings.com", subject, html_content=html_content)

def send_clinic_registration_confirmation(user_email, clinic_name):
    """Send confirmation email when clinic profile is registered"""
    subject = "Clinic Profile Registered - SierraWings"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Clinic Registration Confirmed</h1>
            <p style="color: #e3f2fd; margin: 10px 0 0 0;">SierraWings Medical Network</p>
        </div>
        
        <div style="padding: 30px; background: #ffffff;">
            <h2 style="color: #1e3c72;">Congratulations!</h2>
            
            <p>Your clinic <strong>{clinic_name}</strong> has been successfully registered in the SierraWings medical network.</p>
            
            <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                <h3 style="color: #2e7d32; margin-top: 0;">✓ Your clinic is now visible to patients</h3>
                <p style="margin-bottom: 0;">Patients can now see your facility when requesting emergency medical deliveries in your service area.</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e3c72; margin-top: 0;">Next Steps:</h3>
                <p>• Monitor incoming delivery requests</p>
                <p>• Update your service hours and capabilities</p>
                <p>• Review and accept emergency missions</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{url_for('clinic.dashboard', _external=True)}" 
                   style="background: #1e3c72; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Access Clinic Dashboard
                </a>
            </div>
        </div>
    </div>
    """
    
    return send_email(user_email, "noreply@sierrawings.com", subject, html_content=html_content)

def send_password_reset_email(user_email, user_name, reset_token):
    """Send password reset email"""
    subject = "Password Reset - SierraWings"
    reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Password Reset Request</h1>
            <p style="color: #e3f2fd; margin: 10px 0 0 0;">SierraWings Security</p>
        </div>
        
        <div style="padding: 30px; background: #ffffff;">
            <h2 style="color: #1e3c72;">Hello {user_name},</h2>
            
            <p>We received a request to reset your password for your SierraWings account.</p>
            
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <p style="margin: 0;"><strong>Security Notice:</strong> This link will expire in 1 hour for your protection.</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Your Password
                </a>
            </div>
            
            <p>If you didn't request this password reset, you can safely ignore this email. Your password will not be changed.</p>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                For security reasons, do not share this email with anyone.<br>
                This link is valid for 1 hour only.
            </p>
        </div>
    </div>
    """
    
    return send_email(user_email, "noreply@sierrawings.com", subject, html_content=html_content)

def send_emergency_notification_email(clinic_email, clinic_name, emergency_data):
    """Send emergency notification to clinics"""
    subject = "🚨 EMERGENCY DRONE REQUEST - SierraWings"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 3px solid #dc3545;">
        <div style="background-color: #dc3545; color: white; padding: 15px; text-align: center;">
            <h1 style="margin: 0;">🚨 EMERGENCY MEDICAL REQUEST</h1>
        </div>
        <div style="padding: 20px;">
            <h2 style="color: #dc3545;">Immediate Action Required</h2>
            <p><strong>Clinic:</strong> {clinic_name}</p>
            <p><strong>Mission ID:</strong> #{emergency_data['mission_id']}</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 5px solid #dc3545; margin: 15px 0;">
                <h3 style="color: #dc3545; margin-top: 0;">Emergency Details</h3>
                <p><strong>Type:</strong> {emergency_data['emergency_type']}</p>
                <p><strong>Patient:</strong> {emergency_data['patient_name']}</p>
                <p><strong>Contact:</strong> {emergency_data.get('contact_phone', 'Not provided')}</p>
                <p><strong>Delivery Address:</strong> {emergency_data['delivery_address']}</p>
                <p><strong>Details:</strong> {emergency_data['details']}</p>
            </div>
            
            <p style="background-color: #fff3cd; padding: 10px; border: 1px solid #ffeaa7;">
                <strong>⚠️ This is a genuine emergency request requiring immediate response.</strong>
            </p>
            
            <p style="margin: 20px 0;">
                <a href="https://your-domain.com/clinic/missions" 
                   style="background-color: #dc3545; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    🚁 RESPOND TO EMERGENCY
                </a>
            </p>
            
            <hr>
            <p style="color: #666; font-size: 12px;">
                SierraWings Emergency Response System<br>
                For technical support, call 117<br>
                Sierra Leone
            </p>
        </div>
    </div>
    """
    
    return send_email(clinic_email, "emergency@sierrawings.sl", subject, html_content=html_content)

def send_email_verification_otp(user_email, user_name, otp_code):
    """Send email verification OTP to user"""
    subject = "Verify Your Email - SierraWings"
    
    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;">
        <div style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Email Verification</h1>
            <p style="color: #e8f4f8; margin: 10px 0 0 0; font-size: 16px;">SierraWings Medical Platform</p>
        </div>
        
        <div style="padding: 40px 30px; background: #fafbfc;">
            <h2 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 22px;">Hello {user_name},</h2>
            
            <p style="color: #546e7a; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                To complete your registration with SierraWings, please verify your email address using the verification code below:
            </p>
            
            <div style="background: #ffffff; padding: 30px; border-radius: 12px; margin: 30px 0; text-align: center; border: 2px solid #e8f0fe; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);">
                <p style="color: #78909c; font-size: 14px; margin: 0 0 10px 0; text-transform: uppercase; font-weight: 500; letter-spacing: 1px;">Your Verification Code</p>
                <h1 style="color: #2c3e50; font-size: 36px; margin: 0; letter-spacing: 8px; font-family: 'Courier New', monospace; font-weight: 700;">
                    {otp_code}
                </h1>
                <p style="color: #78909c; font-size: 12px; margin: 10px 0 0 0;">Enter this code to verify your email</p>
            </div>
            
            <div style="background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #3498db;">
                <p style="color: #2c3e50; font-size: 14px; margin: 0; font-weight: 500;">
                    <strong>Important:</strong> This code will expire in 10 minutes for security reasons.
                </p>
            </div>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{url_for('auth.verify_email', _external=True)}" 
                   style="background: #3498db; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 500; font-size: 16px; transition: all 0.3s ease;">
                    Verify Email Address
                </a>
            </div>
            
            <div style="border-top: 1px solid #e1e8ed; padding-top: 20px; margin-top: 30px;">
                <p style="color: #78909c; font-size: 13px; margin: 0; text-align: center;">
                    If you didn't create an account with SierraWings, please ignore this email.<br>
                    For support, contact us at <a href="mailto:sierrawingsofficial@gmail.com" style="color: #3498db; text-decoration: none;">sierrawingsofficial@gmail.com</a> or call 034994803
                </p>
            </div>
        </div>
    </div>
    """
    
    return send_email(user_email, "noreply@sierrawings.com", subject, html_content=html_content)

def send_emergency_confirmation_email(clinic_email, clinic_name, emergency_data):
    """Send emergency confirmation email to clinic"""
    subject = f"Emergency Request Confirmed - Transaction {emergency_data['transaction_id']}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">✅ Emergency Request Confirmed</h1>
            <p style="color: #d4edda; margin: 10px 0 0 0;">Payment Processed Successfully</p>
        </div>
        
        <div style="padding: 30px; background: #ffffff;">
            <h2 style="color: #28a745;">Emergency Request Details</h2>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Mission ID:</strong> #{emergency_data['mission_id']}</p>
                <p><strong>Transaction ID:</strong> {emergency_data['transaction_id']}</p>
                <p><strong>Emergency Type:</strong> {emergency_data['emergency_type']}</p>
                <p><strong>Patient:</strong> {emergency_data['patient_name']}</p>
                <p><strong>Payment Amount:</strong> {emergency_data['total_amount']:.2f} NLE</p>
            </div>
            
            <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #c3e6cb;">
                <h3 style="color: #155724; margin-top: 0;">Payment Confirmed</h3>
                <p style="color: #155724;">Emergency payment has been processed. Please respond to this emergency request immediately.</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{url_for('clinic.dashboard', _external=True)}" 
                   style="background: #28a745; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    ACCEPT EMERGENCY REQUEST
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                This emergency request has been pre-paid and is ready for immediate dispatch.<br>
                Please check your clinic dashboard to accept and process this request.
            </p>
        </div>
    </div>
    """
    
    return send_email(clinic_email, "emergency@sierrawings.com", subject, html_content=html_content)