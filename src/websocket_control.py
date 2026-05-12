#!/usr/bin/env python3
"""
Interactive WebSocket Robot Control Script
Real-time control of the robot via WebSocket connection
"""

import asyncio
import json
import websockets
import time
import threading
import sys
import platform

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty

class RobotController:
    def __init__(self):
        self.websocket = None
        self.connected = False
        self.running = True
        self.RPI_IP = "192.168.0.140"
        self.WEBSOCKET_PORT = 8081
        self.uri = f"ws://{self.RPI_IP}:{self.WEBSOCKET_PORT}"
        
        # Control state
        self.v_linear = 0.0
        self.v_angular = 0.0
        self.arm_extend = 0.5
        self.gripper = 0.3
        self.turret_angle = 0.0
        
        # Terminal settings for non-blocking input
        self.old_settings = None

    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print("✅ Connected to robot!")
            
            # Start receiving messages in background
            asyncio.create_task(self.receive_messages())
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False

    async def receive_messages(self):
        """Receive messages from WebSocket server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'speed_info':
                        print(f"\r📊 Speed: L={data.get('leftSpeed', 0):.2f}m/s R={data.get('rightSpeed', 0):.2f}m/s Battery: {data.get('batteryV', 0):.1f}V", end='', flush=True)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Connection closed")
            self.connected = False

    async def send_command(self, command):
        """Send command to robot"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(command))
            except Exception as e:
                print(f"❌ Send error: {e}")

    def get_key(self):
        """Get single key press (non-blocking)"""
        if platform.system() == "Windows":
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
        else:
            if self.old_settings:
                try:
                    import select
                    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                        return sys.stdin.read(1)
                except:
                    pass
        return None

    def setup_terminal(self):
        """Setup terminal for non-blocking input"""
        if platform.system() == "Windows":
            # Windows doesn't need special terminal setup
            pass
        else:
            try:
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
            except:
                pass

    def restore_terminal(self):
        """Restore terminal settings"""
        if platform.system() == "Windows":
            # Windows doesn't need terminal restoration
            pass
        else:
            if self.old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                except:
                    pass

    def print_controls(self):
        """Print control instructions"""
        print("\n" + "="*60)
        print("🤖 ROBOT CONTROLS")
        print("="*60)
        print("\n📱 MOVEMENT:")
        print("  w/s - Forward/Backward")
        print("  a/d - Turn Left/Right")
        print("  space - Stop")
        print("\n🦾 ARM CONTROL:")
        print("  q/e - Extend/Retract Arm")
        print("  r/f - Open/Close Gripper")
        print("  t/g - Rotate Turret Left/Right")
        print("\n⚠️  EMERGENCY:")
        print("  x - EMERGENCY STOP")
        print("\n🚪 EXIT:")
        print("  Ctrl+C - Exit")
        print("\n" + "="*60)

    async def control_loop(self):
        """Main control loop"""
        self.print_controls()
        
        while self.running and self.connected:
            key = self.get_key()
            
            if key:
                # Movement controls
                if key == 'w':
                    self.v_linear = min(1.0, self.v_linear + 0.1)
                elif key == 's':
                    self.v_linear = max(-1.0, self.v_linear - 0.1)
                elif key == 'a':
                    self.v_angular = max(-1.0, self.v_angular - 0.1)
                elif key == 'd':
                    self.v_angular = min(1.0, self.v_angular + 0.1)
                elif key == ' ':
                    self.v_linear = 0.0
                    self.v_angular = 0.0
                
                # Arm controls
                elif key == 'q':
                    self.arm_extend = min(1.0, self.arm_extend + 0.1)
                elif key == 'e':
                    self.arm_extend = max(0.0, self.arm_extend - 0.1)
                elif key == 'r':
                    self.gripper = min(1.0, self.gripper + 0.1)
                elif key == 'f':
                    self.gripper = max(0.0, self.gripper - 0.1)
                elif key == 't':
                    self.turret_angle = min(180, self.turret_angle + 10)
                elif key == 'g':
                    self.turret_angle = max(-180, self.turret_angle - 10)
                
                # Emergency stop
                elif key == 'x':
                    await self.send_command({
                        "type": "motor_command",
                        "vLinear": 0.0,
                        "vAngular": 0.0,
                        "emergency": True
                    })
                    print("\n🚨 EMERGENCY STOP ACTIVATED!")
                    continue
                
                # Send motor command
                await self.send_command({
                    "type": "motor_command",
                    "vLinear": self.v_linear,
                    "vAngular": self.v_angular,
                    "emergency": False
                })
                
                # Send arm command
                await self.send_command({
                    "type": "arm_command",
                    "extend": self.arm_extend,
                    "gripper": self.gripper,
                    "turretAngle": self.turret_angle
                })
                
                # Display current state
                print(f"\r🎮 Linear: {self.v_linear:+.1f} | Angular: {self.v_angular:+.1f} | Arm: {self.arm_extend:.1f} | Grip: {self.gripper:.1f} | Turret: {self.turret_angle:+.0f}°", end='', flush=True)
            
            await asyncio.sleep(0.05)  # 20Hz control rate

    async def run(self):
        """Main run function"""
        self.setup_terminal()
        
        try:
            await self.connect()
            
            if self.connected:
                await self.control_loop()
            else:
                print("❌ Failed to connect to robot")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.running = False
            self.restore_terminal()
            
            if self.websocket:
                await self.websocket.close()

def main():
    """Main function"""
    print("🤖 WebSocket Robot Controller")
    print("Real-time robot control via WebSocket")
    print()
    
    controller = RobotController()
    
    try:
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
