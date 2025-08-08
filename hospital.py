from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import (User, HospitalPatient, MedicalRecord, HospitalService, 
                   DataProcessingLog, PatientDataRequest, ClinicProfile)
from app import db
import json
import secrets
import logging

bp = Blueprint('hospital', __name__)

def log_data_access(patient_id, action_type, description, fields_accessed=None):
    """Log data access for privacy compliance"""
    log = DataProcessingLog(
        patient_id=patient_id,
        clinic_id=current_user.id,
        action_type=action_type,
        action_description=description,
        user_performed=current_user.full_name,
        data_fields=json.dumps(fields_accessed) if fields_accessed else None,
        purpose="Medical care and hospital operations"
    )
    db.session.add(log)
    db.session.commit()

@bp.route('/dashboard')
@login_required
def dashboard():
    """Hospital dashboard with patient management"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    # Get hospital statistics
    total_patients = HospitalPatient.query.filter_by(clinic_id=current_user.id, is_active=True).count()
    recent_patients = HospitalPatient.query.filter_by(clinic_id=current_user.id, is_active=True).order_by(HospitalPatient.created_at.desc()).limit(5).all()
    
    # Recent medical records
    recent_records = MedicalRecord.query.filter_by(clinic_id=current_user.id).order_by(MedicalRecord.visit_date.desc()).limit(10).all()
    
    # Data requests pending
    pending_requests = PatientDataRequest.query.filter_by(clinic_id=current_user.id, status='pending').count()
    
    # Hospital services
    services = HospitalService.query.filter_by(clinic_id=current_user.id).all()
    
    return render_template('hospital/dashboard.html', 
                         total_patients=total_patients,
                         recent_patients=recent_patients,
                         recent_records=recent_records,
                         pending_requests=pending_requests,
                         services=services)

@bp.route('/patients')
@login_required
def patients():
    """Patient management page"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = HospitalPatient.query.filter_by(clinic_id=current_user.id, is_active=True)
    
    if search:
        query = query.filter(
            (HospitalPatient.first_name.contains(search)) |
            (HospitalPatient.last_name.contains(search)) |
            (HospitalPatient.patient_id.contains(search))
        )
    
    patients = query.order_by(HospitalPatient.last_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('hospital/patients.html', patients=patients, search=search)

@bp.route('/patients/register', methods=['GET', 'POST'])
@login_required
def register_patient():
    """Register new patient"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Generate medical record number
            record_number = f"{current_user.id:03d}-{secrets.token_hex(4).upper()}"
            
            # Create patient
            patient = HospitalPatient(
                clinic_id=current_user.id,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=request.form.get('gender'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                address=request.form.get('address'),
                city=request.form.get('city'),
                region=request.form.get('region'),
                medical_record_number=record_number,
                blood_type=request.form.get('blood_type'),
                allergies=request.form.get('allergies'),
                chronic_conditions=request.form.get('chronic_conditions'),
                emergency_contact_name=request.form.get('emergency_contact_name'),
                emergency_contact_phone=request.form.get('emergency_contact_phone'),
                insurance_provider=request.form.get('insurance_provider'),
                insurance_number=request.form.get('insurance_number'),
                privacy_level=request.form.get('privacy_level', 'standard')
            )
            
            # Link to app user if email matches
            if patient.email:
                app_user = User.query.filter_by(email=patient.email.lower()).first()
                if app_user:
                    patient.patient_id = app_user.id
            
            db.session.add(patient)
            db.session.commit()
            
            # Log registration
            log_data_access(patient.id, 'create', f'Patient registered: {patient.full_name}')
            
            flash(f'Patient {patient.full_name} registered successfully. Record number: {record_number}', 'success')
            return redirect(url_for('hospital.patient_details', patient_id=patient.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error registering patient. Please try again.', 'error')
            logging.error(f"Patient registration error: {e}")
    
    return render_template('hospital/register_patient.html')

@bp.route('/patients/<int:patient_id>')
@login_required
def patient_details(patient_id):
    """Patient details and medical records"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    patient = HospitalPatient.query.filter_by(id=patient_id, clinic_id=current_user.id).first()
    if not patient:
        flash('Patient not found.', 'error')
        return redirect(url_for('hospital.patients'))
    
    # Get medical records
    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.visit_date.desc()).all()
    
    # Log data access
    log_data_access(patient_id, 'view', f'Viewed patient details: {patient.full_name}')
    
    return render_template('hospital/patient_details.html', patient=patient, records=records)

@bp.route('/patients/<int:patient_id>/add_record', methods=['GET', 'POST'])
@login_required
def add_medical_record(patient_id):
    """Add medical record for patient"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    patient = HospitalPatient.query.filter_by(id=patient_id, clinic_id=current_user.id).first()
    if not patient:
        flash('Patient not found.', 'error')
        return redirect(url_for('hospital.patients'))
    
    if request.method == 'POST':
        try:
            record = MedicalRecord(
                patient_id=patient_id,
                clinic_id=current_user.id,
                doctor_name=request.form.get('doctor_name'),
                visit_date=datetime.strptime(request.form.get('visit_date'), '%Y-%m-%dT%H:%M'),
                visit_type=request.form.get('visit_type'),
                chief_complaint=request.form.get('chief_complaint'),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                medications=request.form.get('medications'),
                blood_pressure=request.form.get('blood_pressure'),
                heart_rate=int(request.form.get('heart_rate')) if request.form.get('heart_rate') else None,
                temperature=float(request.form.get('temperature')) if request.form.get('temperature') else None,
                weight=float(request.form.get('weight')) if request.form.get('weight') else None,
                height=float(request.form.get('height')) if request.form.get('height') else None,
                notes=request.form.get('notes'),
                confidential=bool(request.form.get('confidential')),
                access_level=request.form.get('access_level', 'standard')
            )
            
            if request.form.get('follow_up_required'):
                record.follow_up_required = True
                if request.form.get('follow_up_date'):
                    record.follow_up_date = datetime.strptime(request.form.get('follow_up_date'), '%Y-%m-%dT%H:%M')
            
            db.session.add(record)
            
            # Update patient last visit
            patient.last_visit = record.visit_date
            db.session.commit()
            
            # Log record creation
            log_data_access(patient_id, 'create', f'Medical record created for {patient.full_name}')
            
            flash('Medical record added successfully.', 'success')
            return redirect(url_for('hospital.patient_details', patient_id=patient_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding medical record. Please try again.', 'error')
            logging.error(f"Medical record error: {e}")
    
    return render_template('hospital/add_medical_record.html', patient=patient)

@bp.route('/search_hospitals')
def search_hospitals():
    """API endpoint for patients to search hospitals"""
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    service = request.args.get('service', '')
    
    # Base query for hospitals
    query = User.query.filter_by(role='clinic', is_active=True, email_verified=True)
    
    if search:
        query = query.filter(
            (User.first_name.contains(search)) |
            (User.last_name.contains(search)) |
            (User.clinic_name.contains(search))
        )
    
    hospitals = query.limit(50).all()
    
    # Get hospital profiles and services
    hospital_data = []
    for hospital in hospitals:
        profile = ClinicProfile.query.filter_by(user_id=hospital.id).first()
        services = HospitalService.query.filter_by(clinic_id=hospital.id, available=True).all()
        
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
            'services': [{'name': s.service_name, 'category': s.service_category} for s in services],
            'operating_hours': json.loads(profile.operating_hours) if profile and profile.operating_hours else None,
            'verified': profile.verified if profile else False
        }
        hospital_data.append(hospital_info)
    
    return jsonify(hospital_data)

@bp.route('/services')
@login_required
def services():
    """Hospital services management"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    services = HospitalService.query.filter_by(clinic_id=current_user.id).all()
    return render_template('hospital/services.html', services=services)

@bp.route('/services/add', methods=['GET', 'POST'])
@login_required
def add_service():
    """Add hospital service"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            service = HospitalService(
                clinic_id=current_user.id,
                service_name=request.form.get('service_name'),
                service_category=request.form.get('service_category'),
                description=request.form.get('description'),
                base_price=float(request.form.get('base_price')) if request.form.get('base_price') else None,
                operating_hours=json.dumps(request.form.get('operating_hours')) if request.form.get('operating_hours') else None
            )
            
            db.session.add(service)
            db.session.commit()
            
            flash('Service added successfully.', 'success')
            return redirect(url_for('hospital.services'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding service. Please try again.', 'error')
            logging.error(f"Service creation error: {e}")
    
    return render_template('hospital/add_service.html')

@bp.route('/data_requests')
@login_required
def data_requests():
    """Handle patient data requests"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    requests = PatientDataRequest.query.filter_by(clinic_id=current_user.id).order_by(PatientDataRequest.requested_at.desc()).all()
    return render_template('hospital/data_requests.html', requests=requests)

@bp.route('/data_requests/<int:request_id>/process', methods=['POST'])
@login_required
def process_data_request(request_id):
    """Process patient data request"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    data_request = PatientDataRequest.query.filter_by(id=request_id, clinic_id=current_user.id).first()
    if not data_request:
        flash('Request not found.', 'error')
        return redirect(url_for('hospital.data_requests'))
    
    action = request.form.get('action')
    response_message = request.form.get('response_message')
    
    if action in ['approved', 'rejected']:
        data_request.status = action
        data_request.response_message = response_message
        data_request.processed_at = datetime.utcnow()
        
        if action == 'approved':
            # Log approval
            log_data_access(data_request.patient_id, 'approve_request', 
                          f'Data request approved: {data_request.request_type}')
        
        db.session.commit()
        flash(f'Request {action} successfully.', 'success')
    
    return redirect(url_for('hospital.data_requests'))

@bp.route('/privacy_logs')
@login_required
def privacy_logs():
    """View data access logs for privacy compliance"""
    if current_user.role != 'clinic':
        flash('Access denied. Hospital access required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    logs = DataProcessingLog.query.filter_by(clinic_id=current_user.id).order_by(DataProcessingLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('hospital/privacy_logs.html', logs=logs)