import json
import logging
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import User, Drone, Mission, TelemetryLog, ClinicProfile, PaymentTransaction, HospitalPatient, HospitalService
from models_extensions import Feedback, SystemAlert, MaintenanceRecord, UpdateMessage, DismissedMessage
from drone_controller import DroneController
from weather_service import get_flight_conditions
from routes_maintenance import is_maintenance_mode, get_maintenance_message
from routes_updates import updates_bp
import subprocess
import os

# Hospital blueprint is registered in app.py, not here

# Initialize drone controller
drone_controller = DroneController()

def get_live_statistics():
    """Get real-time statistics from the database"""
    from sqlalchemy import func, extract
    
    # Get total successful deliveries
    successful_deliveries = Mission.query.filter_by(status='completed').count()
    
    # Get total deliveries (including failed ones for success rate calculation)
    total_deliveries = Mission.query.filter(
        Mission.status.in_(['completed', 'failed'])
    ).count()
    
    # Calculate success rate
    success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 100
    
    # Calculate average delivery time for completed missions
    completed_missions = Mission.query.filter_by(status='completed').all()
    
    total_delivery_time = 0
    delivery_count = 0
    
    for mission in completed_missions:
        if mission.created_at and mission.updated_at:
            delivery_time = (mission.updated_at - mission.created_at).total_seconds() / 60  # minutes
            total_delivery_time += delivery_time
            delivery_count += 1
    
    average_delivery_time = int(total_delivery_time / delivery_count) if delivery_count > 0 else 15
    
    # Format numbers for display
    if successful_deliveries >= 1000:
        deliveries_display = f"{successful_deliveries:,}+"
    else:
        deliveries_display = str(successful_deliveries) if successful_deliveries > 0 else "0"
    
    return {
        'successful_deliveries': deliveries_display,
        'average_delivery_time': average_delivery_time,
        'success_rate': f"{success_rate:.1f}%",
        'raw_success_rate': success_rate,
        'raw_deliveries': successful_deliveries,
        'raw_avg_time': average_delivery_time
    }

@app.route('/check-user-role', methods=['POST'])
def check_user_role():
    """Check user role for login form"""
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    
    if not username:
        return jsonify({'role': 'patient'})
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'role': user.role})
    else:
        return jsonify({'role': 'patient'})

@app.route('/')
def index():
    """Landing page - redirect based on user role"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'clinic':
            return redirect(url_for('hospital.dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
    
    # Get live statistics for homepage
    stats = get_live_statistics()
    return render_template('index.html', stats=stats)



@app.route('/api/stats')
def api_stats():
    """API endpoint for live statistics"""
    stats = get_live_statistics()
    return jsonify(stats)

@app.route('/learn-more')
def learn_more():
    """Learn more about SierraWings page"""
    return render_template('learn_more.html')

@app.route('/terms-of-service')
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms_of_service.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy_policy.html')

@app.route('/data-privacy')
@login_required
def data_privacy():
    """Data privacy rights management page"""
    return render_template('data_privacy.html')

@app.route('/communication-preferences', methods=['GET', 'POST'])
@login_required
def communication_preferences():
    """Communication preferences management"""
    if request.method == 'POST':
        current_user.marketing_consent = request.form.get('marketing_consent') == 'on'
        current_user.data_retention_consent = request.form.get('survey_feedback') == 'on'
        db.session.commit()
        flash('Communication preferences updated successfully.', 'success')
        return redirect(url_for('data_privacy'))
    
    return render_template('communication_preferences.html')

@app.route('/download-personal-data')
@login_required
def download_personal_data():
    """Download personal data in JSON format"""
    import json
    from flask import Response
    
    user_data = {
        'personal_information': {
            'username': current_user.username,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'phone': current_user.phone,
            'address': current_user.address,
            'date_of_birth': current_user.date_of_birth.isoformat() if current_user.date_of_birth else None,
            'role': current_user.role,
            'created_at': current_user.created_at.isoformat(),
            'updated_at': current_user.updated_at.isoformat()
        },
        'privacy_preferences': {
            'data_processing_consent': current_user.data_processing_consent,
            'marketing_consent': current_user.marketing_consent,
            'data_retention_consent': current_user.data_retention_consent
        }
    }
    
    # Add role-specific data
    if current_user.role == 'patient':
        user_data['medical_information'] = {
            'medical_id': current_user.medical_id,
            'emergency_contact': current_user.emergency_contact,
            'allergies': current_user.allergies
        }
        
        # Add mission history
        missions = Mission.query.filter_by(patient_id=current_user.id).all()
        user_data['mission_history'] = [
            {
                'id': mission.id,
                'mission_type': mission.mission_type,
                'priority': mission.priority,
                'status': mission.status,
                'requested_at': mission.requested_at.isoformat(),
                'completed_at': mission.completed_at.isoformat() if mission.completed_at else None
            } for mission in missions
        ]
    
    elif current_user.role == 'clinic':
        user_data['clinic_information'] = {
            'clinic_name': current_user.clinic_name,
            'clinic_license': current_user.clinic_license,
            'specialization': current_user.specialization
        }
    
    json_data = json.dumps(user_data, indent=2)
    
    return Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=personal_data_{current_user.username}.json'}
    )

@app.route('/export-data')
@login_required
def export_data():
    """Export data in portable format"""
    return redirect(url_for('download_personal_data'))

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    user_id = current_user.id
    username = current_user.username
    
    # Delete associated data
    Mission.query.filter_by(patient_id=user_id).delete()
    Mission.query.filter_by(assigned_clinic_id=user_id).delete()
    
    # Delete user account
    db.session.delete(current_user)
    db.session.commit()
    
    # Log the deletion for admin records
    print(f"Account deleted: {username} (ID: {user_id}) at {datetime.utcnow()}")
    
    flash('Your account has been successfully deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/file-complaint')
@login_required
def file_complaint():
    """File a data protection complaint"""
    return render_template('file_complaint.html')

@app.route('/admin/violations')
@login_required
def admin_violations():
    """Admin page to track user violations"""
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get users with violations
    users_with_violations = User.query.filter(User.violation_count > 0).all()
    
    return render_template('admin_violations.html', users=users_with_violations)

@app.route('/admin/deactivate-user/<int:user_id>', methods=['POST'])
@login_required
def deactivate_user(user_id):
    """Deactivate a user account"""
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason', 'Policy violation')
    
    user.is_active = False
    user.violation_count += 1
    user.last_violation_date = datetime.utcnow()
    user.violation_notes = f"{user.violation_notes or ''}\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: Account deactivated - {reason}"
    
    db.session.commit()
    
    flash(f'User {user.username} has been deactivated.', 'success')
    return redirect(url_for('admin_violations'))

@app.route('/admin/reactivate-user/<int:user_id>', methods=['POST'])
@login_required
def reactivate_user(user_id):
    """Reactivate a user account"""
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = True
    user.violation_notes = f"{user.violation_notes or ''}\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: Account reactivated by admin"
    
    db.session.commit()
    
    flash(f'User {user.username} has been reactivated.', 'success')
    return redirect(url_for('admin_violations'))





@app.route('/dashboard')
@login_required
def dashboard():
    """Generic dashboard redirect"""
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'clinic':
        return redirect(url_for('clinic_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    """Patient dashboard"""
    if current_user.role != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user's missions
    missions = Mission.query.filter_by(patient_id=current_user.id).order_by(Mission.created_at.desc()).all()
    
    # Get mission statistics
    total_missions = len(missions)
    completed_missions = len([m for m in missions if m.status == 'completed'])
    active_missions = len([m for m in missions if m.status in ['accepted', 'assigned', 'in_progress']])
    
    return render_template('patient_dashboard.html',
                         missions=missions,
                         total_missions=total_missions,
                         completed_missions=completed_missions,
                         active_missions=active_missions)

@app.route('/request-delivery', methods=['GET', 'POST'])
@login_required
def request_delivery():
    """Request medical delivery"""
    if current_user.role != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Get form data
            medical_items = request.form.get('medical_items', '').strip()
            urgency_level = request.form.get('urgency_level', 'standard')
            delivery_address = request.form.get('delivery_address', '').strip()
            contact_phone = request.form.get('contact_phone', '').strip()
            delivery_notes = request.form.get('delivery_notes', '').strip()
            
            # Validate required fields
            if not all([medical_items, urgency_level, delivery_address, contact_phone]):
                flash('Please fill in all required fields.', 'error')
                return render_template('request_delivery.html')
            
            # Create new mission
            mission = Mission(
                patient_id=current_user.id,
                medical_items=medical_items,
                priority=urgency_level,
                delivery_address=delivery_address,
                pickup_address=delivery_address,  # For now, same as delivery address
                special_instructions=delivery_notes,
                status='requested',
                mission_type='delivery',
                created_at=datetime.utcnow()
            )
            
            db.session.add(mission)
            db.session.commit()
            
            # Send notifications
            from notification_service import send_delivery_notification
            send_delivery_notification(mission.id, 'requested')
            
            flash('Delivery request submitted successfully! You will receive email updates as your request is processed.', 'success')
            return redirect(url_for('patient_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating delivery request: {str(e)}")
            flash('An error occurred while submitting your request. Please try again.', 'error')
    
    return render_template('request_delivery.html')

@app.route('/accept-mission/<int:mission_id>', methods=['POST'])
@login_required
def accept_mission(mission_id):
    """Clinic accepts a mission"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        mission = Mission.query.get_or_404(mission_id)
        
        if mission.status != 'requested':
            flash('This mission is no longer available.', 'error')
            return redirect(url_for('clinic_dashboard'))
        
        # Update mission
        mission.status = 'accepted'
        mission.assigned_clinic_id = current_user.id
        mission.accepted_at = datetime.utcnow()
        db.session.commit()
        
        # Send notifications
        from notification_service import send_delivery_notification
        send_delivery_notification(mission.id, 'accepted')
        
        flash('Mission accepted successfully! The patient has been notified.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error accepting mission: {str(e)}")
        flash('An error occurred while accepting the mission.', 'error')
    
    return redirect(url_for('clinic_dashboard'))

@app.route('/assign-drone/<int:mission_id>', methods=['POST'])
@login_required
def assign_drone(mission_id):
    """Assign drone to mission"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        mission = Mission.query.get_or_404(mission_id)
        drone_id = request.form.get('drone_id')
        
        if not drone_id:
            flash('Please select a drone.', 'error')
            return redirect(url_for('clinic_dashboard'))
        
        # Check if drone is available
        drone = Drone.query.get_or_404(drone_id)
        if drone.status != 'available':
            flash('Selected drone is not available.', 'error')
            return redirect(url_for('clinic_dashboard'))
        
        # Update mission and drone
        mission.assigned_drone_id = drone_id
        mission.status = 'assigned'
        drone.status = 'assigned'
        db.session.commit()
        
        # Send notifications
        from notification_service import send_delivery_notification
        send_delivery_notification(mission.id, 'assigned')
        
        flash('Drone assigned successfully! All parties have been notified.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error assigning drone: {str(e)}")
        flash('An error occurred while assigning the drone.', 'error')
    
    return redirect(url_for('clinic_dashboard'))

@app.route('/start-delivery/<int:mission_id>', methods=['POST'])
@login_required
def start_delivery(mission_id):
    """Start delivery (drone takes off)"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        mission = Mission.query.get_or_404(mission_id)
        
        if mission.status != 'assigned':
            flash('Mission must be assigned before starting delivery.', 'error')
            return redirect(url_for('clinic_dashboard'))
        
        # Update mission and drone status
        mission.status = 'in_transit'
        mission.started_at = datetime.utcnow()
        
        if mission.assigned_drone_id:
            drone = Drone.query.get(mission.assigned_drone_id)
            if drone:
                drone.status = 'in_flight'
        
        db.session.commit()
        
        # Send notifications
        from notification_service import send_delivery_notification
        send_delivery_notification(mission.id, 'in_transit')
        
        flash('Delivery started! The patient has been notified that their delivery is en route.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error starting delivery: {str(e)}")
        flash('An error occurred while starting the delivery.', 'error')
    
    return redirect(url_for('clinic_dashboard'))

@app.route('/complete-delivery/<int:mission_id>', methods=['POST'])
@login_required
def complete_delivery(mission_id):
    """Complete delivery (mark as delivered)"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        mission = Mission.query.get_or_404(mission_id)
        delivery_status = request.form.get('delivery_status', 'delivered')  # 'delivered' or 'failed'
        
        if mission.status != 'in_transit':
            flash('Mission must be in transit to complete delivery.', 'error')
            return redirect(url_for('clinic_dashboard'))
        
        # Update mission
        mission.status = 'completed' if delivery_status == 'delivered' else 'failed'
        mission.completed_at = datetime.utcnow()
        
        # Update drone status
        if mission.assigned_drone_id:
            drone = Drone.query.get(mission.assigned_drone_id)
            if drone:
                drone.status = 'available'
        
        db.session.commit()
        
        # Send notifications
        from notification_service import send_delivery_notification
        send_delivery_notification(mission.id, delivery_status)
        
        status_message = 'delivered successfully' if delivery_status == 'delivered' else 'failed'
        flash(f'Delivery {status_message}! All parties have been notified.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error completing delivery: {str(e)}")
        flash('An error occurred while completing the delivery.', 'error')
    
    return redirect(url_for('clinic_dashboard'))

@app.route('/search-hospitals')
@login_required
def search_hospitals():
    """Hospital search page for patients"""
    if current_user.role != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    service = request.args.get('service', '')
    
    # Base query for hospitals
    query = User.query.filter_by(role='clinic', is_active=True, email_verified=True)
    
    if search:
        query = query.filter(
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%')) |
            (User.clinic_name.ilike(f'%{search}%'))
        )
    
    hospitals = query.all()
    
    # Get hospital profiles and services
    hospital_data = []
    for hospital in hospitals:
        profile = ClinicProfile.query.filter_by(user_id=hospital.id).first()
        services = db.session.query(HospitalService).filter_by(hospital_id=hospital.id, available=True).all()
        
        # Filter by location if specified
        if location and profile:
            if location.lower() not in (profile.city or '').lower() and location.lower() not in (profile.region or '').lower():
                continue
        
        # Filter by service if specified
        if service:
            service_match = any(s.service_name.lower().find(service.lower()) >= 0 for s in services)
            if not service_match:
                continue
        
        hospital_info = {
            'id': hospital.id,
            'name': hospital.clinic_name or f"{hospital.first_name} {hospital.last_name}",
            'email': hospital.email,
            'phone': hospital.phone,
            'address': profile.address if profile else None,
            'city': profile.city if profile else None,
            'region': profile.region if profile else None,
            'services': services,
            'operating_hours': json.loads(profile.operating_hours) if profile and profile.operating_hours else None,
            'verified': profile.verified if profile else False,
            'profile': profile
        }
        hospital_data.append(hospital_info)
    
    return render_template('search_hospitals.html', 
                         hospitals=hospital_data,
                         search=search,
                         location=location,
                         service=service)

@app.route('/clinic/dashboard')
@login_required
def clinic_dashboard():
    """Clinic dashboard"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pending missions
    pending_missions = Mission.query.filter_by(status='requested').order_by(Mission.created_at.desc()).all()
    
    # Get clinic's handled missions
    handled_missions = Mission.query.filter_by(assigned_clinic_id=current_user.id).order_by(Mission.created_at.desc()).all()
    
    # Get available drones
    available_drones = Drone.query.filter_by(status='available').all()
    
    # Get statistics
    total_handled = len(handled_missions)
    completed_today = len([m for m in handled_missions if m.completed_at and m.completed_at.date() == datetime.now().date()])
    
    return render_template('clinic_dashboard.html',
                         pending_missions=pending_missions,
                         handled_missions=handled_missions,
                         available_drones=available_drones,
                         total_handled=total_handled,
                         completed_today=completed_today)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get system statistics
    total_users = User.query.count()
    total_drones = Drone.query.count()
    total_missions = Mission.query.count()
    active_missions = Mission.query.filter(Mission.status.in_(['accepted', 'assigned', 'in_progress'])).count()
    
    # Get recent activities
    recent_missions = Mission.query.order_by(Mission.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get drone status
    available_drones = Drone.query.filter_by(status='available').count()
    in_flight_drones = Drone.query.filter_by(status='in_flight').count()
    maintenance_drones = Drone.query.filter_by(status='maintenance').count()
    
    # Get feedback data
    total_feedback = Feedback.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    recent_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    
    # Get current time for system status
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get all drones for wireless connection
    all_drones = Drone.query.all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_drones=total_drones,
                         total_missions=total_missions,
                         active_missions=active_missions,
                         recent_missions=recent_missions,
                         recent_users=recent_users,
                         available_drones=all_drones,
                         in_flight_drones=in_flight_drones,
                         maintenance_drones=maintenance_drones,
                         total_feedback=total_feedback,
                         pending_feedback=pending_feedback,
                         recent_feedback=recent_feedback,
                         current_time=current_time)

@app.route('/admin/feedback')
@login_required
def admin_feedback():
    """Admin feedback management"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all feedback with sorting
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    status_filter = request.args.get('status', 'all')
    
    query = Feedback.query
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Apply sorting
    if sort_by == 'created_at':
        if order == 'asc':
            query = query.order_by(Feedback.created_at.asc())
        else:
            query = query.order_by(Feedback.created_at.desc())
    elif sort_by == 'rating':
        if order == 'asc':
            query = query.order_by(Feedback.rating.asc())
        else:
            query = query.order_by(Feedback.rating.desc())
    elif sort_by == 'status':
        query = query.order_by(Feedback.status)
    
    feedback_list = query.all()
    
    # Get statistics
    total_feedback = Feedback.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    reviewed_feedback = Feedback.query.filter_by(status='reviewed').count()
    resolved_feedback = Feedback.query.filter_by(status='resolved').count()
    
    return render_template('admin_feedback.html',
                         feedback_list=feedback_list,
                         total_feedback=total_feedback,
                         pending_feedback=pending_feedback,
                         reviewed_feedback=reviewed_feedback,
                         resolved_feedback=resolved_feedback,
                         current_sort=sort_by,
                         current_order=order,
                         current_status=status_filter)

@app.route('/admin/feedback/<int:feedback_id>/update', methods=['POST'])
@login_required
def update_feedback_status(feedback_id):
    """Update feedback status"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    feedback = Feedback.query.get_or_404(feedback_id)
    new_status = request.form.get('status')
    admin_response = request.form.get('admin_response')
    
    if new_status in ['pending', 'reviewed', 'resolved']:
        feedback.status = new_status
        if admin_response:
            feedback.admin_response = admin_response
        feedback.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Feedback status updated successfully!', 'success')
    else:
        flash('Invalid status.', 'error')
    
    return redirect(url_for('admin_feedback'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        # Update user profile
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        
        # Role-specific updates
        if current_user.role == 'patient':
            current_user.emergency_contact = request.form.get('emergency_contact')
            current_user.allergies = request.form.get('allergies')
            current_user.medical_id = request.form.get('medical_id')
        elif current_user.role == 'clinic':
            current_user.clinic_name = request.form.get('clinic_name')
            current_user.clinic_license = request.form.get('clinic_license')
            current_user.specialization = request.form.get('specialization')
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=current_user)

# Missing admin routes
@app.route('/admin/manage-users')
@login_required
def manage_users():
    """Manage users page"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/manage-drones')
@login_required
def manage_drones():
    """Manage drones page"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    drones = Drone.query.all()
    return render_template('manage_drones.html', drones=drones)

@app.route('/admin/system-settings')
@login_required
def system_settings():
    """System settings page"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('system_settings.html')

# Patient records route
@app.route('/patient-records')
@login_required
def patient_records():
    """Patient records page (clinic only)"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all patients for now - in real app, filter by clinic
    patients = User.query.filter_by(role='patient').all()
    return render_template('patient_records.html', patients=patients)

# Live tracking route (clinic and admin access)
@app.route('/live-tracking')
@login_required
def live_tracking():
    """Live tracking page"""
    if current_user.role not in ['clinic', 'admin']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    drones = Drone.query.filter_by(status='in_flight').all()
    return render_template('live_tracking.html', drones=drones)

# Missing mission routes
@app.route('/mission/<int:mission_id>/view')
@login_required
def view_mission(mission_id):
    """View mission details"""
    mission = Mission.query.get_or_404(mission_id)
    
    # Check access permissions
    if current_user.role == 'patient' and mission.patient_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    elif current_user.role == 'clinic' and mission.assigned_clinic_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('view_mission.html', mission=mission)



@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings management"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update basic profile information
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.phone = request.form.get('phone', '').strip()
            current_user.address = request.form.get('address', '').strip()
            
            # Role-specific updates
            if current_user.role == 'patient':
                current_user.medical_id = request.form.get('medical_id', '').strip()
                current_user.emergency_contact = request.form.get('emergency_contact', '').strip()
                current_user.allergies = request.form.get('allergies', '').strip()
            elif current_user.role == 'clinic':
                current_user.clinic_name = request.form.get('clinic_name', '').strip()
                current_user.clinic_license = request.form.get('clinic_license', '').strip()
                current_user.specialization = request.form.get('specialization', '').strip()
            
            current_user.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'error')
            else:
                current_user.set_password(new_password)
                current_user.updated_at = datetime.utcnow()
                db.session.commit()
                flash('Password changed successfully!', 'success')
        
        elif action == 'update_notifications':
            # Add notification preferences handling here
            flash('Notification preferences updated!', 'success')
        
        elif action == 'deactivate_account':
            if current_user.role != 'admin':  # Prevent admin self-deactivation
                current_user.is_active = False
                current_user.updated_at = datetime.utcnow()
                db.session.commit()
                logout_user()
                flash('Your account has been deactivated.', 'info')
                return redirect(url_for('index'))
            else:
                flash('Admin accounts cannot be deactivated.', 'error')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=current_user)



@app.route('/track-mission/<int:mission_id>')
@login_required
def track_mission(mission_id):
    """Track specific mission"""
    mission = Mission.query.get_or_404(mission_id)
    
    # Check access permissions
    if current_user.role == 'patient' and mission.patient_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    elif current_user.role == 'clinic' and mission.assigned_clinic_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get telemetry data if drone is assigned
    telemetry_data = []
    if mission.drone_id:
        telemetry_data = TelemetryLog.query.filter_by(
            drone_id=mission.drone_id,
            mission_id=mission_id
        ).order_by(TelemetryLog.timestamp.desc()).limit(100).all()
    
    return render_template('track_mission.html', mission=mission, telemetry_data=telemetry_data)



@app.route('/api/drones/positions', methods=['GET'])
@login_required
def get_drone_positions():
    """Get current GPS positions for all drones"""
    if current_user.role not in ['admin', 'clinic']:
        return jsonify({'error': 'Access denied'}), 403
    
    drones = Drone.query.all()
    positions = []
    
    for drone in drones:
        positions.append({
            'id': drone.id,
            'name': drone.name,
            'location_lat': drone.location_lat,
            'location_lon': drone.location_lon,
            'altitude': drone.altitude,
            'battery_level': drone.battery_level,
            'status': drone.status,
            'last_seen': drone.last_seen.isoformat() if drone.last_seen else None
        })
    
    return jsonify(positions)

@app.route('/api/missions/<int:mission_id>/path', methods=['GET'])
@login_required
def get_mission_path(mission_id):
    """Get mission path for tracking"""
    mission = Mission.query.get_or_404(mission_id)
    
    # Check access permissions
    if current_user.role == 'patient' and mission.patient_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    elif current_user.role == 'clinic' and mission.assigned_clinic_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get telemetry path
    telemetry_logs = TelemetryLog.query.filter_by(mission_id=mission_id).order_by(TelemetryLog.timestamp).all()
    
    path = []
    for log in telemetry_logs:
        if log.latitude and log.longitude:
            path.append([log.latitude, log.longitude])
    
    # Mission waypoints
    pickup = None
    if mission.pickup_lat and mission.pickup_lon:
        pickup = {
            'lat': mission.pickup_lat,
            'lon': mission.pickup_lon,
            'address': mission.pickup_address
        }
    
    delivery = None
    if mission.delivery_lat and mission.delivery_lon:
        delivery = {
            'lat': mission.delivery_lat,
            'lon': mission.delivery_lon,
            'address': mission.delivery_address
        }
    
    return jsonify({
        'path': path,
        'pickup': pickup,
        'delivery': delivery,
        'mission_id': mission_id,
        'status': mission.status
    })

@app.route('/manage-missions')
@login_required
def manage_missions():
    """Manage missions (clinic interface)"""
    if current_user.role != 'clinic':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get missions based on status
    pending_missions = Mission.query.filter_by(status='requested').order_by(Mission.created_at.desc()).all()
    active_missions = Mission.query.filter_by(assigned_clinic_id=current_user.id).filter(
        Mission.status.in_(['accepted', 'assigned', 'in_progress'])
    ).order_by(Mission.created_at.desc()).all()
    
    return render_template('manage_missions.html', 
                         pending_missions=pending_missions,
                         active_missions=active_missions)

@app.route('/user-management')
@login_required
def user_management():
    """User management (admin only)"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('user_management.html', users=users)

@app.route('/drone-management')
@login_required
def drone_management():
    """Drone management (admin only)"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    drones = Drone.query.order_by(Drone.created_at.desc()).all()
    return render_template('drone_management.html', drones=drones)

@app.route('/emergency', methods=['GET', 'POST'])
@login_required
def emergency():
    """Emergency request page"""
    if current_user.role != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Get form data
            emergency_type = request.form.get('emergency_type', 'medical')
            medical_items = request.form.get('medical_items', '').strip()
            delivery_address = request.form.get('delivery_address', '').strip()
            contact_phone = request.form.get('contact_phone', '').strip()
            emergency_notes = request.form.get('emergency_notes', '').strip()
            
            # Validate required fields
            if not all([medical_items, delivery_address, contact_phone]):
                flash('Please fill in all required fields.', 'error')
                return render_template('emergency.html')
            
            # Create emergency mission
            mission = Mission(
                patient_id=current_user.id,
                medical_items=medical_items,
                priority='emergency',
                delivery_address=delivery_address,
                pickup_address='Emergency Medical Center - Freetown',
                special_instructions=f"EMERGENCY DELIVERY - PRIORITY 1\n\nDetails: {emergency_notes}",
                status='requested',
                mission_type='emergency',
                created_at=datetime.utcnow()
            )
            
            db.session.add(mission)
            db.session.commit()
            
            # Send notifications
            from notification_service import send_delivery_notification
            send_delivery_notification(mission.id, 'requested')
            
            flash('Emergency request submitted successfully! All clinics have been notified.', 'success')
            return redirect(url_for('patient_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating emergency request: {str(e)}")
            flash('An error occurred while submitting your request. Please try again.', 'error')
    
    return render_template('emergency.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    """Submit feedback"""
    if request.method == 'POST':
        feedback_entry = Feedback(
            user_id=current_user.id,
            subject=request.form.get('subject'),
            message=request.form.get('message'),
            rating=int(request.form.get('rating', 5)),
            category=request.form.get('category', 'general')
        )
        
        db.session.add(feedback_entry)
        db.session.commit()
        
        # Send feedback automatically to official email
        try:
            from mail_service import send_email
            feedback_email_body = f"""
New Feedback Received from SierraWings Platform

From: {current_user.first_name} {current_user.last_name} ({current_user.username})
Email: {current_user.email}
Role: {current_user.role.title()}
Category: {request.form.get('category', 'general').title()}
Rating: {request.form.get('rating', 5)}/5 stars
Subject: {request.form.get('subject')}

Message:
{request.form.get('message')}

Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review and respond accordingly.
            """
            
            send_email(
                to_email='sierrawingsofficial@gmail.com',
                subject=f'New SierraWings Feedback: {request.form.get("subject")}',
                text_content=feedback_email_body
            )
            
            flash('Thank you for your feedback! We will review it soon.', 'success')
        except Exception as e:
            logging.error(f'Failed to send feedback email: {str(e)}')
            flash('Feedback submitted but email notification failed. We will still review your feedback.', 'warning')
        
        return redirect(url_for('dashboard'))
    
    return render_template('feedback.html')


@app.route('/admin/maintenance-alerts')
@login_required
def maintenance_alerts():
    """Admin maintenance alerts management"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get recent maintenance alerts
    from models_extensions import MaintenanceAlert
    alerts = MaintenanceAlert.query.order_by(MaintenanceAlert.created_at.desc()).limit(20).all()
    
    return render_template('admin_maintenance_alerts.html', alerts=alerts)


@app.route('/admin/send-maintenance-alert', methods=['GET', 'POST'])
@login_required
def send_maintenance_alert():
    """Send maintenance alert to all users"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        alert_type = request.form.get('alert_type', 'scheduled')
        
        # Parse dates if provided
        start_time = None
        end_time = None
        
        if request.form.get('start_time'):
            try:
                start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        
        if request.form.get('end_time'):
            try:
                end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        
        if not title or not message:
            flash('Title and message are required.', 'error')
            return render_template('admin_send_maintenance_alert.html')
        
        # Send maintenance alert
        from maintenance_service import send_maintenance_alert as send_alert
        result = send_alert(title, message, start_time, end_time, alert_type)
        
        if result['success']:
            flash(f'Maintenance alert sent successfully! Delivered to {result["successful_sends"]} users.', 'success')
            return redirect(url_for('maintenance_alerts'))
        else:
            flash(f'Error sending maintenance alert: {result["error"]}', 'error')
    
    return render_template('admin_send_maintenance_alert.html')


@app.route('/admin/quick-maintenance-alert', methods=['POST'])
@login_required
def quick_maintenance_alert():
    """Send quick maintenance alert using predefined templates"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    alert_template = request.form.get('template')
    
    from maintenance_service import quick_maintenance_alerts, send_scheduled_maintenance_alert
    templates = quick_maintenance_alerts()
    
    if alert_template in templates:
        template_data = templates[alert_template]
        start_time = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes from now
        end_time = start_time + timedelta(hours=template_data['duration_hours'])
        
        result = send_scheduled_maintenance_alert(
            template_data['title'],
            template_data['message'],
            start_time,
            end_time
        )
        
        if result['success']:
            flash(f'Quick maintenance alert sent! Delivered to {result["successful_sends"]} users.', 'success')
        else:
            flash(f'Error sending quick alert: {result["error"]}', 'error')
    else:
        flash('Invalid template selected.', 'error')
    
    return redirect(url_for('maintenance_alerts'))


@app.route('/admin/maintenance-timeline')
@login_required
def maintenance_timeline():
    """Interactive maintenance timeline visualization"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('maintenance_timeline.html')


@app.route('/sw.js')
def service_worker():
    """Serve the service worker file"""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# API Routes
@app.route('/api/missions/<int:mission_id>/accept', methods=['POST'])
@login_required
def api_accept_mission(mission_id):
    """Accept a mission (clinic only)"""
    if current_user.role != 'clinic':
        return jsonify({'error': 'Access denied'}), 403
    
    mission = Mission.query.get_or_404(mission_id)
    
    if mission.status != 'requested':
        return jsonify({'error': 'Mission cannot be accepted'}), 400
    
    mission.status = 'accepted'
    mission.assigned_clinic_id = current_user.id
    db.session.commit()
    
    return jsonify({'message': 'Mission accepted successfully'})

@app.route('/api/missions/<int:mission_id>/reject', methods=['POST'])
@login_required
def reject_mission(mission_id):
    """Reject a mission (clinic only)"""
    if current_user.role != 'clinic':
        return jsonify({'error': 'Access denied'}), 403
    
    mission = Mission.query.get_or_404(mission_id)
    
    if mission.status != 'requested':
        return jsonify({'error': 'Mission cannot be rejected'}), 400
    
    mission.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'message': 'Mission rejected'})

# Weather API Routes
@app.route('/api/weather/conditions')
@login_required
def api_weather_conditions():
    """Get current weather conditions and flight safety assessment"""
    try:
        lat = request.args.get('lat', 8.4606, type=float)
        lon = request.args.get('lon', -11.7799, type=float)
        
        conditions = get_flight_conditions(lat, lon)
        return jsonify(conditions)
    except Exception as e:
        logging.error(f"Weather API error: {str(e)}")
        return jsonify({'error': 'Weather data unavailable'}), 500

@app.route('/api/weather/flight-status')
@login_required
def api_flight_status():
    """Get flight status for all user modes"""
    try:
        conditions = get_flight_conditions()
        return jsonify({
            'flight_safe': conditions['safety_level'] == 'Safe to Fly',
            'status': conditions['safety_level'],
            'color': conditions['safety_color'],
            'icon': conditions['safety_icon'],
            'details': {
                'temperature': conditions['temperature'],
                'wind_speed': conditions['wind_speed'],
                'visibility': conditions['visibility'],
                'conditions': conditions['conditions']
            },
            'updated_at': conditions['updated_at']
        })
    except Exception as e:
        logging.error(f"Flight status API error: {str(e)}")
        return jsonify({'error': 'Flight status unavailable'}), 500

# Drone Management and Wireless Connection Routes
@app.route('/api/drones/connect', methods=['POST'])
@login_required
def api_connect_drone():
    """Connect to drone via wireless (Raspberry Pi + Pixhawk)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        drone_id = request.json.get('drone_id')
        connection_type = request.json.get('connection_type', 'wifi')  # wifi or cellular
        
        drone = Drone.query.get_or_404(drone_id)
        
        # Simulate wireless connection
        if connection_type == 'wifi':
            drone.wireless_status = 'connected_wifi'
            drone.connection_strength = 85
        else:
            drone.wireless_status = 'connected_cellular'
            drone.connection_strength = 72
        
        drone.last_connected = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Drone {drone.name} connected via {connection_type}',
            'status': drone.wireless_status,
            'strength': drone.connection_strength
        })
    except Exception as e:
        logging.error(f"Drone connection error: {str(e)}")
        return jsonify({'error': 'Connection failed'}), 500

@app.route('/api/drones/disconnect', methods=['POST'])
@login_required
def api_disconnect_drone():
    """Disconnect drone wireless connection"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        drone_id = request.json.get('drone_id')
        drone = Drone.query.get_or_404(drone_id)
        
        drone.wireless_status = 'disconnected'
        drone.connection_strength = 0
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Drone {drone.name} disconnected',
            'status': drone.wireless_status
        })
    except Exception as e:
        logging.error(f"Drone disconnection error: {str(e)}")
        return jsonify({'error': 'Disconnection failed'}), 500

@app.route('/api/drones/status')
@login_required
def api_drone_status():
    """Get real-time drone connection status"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        drones = Drone.query.all()
        drone_status = []
        
        for drone in drones:
            drone_status.append({
                'id': drone.id,
                'name': drone.name,
                'model': drone.model,
                'status': drone.status,
                'wireless_status': getattr(drone, 'wireless_status', 'disconnected'),
                'connection_strength': getattr(drone, 'connection_strength', 0),
                'last_connected': drone.last_connected.isoformat() if hasattr(drone, 'last_connected') and drone.last_connected else None,
                'battery_level': getattr(drone, 'battery_level', 0),
                'location': {
                    'lat': getattr(drone, 'current_latitude', 0),
                    'lon': getattr(drone, 'current_longitude', 0)
                }
            })
        
        return jsonify({
            'drones': drone_status,
            'summary': {
                'total': len(drones),
                'connected': len([d for d in drone_status if d['wireless_status'] in ['connected_wifi', 'connected_cellular']]),
                'available': len([d for d in drone_status if d['status'] == 'available']),
                'in_flight': len([d for d in drone_status if d['status'] == 'in_flight'])
            }
        })
    except Exception as e:
        logging.error(f"Drone status API error: {str(e)}")
        return jsonify({'error': 'Status unavailable'}), 500

@app.route('/api/missions/<int:mission_id>/dispatch', methods=['POST'])
@login_required
def dispatch_mission(mission_id):
    """Dispatch drone for mission"""
    if current_user.role != 'clinic':
        return jsonify({'error': 'Access denied'}), 403
    
    mission = Mission.query.get_or_404(mission_id)
    drone_id = request.json.get('drone_id')
    
    if mission.status != 'accepted':
        return jsonify({'error': 'Mission not ready for dispatch'}), 400
    
    drone = Drone.query.get_or_404(drone_id)
    
    if drone.status != 'available':
        return jsonify({'error': 'Drone not available'}), 400
    
    # Assign drone to mission
    mission.drone_id = drone_id
    mission.status = 'assigned'
    mission.started_at = datetime.utcnow()
    
    # Update drone status
    drone.status = 'in_flight'
    
    db.session.commit()
    
    return jsonify({'message': 'Mission dispatched successfully'})

@app.route('/api/drones/locations')
@login_required
def api_drone_locations():
    """Get current drone locations for map display"""
    drones = Drone.query.filter_by(status='available').all()
    
    drone_data = []
    for drone in drones:
        drone_info = {
            'id': drone.id,
            'name': drone.name,
            'status': drone.status,
            'location_lat': drone.location_lat,
            'location_lon': drone.location_lon,
            'battery_level': drone.battery_level,
            'last_seen': drone.last_seen.isoformat() if drone.last_seen else None
        }
        drone_data.append(drone_info)
    
    return jsonify({'drones': drone_data})

@app.route('/api/telemetry')
@login_required
def get_telemetry():
    """Get telemetry data for a mission"""
    mission_id = request.args.get('mission_id')
    
    if not mission_id:
        return jsonify({'error': 'Mission ID required'}), 400
    
    mission = Mission.query.get_or_404(mission_id)
    
    # Check access permissions
    if current_user.role == 'patient' and mission.patient_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    elif current_user.role == 'clinic' and mission.assigned_clinic_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if not mission.drone_id:
        return jsonify({'error': 'No drone assigned to mission'}), 400
    
    # Get recent telemetry data
    telemetry = TelemetryLog.query.filter_by(
        drone_id=mission.drone_id,
        mission_id=mission_id
    ).order_by(TelemetryLog.timestamp.desc()).limit(50).all()
    
    telemetry_data = []
    for log in telemetry:
        telemetry_data.append({
            'timestamp': log.timestamp.isoformat(),
            'latitude': log.latitude,
            'longitude': log.longitude,
            'altitude': log.altitude,
            'heading': log.heading,
            'speed': log.speed,
            'battery_level': log.battery_level,
            'signal_strength': log.signal_strength,
            'flight_mode': log.flight_mode,
            'armed': log.armed
        })
    
    return jsonify({
        'mission_id': mission_id,
        'drone_id': mission.drone_id,
        'telemetry': telemetry_data
    })

@app.route('/api/drones')
@login_required
def get_drones():
    """Get list of all drones"""
    if current_user.role not in ['admin', 'clinic']:
        return jsonify({'error': 'Access denied'}), 403
    
    drones = Drone.query.all()
    
    drone_list = []
    for drone in drones:
        drone_list.append({
            'id': drone.id,
            'name': drone.name,
            'model': drone.model,
            'serial_number': drone.serial_number,
            'status': drone.status,
            'battery_level': drone.battery_level,
            'max_payload': drone.max_payload,
            'flight_time': drone.flight_time,
            'location': {
                'lat': drone.location_lat,
                'lon': drone.location_lon
            },
            'last_seen': drone.last_seen.isoformat() if drone.last_seen else None
        })
    
    return jsonify({'drones': drone_list})

@app.route('/api/drones/available')
@login_required
def get_available_drones():
    """Get list of available drones"""
    if current_user.role not in ['admin', 'clinic']:
        return jsonify({'error': 'Access denied'}), 403
    
    drones = Drone.query.filter_by(status='available').all()
    
    drone_list = []
    for drone in drones:
        drone_list.append({
            'id': drone.id,
            'name': drone.name,
            'model': drone.model,
            'battery_level': drone.battery_level,
            'max_payload': drone.max_payload,
            'location': {
                'lat': drone.location_lat,
                'lon': drone.location_lon
            }
        })
    
    return jsonify({'drones': drone_list})

@app.route('/missions')
@login_required
def get_missions():
    """Display missions list page"""
    if current_user.role == 'patient':
        # Patient missions
        missions = Mission.query.filter_by(patient_id=current_user.id).order_by(Mission.requested_at.desc()).all()
    elif current_user.role == 'clinic':
        # Clinic missions
        missions = Mission.query.filter_by(assigned_clinic_id=current_user.id).order_by(Mission.requested_at.desc()).all()
    else:
        # Admin missions (all)
        missions = Mission.query.order_by(Mission.requested_at.desc()).all()
    
    return render_template('missions_list.html', missions=missions)

@app.route('/api/missions')
@login_required
def get_missions_api():
    """Get list of missions as JSON"""
    if current_user.role == 'patient':
        # Patient missions
        missions = Mission.query.filter_by(patient_id=current_user.id).all()
    elif current_user.role == 'clinic':
        # Clinic missions
        missions = Mission.query.filter_by(assigned_clinic_id=current_user.id).all()
    else:
        # Admin missions (all)
        missions = Mission.query.all()
    
    mission_list = []
    for mission in missions:
        mission_list.append({
            'id': mission.id,
            'mission_type': mission.mission_type,
            'priority': mission.priority,
            'status': mission.status,
            'pickup_address': mission.pickup_address,
            'delivery_address': mission.delivery_address,
            'requested_at': mission.requested_at.isoformat() if mission.requested_at else None,
            'scheduled_at': mission.scheduled_at.isoformat() if mission.scheduled_at else None,
            'patient_id': mission.patient_id,
            'assigned_clinic_id': mission.assigned_clinic_id,
            'drone_id': mission.drone_id,
            'cost': mission.cost,
            'payment_status': mission.payment_status
        })
    
    return jsonify({'missions': mission_list})

@app.route('/api/missions/stats')
@login_required
def get_mission_stats():
    """Get mission statistics"""
    if current_user.role == 'patient':
        # Patient stats
        missions = Mission.query.filter_by(patient_id=current_user.id).all()
    elif current_user.role == 'clinic':
        # Clinic stats
        missions = Mission.query.filter_by(assigned_clinic_id=current_user.id).all()
    else:
        # Admin stats
        missions = Mission.query.all()
    
    total = len(missions)
    completed = len([m for m in missions if m.status == 'completed'])
    active = len([m for m in missions if m.status in ['accepted', 'assigned', 'in_progress']])
    cancelled = len([m for m in missions if m.status == 'cancelled'])
    
    return jsonify({
        'total': total,
        'completed': completed,
        'active': active,
        'cancelled': cancelled
    })

@app.route('/api/telemetry/simulate/<int:mission_id>', methods=['POST'])
@login_required
def simulate_telemetry(mission_id):
    """Simulate telemetry data for testing"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    mission = Mission.query.get_or_404(mission_id)
    
    if not mission.drone_id:
        return jsonify({'error': 'No drone assigned to mission'}), 400
    
    # Generate simulated telemetry data
    import random
    
    telemetry = TelemetryLog(
        drone_id=mission.drone_id,
        mission_id=mission_id,
        latitude=8.4606 + random.uniform(-0.01, 0.01),
        longitude=-13.2317 + random.uniform(-0.01, 0.01),
        altitude=random.uniform(50, 150),
        heading=random.uniform(0, 360),
        speed=random.uniform(10, 25),
        battery_level=random.randint(20, 100),
        signal_strength=random.randint(60, 100),
        flight_mode='AUTO',
        armed=True,
        temperature=random.uniform(20, 35),
        wind_speed=random.uniform(0, 10),
        wind_direction=random.uniform(0, 360)
    )
    
    db.session.add(telemetry)
    db.session.commit()
    
    return jsonify({'message': 'Telemetry data simulated successfully'})

@app.route('/api/session/check')
@login_required
def check_session():
    """Check if user session is still valid"""
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'role': current_user.role if current_user.is_authenticated else None
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.route('/admin/drones')
@login_required
def admin_drone_management():
    """Admin drone management page"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all drones
    drones = Drone.query.all()
    
    return render_template('admin_drone_management.html', drones=drones)

@app.route('/api/admin/drones/status')
@login_required
def get_admin_drone_status():
    """Get drone status for admin management"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    drones = Drone.query.all()
    drone_data = []
    
    for drone in drones:
        drone_data.append({
            'id': drone.id,
            'name': drone.name,
            'model': drone.model,
            'status': drone.status,
            'battery_level': drone.battery_level,
            'wireless_status': drone.wireless_status,
            'connection_strength': drone.connection_strength,
            'current_latitude': drone.current_latitude,
            'current_longitude': drone.current_longitude,
            'last_seen': drone.last_seen.isoformat() if drone.last_seen else None
        })
    
    # Summary statistics
    summary = {
        'total': len(drones),
        'available': len([d for d in drones if d.status == 'available']),
        'in_flight': len([d for d in drones if d.status == 'in_flight']),
        'maintenance': len([d for d in drones if d.status == 'maintenance']),
        'connected': len([d for d in drones if d.wireless_status in ['connected_wifi', 'connected_cellular']])
    }
    
    return jsonify({
        'drones': drone_data,
        'summary': summary
    })

@app.route('/api/feedback/submit', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback and route to official email"""
    try:
        data = request.get_json()
        
        # Create feedback record
        feedback = Feedback(
            user_id=current_user.id,
            feedback_type=data.get('type', 'general'),
            message=data.get('comments', '') or data.get('message', ''),
            rating=data.get('rating', 5),
            status='submitted'
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        # Send email to official address
        try:
            # Handle emoji feedback
            rating_text = str(data.get('rating', '5'))
            emoji = data.get('emoji', '😊')
            label = data.get('label', 'Good')
            comments = data.get('comments', '') or data.get('message', '')
            
            send_email(
                'sierrawingsofficial@gmail.com',
                f'SierraWings Feedback from {current_user.username}',
                f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #1A252F; color: white; padding: 20px; text-align: center;">
                        <h2>SierraWings Feedback</h2>
                    </div>
                    <div style="padding: 20px; background: #f8f9fa;">
                        <h3>Feedback Details</h3>
                        <p><strong>From:</strong> {current_user.username} ({current_user.email})</p>
                        <p><strong>Role:</strong> {current_user.role}</p>
                        <p><strong>Rating:</strong> {emoji} {label} ({rating_text}/5)</p>
                        <p><strong>Type:</strong> {data.get('type', 'general')}</p>
                        <p><strong>Message:</strong></p>
                        <p style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                            {comments or 'No message provided'}
                        </p>
                        <p><strong>Submitted:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    </div>
                </div>
                """,
                f"SierraWings Feedback\n\nFrom: {current_user.username} ({current_user.email})\nRole: {current_user.role}\n\nRating: {emoji} {label} ({rating_text}/5)\nType: {data.get('type', 'general')}\n\nMessage:\n{comments or 'No message provided'}\n\nSubmitted: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            })
            
        except Exception as e:
            logging.error(f"Error sending feedback email: {str(e)}")
            return jsonify({
                'success': True,
                'message': 'Feedback recorded but email delivery failed'
            })
        
    except Exception as e:
        logging.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': 'Failed to submit feedback'}), 500

@app.route('/api/admin/user-count')
@login_required
def get_user_count():
    """Get total user count for admin dashboard"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        from models import User
        user_count = User.query.count()
        return jsonify({'count': user_count})
    except Exception as e:
        logging.error(f"Error getting user count: {str(e)}")
        return jsonify({'count': 0})





@app.route('/api/system/status')
@login_required
def api_system_status():
    """Get system status for admin dashboard"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get system statistics
        from models import User, Mission, Drone
        
        total_users = User.query.count()
        total_missions = Mission.query.count()
        active_drones = Drone.query.filter_by(status='available').count()
        pending_missions = Mission.query.filter_by(status='pending').count()
        
        return jsonify({
            'total_users': total_users,
            'total_missions': total_missions,
            'active_drones': active_drones,
            'pending_missions': pending_missions,
            'system_health': 'operational'
        })
    except Exception as e:
        logging.error(f"System status error: {str(e)}")
        return jsonify({
            'total_users': 0,
            'total_missions': 0,
            'active_drones': 0,
            'pending_missions': 0,
            'system_health': 'error'
        })

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)

@app.route("/api/maintenance/check")
def check_maintenance_status():
    """Check if system is in maintenance mode"""
    try:
        return jsonify({
            "success": True,
            "maintenance_mode": False,
            "message": "System is operational"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "maintenance_mode": False,
            "message": f"Error checking maintenance status: {str(e)}"
        }), 500

@app.route("/api/system/status")
def get_system_status():
    """Get system status for admin dashboard"""
    try:
        total_users = User.query.count()
        total_missions = Mission.query.count()
        active_missions = Mission.query.filter_by(status="in_progress").count()
        total_drones = Drone.query.count()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_missions": total_missions,
                "active_missions": active_missions,
                "total_drones": total_drones,
                "system_health": "healthy"
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error fetching system status: {str(e)}"
        }), 500

@app.route("/api/broadcast/history")
def get_broadcast_history():
    """Get broadcast history for updates panel"""
    try:
        # Return empty history for now
        return jsonify({
            "success": True,
            "broadcasts": []
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error fetching broadcast history: {str(e)}"
        }), 500

@app.route('/cancel-account-deletion', methods=['POST'])
@login_required
def cancel_account_deletion():
    """Cancel pending account deletion request"""
    try:
        deletion_request = AccountDeletionRequest.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if not deletion_request:
            return jsonify({
                'success': False,
                'message': 'No pending deletion request found'
            })
        
        deletion_request.status = 'cancelled'
        deletion_request.processed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deletion request cancelled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cancelling request: {str(e)}'
        }), 500

