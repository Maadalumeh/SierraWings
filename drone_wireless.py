"""
Drone Wireless Connection Manager
Handles real time communication with Raspberry Pi onboard drones
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List
import websockets
import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import socket

class DroneWirelessManager:
    """Manages wireless connections to drone Raspberry Pi units"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.socketio = SocketIO(app, cors_allowed_origins="*")
        self.connected_drones = {}  # drone_id -> connection_info
        self.drone_status = {}  # drone_id -> status_info
        self.discovery_port = 8888
        self.api_port = 5001
        self.setup_routes()
        self.setup_websocket_handlers()
        
    def setup_routes(self):
        """Setup REST API routes for drone communication"""
        
        @self.app.route('/api/drone/connect', methods=['POST'])
        def connect_drone():
            """Connect to a specific drone"""
            data = request.get_json()
            drone_id = data.get('drone_id')
            drone_ip = data.get('drone_ip')
            
            if not drone_id or not drone_ip:
                return jsonify({'error': 'drone_id and drone_ip required'}), 400
            
            try:
                # Test connection to drone
                response = requests.get(f'http://{drone_ip}:{self.api_port}/ping', timeout=5)
                if response.status_code == 200:
                    self.connected_drones[drone_id] = {
                        'ip': drone_ip,
                        'connected_at': datetime.now().isoformat(),
                        'status': 'connected',
                        'last_ping': time.time()
                    }
                    self.drone_status[drone_id] = {
                        'status': 'connected',
                        'battery': 100,
                        'gps': {'lat': 0, 'lon': 0, 'alt': 0},
                        'armed': False,
                        'mode': 'STABILIZE'
                    }
                    return jsonify({'status': 'connected', 'drone_id': drone_id})
                else:
                    return jsonify({'error': 'Failed to connect to drone'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/drone/disconnect', methods=['POST'])
        def disconnect_drone():
            """Disconnect from a specific drone"""
            data = request.get_json()
            drone_id = data.get('drone_id')
            
            if drone_id in self.connected_drones:
                del self.connected_drones[drone_id]
                if drone_id in self.drone_status:
                    self.drone_status[drone_id]['status'] = 'disconnected'
                return jsonify({'status': 'disconnected', 'drone_id': drone_id})
            else:
                return jsonify({'error': 'Drone not connected'}), 404
        
        @self.app.route('/api/drone/status/<drone_id>', methods=['GET'])
        def get_drone_status(drone_id):
            """Get current status of a specific drone"""
            if drone_id in self.drone_status:
                return jsonify(self.drone_status[drone_id])
            else:
                return jsonify({'error': 'Drone not found'}), 404
        
        @self.app.route('/api/drone/list', methods=['GET'])
        def list_connected_drones():
            """List all connected drones"""
            return jsonify({
                'connected_drones': list(self.connected_drones.keys()),
                'drone_status': self.drone_status
            })
        
        @self.app.route('/api/drone/ping/<drone_id>', methods=['GET'])
        def ping_drone(drone_id):
            """Ping a specific drone to check connectivity"""
            if drone_id not in self.connected_drones:
                return jsonify({'error': 'Drone not connected'}), 404
            
            drone_info = self.connected_drones[drone_id]
            try:
                response = requests.get(f'http://{drone_info["ip"]}:{self.api_port}/ping', timeout=3)
                if response.status_code == 200:
                    self.connected_drones[drone_id]['last_ping'] = time.time()
                    return jsonify({'status': 'ping_success', 'response_time': response.elapsed.total_seconds()})
                else:
                    return jsonify({'error': 'Ping failed'}), 500
            except Exception as e:
                # Mark as disconnected if ping fails
                self.drone_status[drone_id]['status'] = 'disconnected'
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/drone/gps/<drone_id>', methods=['GET'])
        def get_drone_gps(drone_id):
            """Get GPS coordinates for a specific drone"""
            if drone_id not in self.connected_drones:
                return jsonify({'error': 'Drone not connected'}), 404
            
            drone_info = self.connected_drones[drone_id]
            try:
                response = requests.get(f'http://{drone_info["ip"]}:{self.api_port}/gps', timeout=5)
                if response.status_code == 200:
                    gps_data = response.json()
                    # Update cached status
                    self.drone_status[drone_id]['gps'] = gps_data
                    return jsonify(gps_data)
                else:
                    return jsonify({'error': 'Failed to get GPS data'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def setup_websocket_handlers(self):
        """Setup WebSocket handlers for real time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client WebSocket connection"""
            emit('connection_status', {'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client WebSocket disconnection"""
            pass
        
        @self.socketio.on('drone_connect')
        def handle_drone_connect(data):
            """Handle drone connection request via WebSocket"""
            drone_id = data.get('drone_id')
            drone_ip = data.get('drone_ip')
            
            # Similar logic as REST API but emit results
            try:
                response = requests.get(f'http://{drone_ip}:{self.api_port}/ping', timeout=5)
                if response.status_code == 200:
                    self.connected_drones[drone_id] = {
                        'ip': drone_ip,
                        'connected_at': datetime.now().isoformat(),
                        'status': 'connected',
                        'last_ping': time.time()
                    }
                    emit('drone_connection_status', {
                        'drone_id': drone_id,
                        'status': 'connected',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    emit('drone_connection_status', {
                        'drone_id': drone_id,
                        'status': 'failed',
                        'error': 'Connection failed'
                    })
            except Exception as e:
                emit('drone_connection_status', {
                    'drone_id': drone_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        @self.socketio.on('request_gps_update')
        def handle_gps_request(data):
            """Handle real time GPS update request"""
            drone_id = data.get('drone_id')
            if drone_id in self.connected_drones:
                self.send_gps_update(drone_id)
    
    def send_gps_update(self, drone_id: str):
        """Send GPS update for a specific drone"""
        if drone_id not in self.connected_drones:
            return
        
        drone_info = self.connected_drones[drone_id]
        try:
            response = requests.get(f'http://{drone_info["ip"]}:{self.api_port}/gps', timeout=3)
            if response.status_code == 200:
                gps_data = response.json()
                self.drone_status[drone_id]['gps'] = gps_data
                
                # Emit to all connected clients
                self.socketio.emit('gps_update', {
                    'drone_id': drone_id,
                    'gps': gps_data,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logging.error(f"Failed to get GPS for drone {drone_id}: {e}")
    
    def start_monitoring(self):
        """Start continuous monitoring of connected drones"""
        def monitor_loop():
            while True:
                try:
                    for drone_id in list(self.connected_drones.keys()):
                        # Check connectivity
                        last_ping = self.connected_drones[drone_id].get('last_ping', 0)
                        if time.time() - last_ping > 30:  # 30 seconds timeout
                            self.drone_status[drone_id]['status'] = 'disconnected'
                            self.socketio.emit('drone_status_update', {
                                'drone_id': drone_id,
                                'status': 'disconnected'
                            })
                        else:
                            # Send GPS update
                            self.send_gps_update(drone_id)
                    
                    time.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    logging.error(f"Monitor loop error: {e}")
                    time.sleep(10)
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def discover_drones(self):
        """Discover available drones on the network"""
        def discovery_loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('', self.discovery_port))
            except OSError as e:
                if e.errno == 98:  # Address already in use
                    print(f"Discovery port {self.discovery_port} already in use, skipping discovery")
                    return
                else:
                    raise
            
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    message = json.loads(data.decode())
                    
                    if message.get('type') == 'drone_announcement':
                        drone_id = message.get('drone_id')
                        drone_ip = addr[0]
                        
                        # Auto-connect to discovered drones
                        if drone_id not in self.connected_drones:
                            self.socketio.emit('drone_discovered', {
                                'drone_id': drone_id,
                                'ip': drone_ip,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                except Exception as e:
                    logging.error(f"Discovery error: {e}")
                    time.sleep(5)
        
        # Start discovery in background thread
        discovery_thread = threading.Thread(target=discovery_loop, daemon=True)
        discovery_thread.start()

def initialize_drone_wireless(app: Flask):
    """Initialize the drone wireless management system"""
    manager = DroneWirelessManager(app)
    manager.start_monitoring()
    manager.discover_drones()
    return manager