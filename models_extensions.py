from app import db
from datetime import datetime

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    category = db.Column(db.String(50), nullable=False)  # bug_report, feature_request, general
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='feedbacks')
    
    def __repr__(self):
        return f'<Feedback {self.id}: {self.subject}>'



class SystemAlert(db.Model):
    __tablename__ = 'system_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # emergency, maintenance, system, weather
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Targeting
    target_roles = db.Column(db.String(100))  # comma-separated roles
    target_regions = db.Column(db.String(100))  # comma-separated regions
    
    # Status
    active = db.Column(db.Boolean, default=True)
    acknowledged = db.Column(db.Boolean, default=False)
    resolved = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemAlert {self.id}: {self.title}>'

class MaintenanceRecord(db.Model):
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    drone_id = db.Column(db.Integer, db.ForeignKey('drones.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Maintenance details
    maintenance_type = db.Column(db.String(50), nullable=False)  # routine, repair, upgrade
    description = db.Column(db.Text, nullable=False)
    parts_replaced = db.Column(db.Text)  # JSON string
    cost = db.Column(db.Float)
    
    # Scheduling
    scheduled_date = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='normal')
    
    # Results
    notes = db.Column(db.Text)
    next_maintenance_due = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    drone = db.relationship('Drone', backref='maintenance_records')


class MaintenanceAlert(db.Model):
    """System maintenance alerts sent to users"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'scheduled', 'emergency', 'completed'
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_by = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<MaintenanceAlert {self.title}>'

class UpdateMessage(db.Model):
    __tablename__ = 'update_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='info')  # info, warning, success, danger
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DismissedMessage(db.Model):
    __tablename__ = 'dismissed_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('update_messages.id'), nullable=False)
    dismissed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate dismissals
    __table_args__ = (db.UniqueConstraint('user_id', 'message_id', name='unique_user_message_dismissal'),)
