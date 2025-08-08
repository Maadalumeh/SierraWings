"""
Voice-Guided Mission Preparation Checklist Routes
Handles voice checklist API endpoints and integrations
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Mission, Drone, VoiceChecklistLog
from datetime import datetime
import json

voice_checklist = Blueprint('voice_checklist', __name__)

@voice_checklist.route('/api/voice-checklist/start', methods=['POST'])
@login_required
def start_voice_checklist():
    """Start a new voice checklist session"""
    try:
        # Create new checklist log
        checklist_log = VoiceChecklistLog(
            user_id=current_user.id,
            started_at=datetime.utcnow(),
            status='started'
        )
        db.session.add(checklist_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': checklist_log.id,
            'message': 'Voice checklist session started'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/complete', methods=['POST'])
@login_required
def complete_voice_checklist():
    """Complete voice checklist session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        completed_steps = data.get('completed_steps', [])
        
        # Update checklist log
        checklist_log = VoiceChecklistLog.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if checklist_log:
            checklist_log.completed_at = datetime.utcnow()
            checklist_log.status = 'completed'
            checklist_log.completed_steps = json.dumps(completed_steps)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Voice checklist completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Checklist session not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/weather', methods=['GET'])
@login_required
def get_weather_conditions():
    """Get current weather conditions for checklist"""
    try:
        # Mock weather data - in production, integrate with weather API
        weather_data = {
            'temperature': 26,
            'humidity': 65,
            'wind_speed': 12,
            'visibility': 10,
            'conditions': 'Clear',
            'flight_safe': True,
            'warnings': []
        }
        
        # Add warnings based on conditions
        if weather_data['wind_speed'] > 25:
            weather_data['flight_safe'] = False
            weather_data['warnings'].append('High wind speed detected')
            
        if weather_data['visibility'] < 5:
            weather_data['flight_safe'] = False
            weather_data['warnings'].append('Low visibility conditions')
            
        return jsonify({
            'success': True,
            'weather': weather_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/drone-status', methods=['GET'])
@login_required
def get_drone_status():
    """Get drone status for checklist"""
    try:
        # Get available drones
        drones = Drone.query.filter_by(status='available').all()
        
        drone_data = []
        for drone in drones:
            drone_data.append({
                'id': drone.id,
                'name': drone.name,
                'battery_level': drone.battery_level,
                'last_maintenance': drone.last_maintenance.isoformat() if drone.last_maintenance else None,
                'status': drone.status,
                'location': {
                    'latitude': drone.latitude,
                    'longitude': drone.longitude
                }
            })
        
        return jsonify({
            'success': True,
            'drones': drone_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/communication-test', methods=['POST'])
@login_required
def test_communication():
    """Test communication systems"""
    try:
        # Mock communication test
        test_results = {
            'gps_signal': 'strong',
            'telemetry_link': 'active',
            'radio_connection': 'stable',
            'network_latency': 45,
            'all_systems_ok': True
        }
        
        return jsonify({
            'success': True,
            'communication': test_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/flight-path', methods=['GET'])
@login_required
def get_flight_path_info():
    """Get flight path information"""
    try:
        # Mock flight path data
        flight_path = {
            'no_fly_zones': [],
            'obstacles': [],
            'weather_hazards': [],
            'estimated_flight_time': 15,
            'route_clear': True
        }
        
        return jsonify({
            'success': True,
            'flight_path': flight_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/emergency-procedures', methods=['GET'])
@login_required
def get_emergency_procedures():
    """Get emergency procedures information"""
    try:
        emergency_info = {
            'emergency_landing_sites': [
                {'name': 'Freetown Hospital', 'coordinates': [8.4657, -13.2317]},
                {'name': 'Connaught Hospital', 'coordinates': [8.4840, -13.2299]}
            ],
            'backup_communication': 'active',
            'emergency_contacts': [
                {'name': 'Emergency Control', 'number': '+232-xxx-xxxx'},
                {'name': 'Medical Emergency', 'number': '+232-xxx-xxxx'}
            ]
        }
        
        return jsonify({
            'success': True,
            'emergency_info': emergency_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_checklist.route('/api/voice-checklist/history', methods=['GET'])
@login_required
def get_checklist_history():
    """Get user's checklist history"""
    try:
        history = VoiceChecklistLog.query.filter_by(
            user_id=current_user.id
        ).order_by(VoiceChecklistLog.started_at.desc()).limit(10).all()
        
        history_data = []
        for log in history:
            history_data.append({
                'id': log.id,
                'started_at': log.started_at.isoformat(),
                'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                'status': log.status,
                'completed_steps': json.loads(log.completed_steps) if log.completed_steps else []
            })
        
        return jsonify({
            'success': True,
            'history': history_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500