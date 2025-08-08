#!/usr/bin/env python3
"""
Test script for maintenance alert system
"""

from datetime import datetime, timedelta
from maintenance_service import send_maintenance_alert, send_emergency_maintenance_alert

def test_maintenance_alert():
    """Test the maintenance alert system"""
    
    # Test 1: Emergency maintenance alert
    print("Testing emergency maintenance alert...")
    result = send_emergency_maintenance_alert(
        title="Emergency System Maintenance",
        message="We are performing emergency maintenance to fix a critical issue. The system will be unavailable for approximately 2 hours. We apologize for any inconvenience."
    )
    print(f"Emergency alert result: {result}")
    
    # Test 2: Scheduled maintenance alert
    print("\nTesting scheduled maintenance alert...")
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=3)
    
    result = send_maintenance_alert(
        title="Scheduled System Update",
        message="We will be performing scheduled maintenance to improve system performance and add new features. During this time, the platform will be temporarily unavailable.",
        start_time=start_time,
        end_time=end_time,
        alert_type="scheduled"
    )
    print(f"Scheduled alert result: {result}")

if __name__ == "__main__":
    test_maintenance_alert()