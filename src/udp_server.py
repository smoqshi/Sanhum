#!/usr/bin/env python3
"""
UDP Server for Sanhum Robot Control
Provides real-time communication with minimal delays
"""

import asyncio
import json
import socket
import threading
import time
from typing import Dict, Any

class UDPServer:
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.clients = set()
        self.running = False
        
        # Motor state
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.battery_voltage = 12.6
        self.last_command_time = 0
        
        print(f"UDP Server starting on {host}:{port}")
    
    async def start(self):
        """Start the UDP server"""
        self.running = True
        
        # Create UDP socket
        loop = asyncio.get_event_loop()
        
        try:
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: self.handle_client, 
                self.host, self.port
            )
            
            print(f"UDP Server listening on {self.host}:{self.port}")
            
            # Keep server running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"UDP Server error: {e}")
        finally:
            if transport:
                transport.close()
    
    async def handle_client(self, data: bytes, addr):
        """Handle incoming UDP messages"""
        try:
            message = data.decode('utf-8')
            command = json.loads(message)
            
            print(f"UDP received from {addr}: {command}")
            
            # Process different command types
            if command.get('type') == 'motor_command':
                await self.process_motor_command(command, addr)
            elif command.get('type') == 'arm_command':
                await self.process_arm_command(command, addr)
            elif command.get('type') == 'get_status':
                await self.send_status(addr)
                
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Invalid message from {addr}: {e}")
        except Exception as e:
            print(f"Error processing message from {addr}: {e}")
    
    async def process_motor_command(self, command: Dict[str, Any], addr):
        """Process motor control commands"""
        try:
            v_linear = command.get('vLinear', 0.0)
            v_angular = command.get('vAngular', 0.0)
            emergency = command.get('emergency', False)
            
            if emergency:
                print(f"Emergency stop received from {addr}")
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
            await self.send_speed_info(addr)
            
            # Here you would interface with actual motor control
            # For now, just print the command
            print(f"Motor command: v={v_linear:.2f}, w={v_angular:.2f}")
            print(f"Wheel speeds: L={self.left_speed:.2f}, R={self.right_speed:.2f}")
            
        except Exception as e:
            print(f"Error processing motor command: {e}")
    
    async def process_arm_command(self, command: Dict[str, Any], addr):
        """Process arm control commands"""
        try:
            extend = command.get('extend', 0.0)
            gripper = command.get('gripper', 0.0)
            turret_angle = command.get('turretAngle', 0.0)
            
            print(f"Arm command: extend={extend:.2f}, gripper={gripper:.2f}, turret={turret_angle:.1f}")
            
            # Here you would interface with actual arm control
            # For now, just print the command
            
        except Exception as e:
            print(f"Error processing arm command: {e}")
    
    async def send_speed_info(self, addr):
        """Send current speed and battery info to client"""
        try:
            speed_info = {
                'type': 'speed_info',
                'leftSpeed': round(self.left_speed, 3),
                'rightSpeed': round(self.right_speed, 3),
                'batteryV': round(self.battery_voltage, 2),
                'timestamp': int(time.time() * 1000)
            }
            
            message = json.dumps(speed_info).encode('utf-8')
            
            # Send back to client
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: None, '0.0.0.0', 0
            )
            
            transport.sendto(message, addr)
            print(f"Sent speed info to {addr}")
            
        except Exception as e:
            print(f"Error sending speed info: {e}")
    
    async def send_status(self, addr):
        """Send full status to client"""
        try:
            status = {
                'type': 'status',
                'leftSpeed': round(self.left_speed, 3),
                'rightSpeed': round(self.right_speed, 3),
                'batteryV': round(self.battery_voltage, 2),
                'timestamp': int(time.time() * 1000)
            }
            
            message = json.dumps(status).encode('utf-8')
            
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: None, '0.0.0.0', 0
            )
            
            transport.sendto(message, addr)
            print(f"Sent status to {addr}")
            
        except Exception as e:
            print(f"Error sending status: {e}")
    
    def stop(self):
        """Stop the UDP server"""
        self.running = False
        print("UDP Server stopped")

async def main():
    """Main function to run the UDP server"""
    server = UDPServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down UDP server...")
        server.stop()

if __name__ == "__main__":
    asyncio.run(main())
