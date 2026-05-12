#!/usr/bin/env python3
"""
WebSocket Client Test Script
Connects to the WebSocket server without browser to test functionality
"""

import asyncio
import json
import websockets
import time

async def test_websocket_connection():
    """Test WebSocket connection and command sending"""
    
    # WebSocket server configuration
    RPI_IP = "192.168.0.140"
    WEBSOCKET_PORT = 8081
    uri = f"ws://{RPI_IP}:{WEBSOCKET_PORT}"
    
    print(f"Connecting to WebSocket server at {uri}")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server!")
            
            # Test motor commands
            test_commands = [
                {"type": "motor_command", "vLinear": 0.5, "vAngular": 0.0, "emergency": False},
                {"type": "motor_command", "vLinear": 0.0, "vAngular": 0.5, "emergency": False},
                {"type": "motor_command", "vLinear": -0.3, "vAngular": -0.2, "emergency": False},
                {"type": "motor_command", "vLinear": 0.0, "vAngular": 0.0, "emergency": False},
            ]
            
            # Send test commands
            for i, command in enumerate(test_commands):
                print(f"\n--- Test Command {i+1} ---")
                print(f"Sending: {command}")
                
                await websocket.send(json.dumps(command))
                print("Command sent successfully!")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"Response: {response}")
                except asyncio.TimeoutError:
                    print("No response received (timeout)")
                
                # Wait between commands
                await asyncio.sleep(1)
            
            # Test arm commands
            arm_commands = [
                {"type": "arm_command", "extend": 0.5, "gripper": 0.3, "turretAngle": 0},
                {"type": "arm_command", "extend": 0.8, "gripper": 0.7, "turretAngle": 45},
                {"type": "arm_command", "extend": 0.2, "gripper": 0.1, "turretAngle": -90},
            ]
            
            print("\n=== Testing Arm Commands ===")
            for i, command in enumerate(arm_commands):
                print(f"\n--- Arm Command {i+1} ---")
                print(f"Sending: {command}")
                
                await websocket.send(json.dumps(command))
                print("Arm command sent successfully!")
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"Response: {response}")
                except asyncio.TimeoutError:
                    print("No response received (timeout)")
                
                await asyncio.sleep(1)
            
            print("\n✅ All tests completed successfully!")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused! WebSocket server may not be running.")
        print(f"Make sure the WebSocket server is running on {RPI_IP}:{WEBSOCKET_PORT}")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Connection closed unexpectedly!")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("=== WebSocket Client Test ===")
    print("This script tests the WebSocket server without using a browser.")
    print("Make sure the WebSocket server is running on the RPi.")
    print()
    
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
