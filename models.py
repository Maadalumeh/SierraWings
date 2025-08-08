from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # patient, clinic, admin
    is_active = db.Column(db.Boolean, default=True)
    
    # Age and compliance
    date_of_birth = db.Column(db.Date)
    age_verified = db.Column(db.Boolean, default=False)
    
    # Data privacy preferences
    data_processing_consent = db.Column(db.Boolean, default=True)
    marketing_consent = db.Column(db.Boolean, default=False)
    data_retention_consent = db.Column(db.Boolean, default=True)
    
    # Account security tracking
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    account_locked_until = db.Column(db.DateTime)
    
    # Admin tracking for violations
    violation_count = db.Column(db.Integer, default=0)
    last_violation_date = db.Column(db.DateTime)
    violation_notes = db.Column(db.Text)
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Medical information (for patients)
    medical_id = db.Column(db.String(50))
    emergency_contact = db.Column(db.String(100))
    allergies = db.Column(db.Text)
    
    # Clinic information
    clinic_name = db.Column(db.String(100))
    clinic_license = db.Column(db.String(50))
    specialization = db.Column(db.String(100))
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(6))  # 6-digit OTP code
    email_verification_expires = db.Column(db.DateTime)
    email_verification_sent_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    missions_requested = db.relationship('Mission', foreign_keys='Mission.patient_id', backref='patient', lazy='dynamic')
    missions_handled = db.relationship('Mission', foreign_keys='Mission.assigned_clinic_id', backref='assigned_clinic', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Drone(db.Model):
    __tablename__ = 'drones'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='available')  # available, in_flight, maintenance, offline
    
    # Current location
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    altitude = db.Column(db.Float, default=0)
    
    # Drone specifications
    max_payload = db.Column(db.Float)  # kg
    flight_time = db.Column(db.Integer)  # minutes
    battery_level = db.Column(db.Integer, default=100)
    
    # Connection information
    connection_string = db.Column(db.String(200))
    pixhawk_status = db.Column(db.String(20), default='disconnected')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Operational data
    total_flights = db.Column(db.Integer, default=0)
    total_flight_time = db.Column(db.Integer, default=0)  # minutes
    maintenance_due = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    missions = db.relationship('Mission', foreign_keys='Mission.drone_id', backref='drone', lazy='dynamic')
    telemetry_logs = db.relationship('TelemetryLog', backref='drone', lazy='dynamic')
    
    def __repr__(self):
        return f'<Drone {self.name}>'

class Mission(db.Model):
    __tablename__ = 'missions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_clinic_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    drone_id = db.Column(db.Integer, db.ForeignKey('drones.id'))
    
    # Mission details
    mission_type = db.Column(db.String(50), nullable=False)  # delivery, pickup, emergency
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, emergency
    status = db.Column(db.String(20), default='requested')  # requested, accepted, assigned, in_progress, completed, cancelled
    
    # Medical information
    medical_items = db.Column(db.Text)  # JSON string of items
    prescription_number = db.Column(db.String(50))
    special_instructions = db.Column(db.Text)
    
    # Location information
    pickup_address = db.Column(db.Text, nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lon = db.Column(db.Float)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_lat = db.Column(db.Float)
    delivery_lon = db.Column(db.Float)
    
    # Timing
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    scheduled_at = db.Column(db.DateTime)
    
    # Additional fields for compatibility
    contact_phone = db.Column(db.String(20))
    
    # Payment
    cost = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    
    # Delivery confirmation
    delivery_notes = db.Column(db.Text)
    signature_data = db.Column(db.Text)
    photo_proof = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    telemetry_logs = db.relationship('TelemetryLog', backref='mission', lazy='dynamic')
    
    def __repr__(self):
        return f'<Mission {self.id} - {self.mission_type}>'

class TelemetryLog(db.Model):
    __tablename__ = 'telemetry_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    drone_id = db.Column(db.Integer, db.ForeignKey('drones.id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('missions.id'))
    
    # GPS data
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    altitude = db.Column(db.Float)
    heading = db.Column(db.Float)
    speed = db.Column(db.Float)
    
    # System status
    battery_level = db.Column(db.Integer)
    battery_voltage = db.Column(db.Float)
    signal_strength = db.Column(db.Integer)
    flight_mode = db.Column(db.String(20))
    armed = db.Column(db.Boolean, default=False)
    
    # Environmental data
    temperature = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TelemetryLog {self.drone_id} - {self.timestamp}>'

class ClinicProfile(db.Model):
    __tablename__ = 'clinic_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Clinic information
    clinic_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    registration_date = db.Column(db.Date)
    
    # Contact information
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    
    # Address
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    region = db.Column(db.String(50))
    postal_code = db.Column(db.String(10))
    
    # Operational details
    operating_hours = db.Column(db.Text)  # JSON string
    services_offered = db.Column(db.Text)  # JSON string
    emergency_contact = db.Column(db.String(100))
    
    # Verification status
    verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='clinic_profile')
    
    def __repr__(self):
        return f'<ClinicProfile {self.clinic_name}>'

class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(db.Integer, db.ForeignKey('missions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Payment details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='SLE')  # Sierra Leone Leone
    payment_method = db.Column(db.String(50))  # mobile_money, cash, card
    
    # Transaction status
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100))
    reference_number = db.Column(db.String(100))
    
    # Provider information (for mobile money)
    provider = db.Column(db.String(50))  # orange_money, africell_money, qmoney
    phone_number = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mission = db.relationship('Mission', backref='payment_transaction')
    user = db.relationship('User', backref='payment_transactions')
    
    def __repr__(self):
        return f'<PaymentTransaction {self.id} - {self.amount}>'

class HospitalPatient(db.Model):
    __tablename__ = 'hospital_patients'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Clinic that registered this patient
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # If patient has app account
    
    # Patient personal information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Address information
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    region = db.Column(db.String(50))
    
    # Medical information
    medical_record_number = db.Column(db.String(50), nullable=False)
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    
    # Insurance information
    insurance_provider = db.Column(db.String(100))
    insurance_number = db.Column(db.String(50))
    
    # Privacy and consent
    data_consent_given = db.Column(db.Boolean, default=True)
    data_consent_date = db.Column(db.DateTime, default=datetime.utcnow)
    privacy_level = db.Column(db.String(20), default='standard')  # standard, restricted, minimal
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_visit = db.Column(db.DateTime)
    
    # Relationships
    clinic = db.relationship('User', foreign_keys='HospitalPatient.clinic_id', backref='clinic_patients')
    app_user = db.relationship('User', foreign_keys='HospitalPatient.patient_id', backref='hospital_records')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.utcnow().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def __repr__(self):
        return f'<HospitalPatient {self.full_name} - {self.medical_record_number}>'

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('hospital_patients.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    
    # Visit information
    visit_date = db.Column(db.DateTime, nullable=False)
    visit_type = db.Column(db.String(50), nullable=False)  # consultation, emergency, checkup, surgery
    chief_complaint = db.Column(db.Text)
    
    # Medical details
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    medications = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    
    # Vital signs
    blood_pressure = db.Column(db.String(10))
    heart_rate = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    
    # Additional notes
    notes = db.Column(db.Text)
    attachments = db.Column(db.Text)  # JSON string of file paths
    
    # Privacy and access
    confidential = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='standard')  # standard, restricted, emergency_only
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = db.relationship('User', backref='medical_records')
    
    def __repr__(self):
        return f'<MedicalRecord {self.id} - {self.visit_date}>'

class HospitalService(db.Model):
    __tablename__ = 'hospital_services'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Service information
    service_name = db.Column(db.String(100), nullable=False)
    service_category = db.Column(db.String(50), nullable=False)  # emergency, consultation, surgery, diagnostic
    description = db.Column(db.Text)
    
    # Availability
    available = db.Column(db.Boolean, default=True)
    operating_hours = db.Column(db.Text)  # JSON string
    
    # Pricing
    base_price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='SLE')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = db.relationship('User', backref='clinic_services')
    
    def __repr__(self):
        return f'<HospitalService {self.service_name}>'

class DataProcessingLog(db.Model):
    __tablename__ = 'data_processing_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('hospital_patients.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Action details
    action_type = db.Column(db.String(50), nullable=False)  # view, edit, delete, export, share
    action_description = db.Column(db.Text)
    user_performed = db.Column(db.String(100), nullable=False)
    
    # Data accessed
    data_fields = db.Column(db.Text)  # JSON string of fields accessed
    purpose = db.Column(db.Text)  # Purpose of data access
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('HospitalPatient', backref='data_access_logs')
    clinic = db.relationship('User', backref='data_processing_logs')
    
    def __repr__(self):
        return f'<DataProcessingLog {self.action_type} - {self.timestamp}>'

class PatientDataRequest(db.Model):
    __tablename__ = 'patient_data_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('hospital_patients.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Request details
    request_type = db.Column(db.String(50), nullable=False)  # access, correction, deletion, portability
    request_description = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    response_message = db.Column(db.Text)
    
    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    patient = db.relationship('HospitalPatient', backref='data_requests')
    clinic = db.relationship('User', backref='patient_data_requests')
    
    def __repr__(self):
        return f'<PatientDataRequest {self.request_type} - {self.status}>'

class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Login details
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    login_method = db.Column(db.String(50), default='email')  # email, 2fa, backup_code
    
    # Success/failure
    success = db.Column(db.Boolean, default=True)
    failure_reason = db.Column(db.String(200))
    
    # Location (if available)
    location = db.Column(db.String(200))
    
    # Relationships
    user = db.relationship('User', backref='login_logs')
    
    def __repr__(self):
        return f'<LoginLog {self.user_id} - {self.login_time}>'

class AccountDeletionRequest(db.Model):
    __tablename__ = 'account_deletion_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='deletion_request')
    processed_by_admin = db.relationship('User', foreign_keys=[processed_by])

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(50), nullable=False)  # 'update', 'maintenance', 'announcement', 'alert'
    target_role = db.Column(db.String(20), nullable=False)  # 'patient', 'clinic', 'admin', 'all'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    admin = db.relationship('User', backref='announcements')

class VoiceChecklistLog(db.Model):
    __tablename__ = 'voice_checklist_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Session details
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='started')  # started, completed, abandoned
    
    # Checklist data
    completed_steps = db.Column(db.Text)  # JSON string of completed steps
    weather_conditions = db.Column(db.Text)  # JSON string of weather data
    drone_status = db.Column(db.Text)  # JSON string of drone status
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='voice_checklist_logs')
    
    def __repr__(self):
        return f'<VoiceChecklistLog {self.user_id} - {self.status}>'

class AnnouncementDismissal(db.Model):
    __tablename__ = 'announcement_dismissals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    dismissed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='dismissed_announcements')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'announcement_id'),)
