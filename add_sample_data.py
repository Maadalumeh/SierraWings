#!/usr/bin/env python3
"""
Add sample data to test the live statistics system
"""

from app import app, db
from models import User, Mission, Drone
from datetime import datetime, timedelta
import random

def add_sample_data():
    """Add sample missions and deliveries to test statistics"""
    
    with app.app_context():
        # Get existing users or create new ones with unique usernames
        patient = User.query.filter_by(role='patient').first()
        if not patient:
            patient = User(
                username='testpatient_' + str(random.randint(1000, 9999)),
                email='patient' + str(random.randint(1000, 9999)) + '@test.com',
                role='patient',
                first_name='Test',
                last_name='Patient'
            )
            patient.set_password('password123')
            db.session.add(patient)
        
        clinic = User.query.filter_by(role='clinic').first()
        if not clinic:
            clinic = User(
                username='testclinic_' + str(random.randint(1000, 9999)),
                email='clinic' + str(random.randint(1000, 9999)) + '@test.com',
                role='clinic',
                first_name='Test',
                last_name='Clinic'
            )
            clinic.set_password('password123')
            db.session.add(clinic)
        
        # Create sample drone if it doesn't exist
        drone = Drone.query.filter_by(serial_number='TEST001').first()
        if not drone:
            drone = Drone(
                name='Test Drone 1',
                model='SierraWings X1',
                serial_number='TEST001',
                status='available',
                max_payload=2.0,
                flight_time=45
            )
            db.session.add(drone)
        
        db.session.commit()
        
        # Add sample completed missions
        for i in range(50):
            # Create mission with random completion time
            created_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            completion_time = created_time + timedelta(minutes=random.randint(8, 25))
            
            mission = Mission(
                patient_id=patient.id,
                assigned_clinic_id=clinic.id,
                drone_id=drone.id,
                mission_type='delivery',
                priority='normal',
                status='completed',
                medical_items='Emergency Medicine',
                pickup_address='Central Medical Supply',
                pickup_lat=8.4657,
                pickup_lon=-11.7794,
                delivery_address='Patient Location',
                delivery_lat=8.4657,
                delivery_lon=-11.7794,
                created_at=created_time,
                updated_at=completion_time,
                completed_at=completion_time
            )
            db.session.add(mission)
        
        # Add some failed missions for realistic success rate
        for i in range(3):
            created_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            failure_time = created_time + timedelta(minutes=random.randint(30, 60))
            
            mission = Mission(
                patient_id=patient.id,
                assigned_clinic_id=clinic.id,
                drone_id=drone.id,
                mission_type='delivery',
                priority='normal',
                status='failed',
                medical_items='Emergency Medicine',
                pickup_address='Central Medical Supply',
                pickup_lat=8.4657,
                pickup_lon=-11.7794,
                delivery_address='Patient Location',
                delivery_lat=8.4657,
                delivery_lon=-11.7794,
                created_at=created_time,
                updated_at=failure_time
            )
            db.session.add(mission)
        
        db.session.commit()
        print("Sample data added successfully!")
        print(f"Total completed missions: {Mission.query.filter_by(status='completed').count()}")
        print(f"Total failed missions: {Mission.query.filter_by(status='failed').count()}")

if __name__ == '__main__':
    add_sample_data()