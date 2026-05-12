#!/usr/bin/env python3
"""
WebSocket Server for Sanhum Robot Control
Provides real-time communication with minimal delays
Replaces UDP for browser compatibility
"""

import asyncio
import json
import websockets
import threading
import time
import logging
from typing import Dict, Any, Set

# Configure logging for WebSocket system
# Logs appear in terminal AND saved to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Terminal output (real-time)
        logging.FileHandler('/tmp/sanhum_websocket.log')  # File backup
    ]
)
logger = logging.getLogger('websocket_server')

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        
        # Motor state
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.battery_voltage = 12.6
        self.last_command_time = 0
        
        logger.info(f"WebSocket Server starting on {host}:{port}")
    
    async def register_client(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            # Send initial status
            await self.send_speed_info(websocket)
            
            # Keep connection alive and handle messages
            async for message in websocket:
                await self.handle_message(message, websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_message(self, message: str, websocket):
        """Handle incoming WebSocket messages"""
        try:
            command = json.loads(message)
            logger.debug(f"Received command: {command}")
            
            # Process different command types
            if command.get('type') == 'motor_command':
                await self.process_motor_command(command, websocket)
            elif command.get('type') == 'arm_command':
                await self.process_arm_command(command, websocket)
            elif command.get('type') == 'get_status':
                await self.send_status(websocket)
                
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Invalid message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def process_motor_command(self, command: Dict[str, Any], websocket):
        """Process motor control commands"""
        try:
            v_linear = command.get('vLinear', 0.0)
            v_angular = command.get('vAngular', 0.0)
            emergency = command.get('emergency', False)
            
            if emergency:
                logger.warning("Emergency stop received")
                self.left_speed = 0.0
                self.right_speed = 0.0
            else:
                # Convert to wheel speeds (simplified kinematics)
                # vL = v - w * L/2, vR = v + w * L/2
                track_width = 0.5  # meters
                self.left_speed = v_linear - v_angular * track_width / 2
                self.right_speed = v_linear + v_angular * track_width / 2
            
            self.last_command_time = time.time()
            
            # Send speed info back to client
            await self.send_speed_info(websocket)
            
            # Here you would interface with actual motor control
            # For now, just log the command
            logger.info(f"Motor command: v={v_linear:.2f}, w={v_angular:.2f}")
            logger.info(f"Wheel speeds: L={self.left_speed:.2f}, R={self.right_speed:.2f}")
            
            # Send to motor control process
            self.send_to_motor_control(v_linear, v_angular, emergency)
            
        except Exception as e:
            logger.error(f"Error processing motor command: {e}")
    
    async def process_arm_command(self, command: Dict[str, Any], websocket):
        """Process arm control commands"""
        try:
            extend = command.get('extend', 0.0)
            gripper = command.get('gripper', 0.0)
            turret_angle = command.get('turretAngle', 0.0)
            
            logger.info(f"Arm command: extend={extend:.2f}, gripper={gripper:.2f}, turret={turret_angle:.1f}")
            
            # Here you would interface with actual arm control
            # For now, just log the command
            
        except Exception as e:
            logger.error(f"Error processing arm command: {e}")
    
    def send_to_motor_control(self, v_linear, v_angular, emergency):
        """Send command to motor control process via UDP"""
        try:
            import socket
            import struct
            
            # Send to motor control UDP port
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(struct.pack('ff', v_linear, v_angular), ('127.0.0.1', 5005))
            sock.close()
            logger.debug(f"Sent motor command to UDP: v={v_linear:.2f}, w={v_angular:.2f}")
            
        except Exception as e:
            logger.error(f"Error sending to motor control: {e}")
    
    async def send_speed_info(self, websocket=None):
        """Send current speed and battery info to client(s)"""
        try:
            speed_info = {
                'type': 'speed_info',
                'leftSpeed': round(self.left_speed, 3),
                'rightSpeed': round(self.right_speed, 3),
                'batteryV': round(self.battery_voltage, 2),
                'timestamp': int(time.time() * 1000)
            }
            
            message = json.dumps(speed_info)
            
            if websocket:
                await websocket.send(message)
                logger.debug(f"Sent speed info to single client")
            else:
                # Broadcast to all clients
                if self.clients:
                    await asyncio.gather(
                        *[client.send(message) for client in self.clients],
                        return_exceptions=True
                    )
                    logger.debug(f"Broadcast speed info to {len(self.clients)} clients")
            
        except Exception as e:
            logger.error(f"Error sending speed info: {e}")
    
    async def send_status(self, websocket=None):
        """Send full status to client(s)"""
        try:
            status = {
                'type': 'status',
                'leftSpeed': round(self.left_speed, 3),
                'rightSpeed': round(self.right_speed, 3),
                'batteryV': round(self.battery_voltage, 2),
                'timestamp': int(time.time() * 1000)
            }
            
            message = json.dumps(status)
            
            if websocket:
                await websocket.send(message)
            else:
                # Broadcast to all clients
                if self.clients:
                    await asyncio.gather(
                        *[client.send(message) for client in self.clients],
                        return_exceptions=True
                    )
            
        except Exception as e:
            logger.error(f"Error sending status: {e}")
    
    async def start(self):
        """Start the WebSocket server"""
        self.running = True
        
        try:
            async with websockets.serve(self.register_client, self.host, self.port):
                logger.info(f"WebSocket Server listening on {self.host}:{self.port}")
                await asyncio.Future()  # Run forever
        except Exception as e:
            logger.error(f"WebSocket Server error: {e}")
    
    def stop(self):
        """Stop the WebSocket server"""
        self.running = False
        logger.info("WebSocket Server stopped")

async def main():
    """Main function to run the WebSocket server"""
    server = WebSocketServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down WebSocket server...")
        server.stop()

if __name__ == "__main__":
    asyncio.run(main())
