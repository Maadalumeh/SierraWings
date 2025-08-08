"""
SierraWings Notification Service
Handles all email notifications for delivery updates, OTP verification, and system alerts
"""

import os
import logging
from datetime import datetime, timedelta
from flask import current_app
from mail_service import send_email
from models import User, Mission, Drone

def send_delivery_notification(mission_id, notification_type, additional_info=None):
    """
    Send delivery notifications to all relevant parties
    notification_type: 'requested', 'accepted', 'assigned', 'in_transit', 'delivered', 'failed'
    """
    try:
        mission = Mission.query.get(mission_id)
        if not mission:
            logging.error(f"Mission {mission_id} not found for notification")
            return False
        
        patient = User.query.get(mission.patient_id)
        clinic = User.query.get(mission.assigned_clinic_id) if mission.assigned_clinic_id else None
        
        if notification_type == 'requested':
            # Notify patient that request was submitted
            if patient:
                send_delivery_request_confirmation(patient, mission)
            
            # Notify all clinics about new request
            clinics = User.query.filter_by(role='clinic').all()
            for clinic_user in clinics:
                send_new_delivery_request_notification(clinic_user, mission)
        
        elif notification_type == 'accepted':
            # Notify patient that clinic accepted the request
            if patient and clinic:
                send_delivery_accepted_notification(patient, clinic, mission)
        
        elif notification_type == 'assigned':
            # Notify all parties that drone is assigned
            if patient:
                send_delivery_assigned_notification(patient, mission)
            if clinic:
                send_delivery_assigned_notification(clinic, mission)
        
        elif notification_type == 'in_transit':
            # Notify patient that delivery is en route
            if patient:
                send_delivery_in_transit_notification(patient, mission)
        
        elif notification_type == 'delivered':
            # Notify all parties of successful delivery
            if patient:
                send_delivery_completed_notification(patient, mission, 'delivered')
            if clinic:
                send_delivery_completed_notification(clinic, mission, 'delivered')
        
        elif notification_type == 'failed':
            # Notify all parties of failed delivery
            if patient:
                send_delivery_completed_notification(patient, mission, 'failed')
            if clinic:
                send_delivery_completed_notification(clinic, mission, 'failed')
        
        return True
        
    except Exception as e:
        logging.error(f"Error sending delivery notification: {str(e)}")
        return False

def send_delivery_request_confirmation(patient, mission):
    """Send confirmation to patient that request was submitted"""
    subject = f"Delivery Request Confirmed - SierraWings #{mission.id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Delivery Request Confirmed</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .details {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>Delivery Request Confirmed</h2>
            </div>
            <div class="content">
                <p>Dear {patient.first_name},</p>
                <p>Your medical delivery request has been successfully submitted and is being reviewed by our partner clinics.</p>
                
                <div class="details">
                    <h3>Request Details:</h3>
                    <p><strong>Request ID:</strong> #{mission.id}</p>
                    <p><strong>Delivery Address:</strong> {mission.delivery_address}</p>
                    <p><strong>Requested Items:</strong> {mission.medical_items}</p>
                    <p><strong>Urgency:</strong> {mission.priority}</p>
                    <p><strong>Submitted:</strong> {mission.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>You will receive updates as your request progresses through our system.</p>
                
                <p>For questions, contact us at +232 34 994 803 or maadalumeh25@gmail.com</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(patient.email, subject, html_content)

def send_new_delivery_request_notification(clinic, mission):
    """Notify clinic about new delivery request"""
    patient = User.query.get(mission.patient_id)
    subject = f"New Delivery Request - SierraWings #{mission.id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>New Delivery Request</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .details {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .urgent {{ background-color: #ffebee; border-left: 4px solid #f44336; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>New Delivery Request</h2>
            </div>
            <div class="content">
                <p>Dear {clinic.first_name},</p>
                <p>A new medical delivery request requires your attention.</p>
                
                <div class="details {'urgent' if mission.priority == 'emergency' else ''}">
                    <h3>Request Details:</h3>
                    <p><strong>Request ID:</strong> #{mission.id}</p>
                    <p><strong>Patient:</strong> {patient.first_name} {patient.last_name}</p>
                    <p><strong>Delivery Address:</strong> {mission.delivery_address}</p>
                    <p><strong>Requested Items:</strong> {mission.medical_items}</p>
                    <p><strong>Urgency:</strong> {mission.priority.upper()}</p>
                    <p><strong>Submitted:</strong> {mission.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>Please log in to your dashboard to review and respond to this request.</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(clinic.email, subject, html_content)

def send_delivery_accepted_notification(patient, clinic, mission):
    """Notify patient that clinic accepted the request"""
    subject = f"Delivery Request Accepted - SierraWings #{mission.id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Delivery Request Accepted</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .success {{ background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>Delivery Request Accepted</h2>
            </div>
            <div class="content">
                <p>Dear {patient.first_name},</p>
                
                <div class="success">
                    <h3>✅ Great News!</h3>
                    <p>Your delivery request #{mission.id} has been accepted by {clinic.clinic_name or clinic.full_name}.</p>
                    <p>A drone will be assigned shortly for your delivery.</p>
                </div>
                
                <p>You will receive another notification when your delivery is en route.</p>
                
                <p>Track your delivery in real time through your dashboard.</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(patient.email, subject, html_content)

def send_delivery_assigned_notification(user, mission):
    """Notify user that drone is assigned to delivery"""
    subject = f"Drone Assigned - SierraWings #{mission.id}"
    
    drone = Drone.query.get(mission.assigned_drone_id) if mission.assigned_drone_id else None
    drone_name = drone.name if drone else "Medical Drone"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Drone Assigned</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .info {{ background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>Drone Assigned</h2>
            </div>
            <div class="content">
                <p>Dear {user.first_name},</p>
                
                <div class="info">
                    <h3>🚁 Drone Assigned</h3>
                    <p><strong>Drone:</strong> {drone_name}</p>
                    <p><strong>Delivery ID:</strong> #{mission.id}</p>
                    <p>Your delivery is being prepared and will be dispatched shortly.</p>
                </div>
                
                <p>You will receive real time updates as your delivery progresses.</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)

def send_delivery_in_transit_notification(patient, mission):
    """Notify patient that delivery is en route"""
    subject = f"Delivery En Route - SierraWings #{mission.id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Delivery En Route</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .transit {{ background-color: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>Delivery En Route</h2>
            </div>
            <div class="content">
                <p>Dear {patient.first_name},</p>
                
                <div class="transit">
                    <h3>🚁 Your Delivery is En Route</h3>
                    <p><strong>Delivery ID:</strong> #{mission.id}</p>
                    <p>Your medical supplies are now being delivered to your location.</p>
                    <p><strong>Expected Delivery:</strong> Within 30 minutes</p>
                </div>
                
                <p>Track your delivery in real time through your dashboard.</p>
                
                <p>Please be available to receive your delivery.</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(patient.email, subject, html_content)

def send_delivery_completed_notification(user, mission, status):
    """Notify user of completed delivery (success or failure)"""
    if status == 'delivered':
        subject = f"Delivery Completed - SierraWings #{mission.id}"
        status_message = "✅ Delivery Completed Successfully"
        status_color = "#4caf50"
        bg_color = "#e8f5e8"
        message = "Your medical supplies have been successfully delivered."
    else:
        subject = f"Delivery Failed - SierraWings #{mission.id}"
        status_message = "⚠️ Delivery Failed"
        status_color = "#f44336"
        bg_color = "#ffebee"
        message = "Unfortunately, your delivery could not be completed. Our team will contact you shortly."
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Delivery Update</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .status {{ background-color: {bg_color}; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {status_color}; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>Delivery Update</h2>
            </div>
            <div class="content">
                <p>Dear {user.first_name},</p>
                
                <div class="status">
                    <h3>{status_message}</h3>
                    <p><strong>Delivery ID:</strong> #{mission.id}</p>
                    <p>{message}</p>
                    <p><strong>Completed:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>Thank you for using SierraWings medical delivery service.</p>
                
                <p>For questions, contact us at +232 34 994 803 or maadalumeh25@gmail.com</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)

def send_otp_notification(user_email, user_name, otp_code, purpose="verification"):
    """Send OTP code for various purposes"""
    subject = f"Your SierraWings Verification Code - {otp_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SierraWings - Verification Code</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #2980B9; font-size: 28px; font-weight: bold; }}
            .content {{ color: #333; line-height: 1.6; }}
            .otp-code {{ background-color: #e3f2fd; padding: 30px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px solid #2196f3; }}
            .code {{ font-size: 36px; font-weight: bold; color: #2196f3; letter-spacing: 5px; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚁 SierraWings</div>
                <h2>Verification Code</h2>
            </div>
            <div class="content">
                <p>Dear {user_name},</p>
                <p>Your verification code for {purpose} is:</p>
                
                <div class="otp-code">
                    <div class="code">{otp_code}</div>
                    <p>This code will expire in 10 minutes.</p>
                </div>
                
                <p>Enter this code to complete your {purpose}.</p>
                
                <p>If you did not request this code, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>SierraWings - Emergency Medical Delivery Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)