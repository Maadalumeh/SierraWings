"""
SierraWings Maintenance Alert Service
Sends maintenance notifications to users via email
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask
from mail_service import send_email
from models import User, MaintenanceAlert
from app import db


def send_maintenance_alert(title, message, start_time, end_time, alert_type="scheduled"):
    """
    Send maintenance alert to all users via email
    
    Args:
        title: Alert title
        message: Detailed maintenance message
        start_time: Maintenance start time
        end_time: Maintenance end time
        alert_type: Type of alert ('scheduled', 'emergency', 'completed')
    """
    try:
        # Get all active users
        users = User.query.filter_by(is_active=True).all()
        
        # Create maintenance alert record
        alert = MaintenanceAlert(
            title=title,
            message=message,
            start_time=start_time,
            end_time=end_time,
            alert_type=alert_type,
            created_at=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()
        
        # Send email to each user
        successful_sends = 0
        failed_sends = 0
        
        for user in users:
            try:
                # Create personalized email content
                subject = f"🔧 SierraWings Maintenance Alert: {title}"
                
                # Role-specific greeting
                if user.role == 'patient':
                    greeting = f"Dear {user.first_name or user.username},"
                elif user.role == 'clinic':
                    greeting = f"Dear Healthcare Provider,"
                elif user.role == 'admin':
                    greeting = f"Dear Administrator,"
                else:
                    greeting = f"Dear {user.first_name or user.username},"
                
                # Format times
                start_formatted = start_time.strftime('%Y-%m-%d %H:%M GMT') if start_time else "TBD"
                end_formatted = end_time.strftime('%Y-%m-%d %H:%M GMT') if end_time else "TBD"
                
                # Create HTML email content
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: 'Inter', Arial, sans-serif;
                            line-height: 1.6;
                            color: #2c3e50;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #2980B9 0%, #3498DB 100%);
                            color: white;
                            padding: 30px;
                            border-radius: 10px 10px 0 0;
                            text-align: center;
                        }}
                        .content {{
                            background: white;
                            padding: 30px;
                            border: 1px solid #e0e0e0;
                            border-radius: 0 0 10px 10px;
                        }}
                        .alert-box {{
                            background: #fff3cd;
                            border: 1px solid #ffeaa7;
                            border-radius: 8px;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                        .alert-emergency {{
                            background: #f8d7da;
                            border: 1px solid #f5c6cb;
                        }}
                        .alert-completed {{
                            background: #d4edda;
                            border: 1px solid #c3e6cb;
                        }}
                        .time-info {{
                            background: #f8f9fa;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                        }}
                        .footer {{
                            text-align: center;
                            margin-top: 30px;
                            color: #7f8c8d;
                            font-size: 14px;
                        }}
                        .logo {{
                            width: 40px;
                            height: 40px;
                            display: inline-block;
                            margin-right: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🔧 SierraWings Maintenance Alert</h1>
                        <p>Medical Drone Delivery Platform</p>
                    </div>
                    
                    <div class="content">
                        <p>{greeting}</p>
                        
                        <div class="alert-box {'alert-emergency' if alert_type == 'emergency' else 'alert-completed' if alert_type == 'completed' else ''}">
                            <h3>{title}</h3>
                            <p>{message}</p>
                        </div>
                        
                        <div class="time-info">
                            <p><strong>⏰ Maintenance Schedule:</strong></p>
                            <p><strong>Start:</strong> {start_formatted}</p>
                            <p><strong>End:</strong> {end_formatted}</p>
                        </div>
                        
                        <h4>📋 What this means for you:</h4>
                        <ul>
                            <li><strong>Patients:</strong> Delivery requests may be temporarily unavailable</li>
                            <li><strong>Healthcare Providers:</strong> Mission management may be limited</li>
                            <li><strong>Administrators:</strong> System management functions may be restricted</li>
                        </ul>
                        
                        <h4>🔄 What we're doing:</h4>
                        <p>Our technical team is working to improve system performance and add new features to better serve Sierra Leone's medical delivery needs.</p>
                        
                        <p><strong>We apologize for any inconvenience and appreciate your patience.</strong></p>
                        
                        <div class="footer">
                            <p>SierraWings Medical Drone Delivery Platform<br>
                            Revolutionizing emergency medical logistics in Sierra Leone</p>
                            <p>📧 Contact: ramandhandumbuya01@gmail.com | 📱 +232 34 994 803</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Text version for fallback
                text_content = f"""
                {greeting}
                
                SIERRAWINGS MAINTENANCE ALERT: {title}
                
                {message}
                
                MAINTENANCE SCHEDULE:
                Start: {start_formatted}
                End: {end_formatted}
                
                IMPACT:
                - Patients: Delivery requests may be temporarily unavailable
                - Healthcare Providers: Mission management may be limited
                - Administrators: System management functions may be restricted
                
                We're working to improve system performance and add new features.
                
                We apologize for any inconvenience and appreciate your patience.
                
                SierraWings Medical Drone Delivery Platform
                Contact: ramandhandumbuya01@gmail.com | +232 34 994 803
                """
                
                # Send email
                if send_email(user.email, subject, html_content, text_content):
                    successful_sends += 1
                    logging.info(f"Maintenance alert sent successfully to {user.email}")
                else:
                    failed_sends += 1
                    logging.error(f"Failed to send maintenance alert to {user.email}")
                    
            except Exception as e:
                failed_sends += 1
                logging.error(f"Error sending maintenance alert to {user.email}: {str(e)}")
        
        # Send notification copy to official email
        try:
            official_subject = f"📧 Maintenance Alert Sent: {title}"
            official_body = f"""
Maintenance Alert Distribution Report

Title: {title}
Message: {message}
Type: {alert_type}
Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else 'Not specified'}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'Not specified'}

Delivery Statistics:
- Successful sends: {successful_sends}
- Failed sends: {failed_sends}
- Total recipients: {len(users)}

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            send_email('sierrawingsofficial@gmail.com', official_subject, official_body)
            
        except Exception as e:
            logging.error(f"Failed to send maintenance alert report to official email: {str(e)}")
        
        # Log summary
        logging.info(f"Maintenance alert sent: {successful_sends} successful, {failed_sends} failed")
        
        return {
            'success': True,
            'total_users': len(users),
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'alert_id': alert.id
        }
        
    except Exception as e:
        logging.error(f"Error in send_maintenance_alert: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def send_emergency_maintenance_alert(title, message):
    """Send immediate emergency maintenance alert"""
    return send_maintenance_alert(
        title=title,
        message=message,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        alert_type="emergency"
    )


def send_scheduled_maintenance_alert(title, message, start_time, end_time):
    """Send scheduled maintenance alert"""
    return send_maintenance_alert(
        title=title,
        message=message,
        start_time=start_time,
        end_time=end_time,
        alert_type="scheduled"
    )


def send_maintenance_completion_alert(title, message):
    """Send maintenance completion alert"""
    return send_maintenance_alert(
        title=title,
        message=message,
        start_time=None,
        end_time=None,
        alert_type="completed"
    )


# Example usage functions for admins
def quick_maintenance_alerts():
    """Predefined maintenance alert templates"""
    
    templates = {
        'system_update': {
            'title': 'System Update in Progress',
            'message': 'We are performing a system update to improve performance and add new features. The platform will be temporarily unavailable during this time.',
            'duration_hours': 2
        },
        'database_maintenance': {
            'title': 'Database Maintenance',
            'message': 'Scheduled database maintenance is being performed to optimize system performance. All data remains secure during this process.',
            'duration_hours': 1
        },
        'security_update': {
            'title': 'Security Enhancement',
            'message': 'We are implementing important security updates to protect your data and improve system security.',
            'duration_hours': 3
        },
        'server_migration': {
            'title': 'Server Migration',
            'message': 'We are migrating to more powerful servers to provide better service reliability and faster response times.',
            'duration_hours': 4
        }
    }
    
    return templates


if __name__ == "__main__":
    # Test maintenance alert
    test_result = send_maintenance_alert(
        title="Test Maintenance Alert",
        message="This is a test maintenance alert to verify the system is working properly.",
        start_time=datetime.utcnow() + timedelta(hours=1),
        end_time=datetime.utcnow() + timedelta(hours=3),
        alert_type="scheduled"
    )
    print(f"Test result: {test_result}")