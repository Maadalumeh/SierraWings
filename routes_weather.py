"""
Weather API Routes
Provides real-time weather data for drone operations
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from app import app
from weather_service import weather_service
import logging

@app.route('/api/weather')
@login_required
def get_weather():
    """Get current weather data"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        weather_data = weather_service.get_weather_data(lat, lon)
        
        return jsonify({
            'success': True,
            'weather': weather_data
        })
        
    except Exception as e:
        logging.error(f"Weather API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to fetch weather data'
        }), 500

@app.route('/api/weather/forecast')
@login_required
def get_weather_forecast():
    """Get weather forecast"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        forecast_data = weather_service.get_forecast(lat, lon)
        
        return jsonify({
            'success': True,
            'forecast': forecast_data
        })
        
    except Exception as e:
        logging.error(f"Weather forecast API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to fetch forecast data'
        }), 500

@app.route('/api/weather/flight-safety')
@login_required
def get_flight_safety():
    """Get flight safety assessment based on weather"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        weather_data = weather_service.get_weather_data(lat, lon)
        
        return jsonify({
            'success': True,
            'flight_safety': weather_data['flight_safety'],
            'weather_summary': {
                'temperature': weather_data['temperature'],
                'wind_speed': weather_data['wind_speed'],
                'visibility': weather_data['visibility'],
                'description': weather_data['description']
            }
        })
        
    except Exception as e:
        logging.error(f"Flight safety API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to assess flight safety'
        }), 500