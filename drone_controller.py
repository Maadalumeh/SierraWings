"""
SierraWings Drone Controller
Manages communication with Pixhawk flight controllers and live telemetry
"""

import socket
import json
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DroneController:
    """
    Central drone controller for managing fleet operations
    Handles discovery, communication, and telemetry from Pixhawk-equipped drones
    """
    
    def __init__(self, discovery_port=8888):
        self.discovery_port = discovery_port
        self.discovered_drones = {}
        self.server_socket = None
        self.running = False
        self.discovery_thread = None
        self.command_handlers = {}
        
        # Initialize command handlers
        self._setup_command_handlers()
    
    def _setup_command_handlers(self):
        """Setup command handlers for drone operations"""
        self.command_handlers = {
            'arm': self._handle_arm_command,
            'disarm': self._handle_disarm_command,
            'takeoff': self._handle_takeoff_command,
            'land': self._handle_land_command,
            'return_to_launch': self._handle_rtl_command,
            'goto_location': self._handle_goto_command,
            'get_telemetry': self._handle_telemetry_request
        }
    
    def start_server(self):
        """Start the drone discovery and command server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.discovery_port))
            
            self.running = True
            
            # Start discovery listener thread
            self.discovery_thread = threading.Thread(target=self._discovery_listener)
            self.discovery_thread.daemon = True
            self.discovery_thread.start()
            
            logger.info(f"Drone controller started on port {self.discovery_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start drone controller: {e}")
            return False
    
    def stop_server(self):
        """Stop the drone controller server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Drone controller stopped")
    
    def _discovery_listener(self):
        """Listen for drone announcements and commands"""
        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message.get('type') == 'drone_announce':
                    self._handle_drone_announcement(message, addr)
                elif message.get('type') == 'command':
                    self._handle_drone_command(message, addr)
                    
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Discovery listener error: {e}")
                time.sleep(1)
    
    def _handle_drone_announcement(self, message, addr):
        """Handle drone announcement messages"""
        drone_id = message.get('drone_id')
        if drone_id:
            self.discovered_drones[drone_id] = {
                'id': drone_id,
                'name': message.get('name', drone_id),
                'address': addr[0],
                'port': message.get('port', 14550),
                'status': message.get('pixhawk_status', 'unknown'),
                'battery_voltage': message.get('battery_voltage', 0),
                'gps_fix': message.get('gps_fix', False),
                'flight_mode': message.get('flight_mode', 'unknown'),
                'armed': message.get('armed', False),
                'signal_strength': message.get('signal_strength', 0),
                'last_seen': datetime.utcnow(),
                'firmware_version': message.get('firmware_version', 'unknown')
            }
            
            logger.debug(f"Updated drone {drone_id} status: {message.get('pixhawk_status')}")
    
    def _handle_drone_command(self, message, addr):
        """Handle command messages from the web interface"""
        command = message.get('command')
        drone_id = message.get('target_drone')
        
        if command in self.command_handlers:
            result = self.command_handlers[command](drone_id, message.get('params', {}))
            
            # Send response back to web interface
            response = {
                'type': 'command_response',
                'drone_id': drone_id,
                'command': command,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            try:
                self.server_socket.sendto(json.dumps(response).encode(), addr)
            except Exception as e:
                logger.error(f"Failed to send command response: {e}")
    
    def send_command_to_drone(self, drone_id: str, command: str, params: Dict = None) -> Dict:
        """Send command to specific drone"""
        if drone_id not in self.discovered_drones:
            return {'success': False, 'error': 'Drone not found'}
        
        drone_info = self.discovered_drones[drone_id]
        
        try:
            # Create command message
            command_msg = {
                'type': 'command',
                'command': command,
                'target_drone': drone_id,
                'params': params or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send command to drone
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            drone_address = (drone_info['address'], drone_info['port'])
            sock.sendto(json.dumps(command_msg).encode(), drone_address)
            
            # Wait for response
            response_data, _ = sock.recvfrom(1024)
            response = json.loads(response_data.decode())
            
            sock.close()
            return response.get('result', {'success': True})
            
        except Exception as e:
            logger.error(f"Failed to send command to drone {drone_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_discovered_drones(self) -> Dict:
        """Get list of discovered drones"""
        # Clean up old entries (older than 30 seconds)
        current_time = datetime.utcnow()
        expired_drones = []
        
        for drone_id, info in self.discovered_drones.items():
            if (current_time - info['last_seen']).total_seconds() > 30:
                expired_drones.append(drone_id)
        
        for drone_id in expired_drones:
            del self.discovered_drones[drone_id]
            logger.info(f"Removed expired drone: {drone_id}")
        
        return self.discovered_drones.copy()
    
    def get_drone_telemetry(self, drone_id: str) -> Optional[Dict]:
        """Get current telemetry from specific drone"""
        return self.send_command_to_drone(drone_id, 'get_telemetry')
    
    def arm_drone(self, drone_id: str) -> Dict:
        """Arm specific drone"""
        return self.send_command_to_drone(drone_id, 'arm')
    
    def disarm_drone(self, drone_id: str) -> Dict:
        """Disarm specific drone"""
        return self.send_command_to_drone(drone_id, 'disarm')
    
    def takeoff_drone(self, drone_id: str, altitude: float = 10.0) -> Dict:
        """Command drone to takeoff"""
        return self.send_command_to_drone(drone_id, 'takeoff', {'altitude': altitude})
    
    def land_drone(self, drone_id: str) -> Dict:
        """Command drone to land"""
        return self.send_command_to_drone(drone_id, 'land')
    
    def return_to_launch(self, drone_id: str) -> Dict:
        """Command drone to return to launch"""
        return self.send_command_to_drone(drone_id, 'return_to_launch')
    
    def goto_location(self, drone_id: str, latitude: float, longitude: float, altitude: float = 50.0) -> Dict:
        """Command drone to go to specific location"""
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude
        }
        return self.send_command_to_drone(drone_id, 'goto_location', params)
    
    # Command handlers
    def _handle_arm_command(self, drone_id: str, params: Dict) -> Dict:
        """Handle arm command"""
        logger.info(f"Arming drone {drone_id}")
        return self.send_command_to_drone(drone_id, 'arm', params)
    
    def _handle_disarm_command(self, drone_id: str, params: Dict) -> Dict:
        """Handle disarm command"""
        logger.info(f"Disarming drone {drone_id}")
        return self.send_command_to_drone(drone_id, 'disarm', params)
    
    def _handle_takeoff_command(self, drone_id: str, params: Dict) -> Dict:
        """Handle takeoff command"""
        altitude = params.get('altitude', 10.0)
        logger.info(f"Taking off drone {drone_id} to {altitude}m")
        return self.send_command_to_drone(drone_id, 'takeoff', params)
    
    def _handle_land_command(self, drone_id: str, params: Dict) -> Dict:
        """Handle land command"""
        logger.info(f"Landing drone {drone_id}")
        return self.send_command_to_drone(drone_id, 'land', params)
    
    def _handle_rtl_command(self, drone_id: str, params: Dict) -> Dict:
        """Handle return to launch command"""
        logger.info(f"RTL for drone {drone_id}")
        return self.send_command_to_drone(drone_id, 'return_to_launch', params)
    
    def _handle_goto_command(self, drone_id: str, params: Dict) -> Dict:
        """Handle goto location command"""
        lat = params.get('latitude')
        lon = params.get('longitude')
        alt = params.get('altitude', 50.0)
        logger.info(f"Sending drone {drone_id} to {lat}, {lon} at {alt}m")
        return self.send_command_to_drone(drone_id, 'goto_location', params)
    
    def _handle_telemetry_request(self, drone_id: str, params: Dict) -> Dict:
        """Handle telemetry request"""
        return self.send_command_to_drone(drone_id, 'get_telemetry', params)
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        active_drones = len(self.discovered_drones)
        connected_drones = len([d for d in self.discovered_drones.values() if d['status'] == 'connected'])
        
        return {
            'server_running': self.running,
            'discovery_port': self.discovery_port,
            'active_drones': active_drones,
            'connected_drones': connected_drones,
            'last_update': datetime.utcnow().isoformat()
        }

# Global drone controller instance
drone_controller = DroneController()
