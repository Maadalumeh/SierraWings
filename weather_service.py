"""
Weather Service for SierraWings
Provides real-time weather data and flight safety assessments
"""

import requests
import json
from datetime import datetime
from app import app

class WeatherService:
    """Weather service for flight safety assessment"""
    
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.api_key = app.config.get('OPENWEATHER_API_KEY', 'demo_key')
        
    def get_weather_data(self, lat=8.4606, lon=-11.7799):
        """Get current weather data for coordinates (default: Freetown, Sierra Leone)"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return fallback data for demo
                return self._get_fallback_weather_data()
                
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_fallback_weather_data()
    
    def _get_fallback_weather_data(self):
        """Fallback weather data for demo purposes"""
        return {
            "main": {
                "temp": 26,
                "humidity": 75,
                "pressure": 1013
            },
            "weather": [
                {
                    "main": "Clear",
                    "description": "clear sky",
                    "icon": "01d"
                }
            ],
            "wind": {
                "speed": 2.5,
                "deg": 180
            },
            "visibility": 10000,
            "clouds": {
                "all": 10
            },
            "name": "Freetown",
            "sys": {
                "country": "SL"
            }
        }
    
    def assess_flight_safety(self, weather_data):
        """Assess flight safety based on weather conditions"""
        try:
            temp = weather_data['main']['temp']
            wind_speed = weather_data['wind']['speed'] * 3.6  # Convert m/s to km/h
            visibility = weather_data.get('visibility', 10000) / 1000  # Convert m to km
            cloud_coverage = weather_data['clouds']['all']
            weather_main = weather_data['weather'][0]['main'].lower()
            
            # Flight safety assessment
            safety_score = 100
            conditions = []
            
            # Temperature checks
            if temp < 0 or temp > 40:
                safety_score -= 30
                conditions.append("Extreme temperature")
            
            # Wind speed checks
            if wind_speed > 25:
                safety_score -= 40
                conditions.append("High winds")
            elif wind_speed > 15:
                safety_score -= 20
                conditions.append("Moderate winds")
            
            # Visibility checks
            if visibility < 5:
                safety_score -= 35
                conditions.append("Low visibility")
            elif visibility < 8:
                safety_score -= 15
                conditions.append("Reduced visibility")
            
            # Weather condition checks
            if weather_main in ['thunderstorm', 'tornado']:
                safety_score -= 50
                conditions.append("Severe weather")
            elif weather_main in ['rain', 'drizzle']:
                safety_score -= 25
                conditions.append("Precipitation")
            elif weather_main == 'snow':
                safety_score -= 40
                conditions.append("Snow conditions")
            
            # Cloud coverage
            if cloud_coverage > 80:
                safety_score -= 15
                conditions.append("Heavy cloud cover")
            
            # Determine safety level
            if safety_score >= 80:
                safety_level = "Safe to Fly"
                safety_color = "#28a745"
                safety_icon = "fas fa-check-circle"
            elif safety_score >= 60:
                safety_level = "Caution"
                safety_color = "#ffc107"
                safety_icon = "fas fa-exclamation-triangle"
            else:
                safety_level = "Unsafe to Fly"
                safety_color = "#dc3545"
                safety_icon = "fas fa-times-circle"
            
            return {
                'safety_level': safety_level,
                'safety_score': safety_score,
                'safety_color': safety_color,
                'safety_icon': safety_icon,
                'conditions': conditions,
                'temperature': f"{temp}°C",
                'wind_speed': f"{wind_speed:.1f} km/h",
                'visibility': f"{visibility:.1f} km",
                'weather_description': weather_data['weather'][0]['description'].title(),
                'location': weather_data.get('name', 'Unknown'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Flight safety assessment error: {e}")
            return {
                'safety_level': 'Assessment Unavailable',
                'safety_score': 0,
                'safety_color': '#6c757d',
                'safety_icon': 'fas fa-question-circle',
                'conditions': ['Weather data unavailable'],
                'temperature': 'N/A',
                'wind_speed': 'N/A',
                'visibility': 'N/A',
                'weather_description': 'Unknown',
                'location': 'Unknown',
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

# Initialize weather service
weather_service = WeatherService()

def get_flight_conditions(lat=8.4606, lon=-11.7799):
    """Get flight conditions for specified coordinates"""
    weather_data = weather_service.get_weather_data(lat, lon)
    return weather_service.assess_flight_safety(weather_data)