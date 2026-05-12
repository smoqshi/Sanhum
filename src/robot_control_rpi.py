#!/usr/bin/env python3
"""
RPi-Optimized Robot Control App
Lightweight version designed for Raspberry Pi performance
"""

import asyncio
import json
import websockets
import time
import sys
import os
import signal
import platform

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty
    import select

# Gamepad support (optional)
try:
    import pygame
    GAMEPAD_AVAILABLE = True
except ImportError:
    GAMEPAD_AVAILABLE = False

# Lightweight UI options
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

class RPiRobotController:
    def __init__(self):
        self.websocket = None
        self.connected = False
        self.running = True
        self.RPI_IP = "127.0.0.1"  # Localhost for RPi
        self.WEBSOCKET_PORT = 8081
        self.uri = f"ws://{self.RPI_IP}:{self.WEBSOCKET_PORT}"
        
        # Robot state
        self.v_linear = 0.0
        self.v_angular = 0.0
        self.arm_extend = 0.5
        self.gripper = 0.3
        self.turret_angle = 0.0
        self.emergency_stop = False
        
        # Telemetry
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.battery_voltage = 12.0
        self.connection_time = 0
        
        # Gamepad
        self.gamepad = None
        self.gamepad_connected = False
        
        # Terminal settings
        self.old_settings = None
        
        # UI mode
        self.ui_mode = "terminal"  # or "curses" if available
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down robot controller...")
        self.running = False

    def setup_terminal(self):
        """Setup terminal for non-blocking input"""
        if platform.system() != "Windows":
            try:
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
            except:
                pass

    def restore_terminal(self):
        """Restore terminal settings"""
        if self.old_settings and platform.system() != "Windows":
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except:
                pass

    def get_key(self):
        """Get single key press (non-blocking)"""
        if platform.system() == "Windows":
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
        else:
            if self.old_settings:
                try:
                    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                        return sys.stdin.read(1)
                except:
                    pass
        return None

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if platform.system() != "Windows" else 'cls')

    def print_status(self):
        """Print current status"""
        self.clear_screen()
        print("="*60)
        print("🤖 RPi Robot Controller")
        print("="*60)
        print(f"🔌 Connection: {'✅ Connected' if self.connected else '❌ Disconnected'}")
        print(f"🎮 Gamepad: {'✅ Connected' if self.gamepad_connected else '❌ Not Connected'}")
        print()
        print("📊 Telemetry:")
        print(f"   Left Speed:  {self.left_speed:+.2f} m/s")
        print(f"   Right Speed: {self.right_speed:+.2f} m/s")
        print(f"   Battery:     {self.battery_voltage:.1f}V")
        print(f"   Uptime:      {self.connection_time:.0f}s")
        print()
        print("🎮 Current Controls:")
        print(f"   Linear:      {self.v_linear:+.2f}")
        print(f"   Angular:     {self.v_angular:+.2f}")
        print(f"   Arm Extend:  {self.arm_extend:.2f}")
        print(f"   Gripper:     {self.gripper:.2f}")
        print(f"   Turret:      {self.turret_angle:+.0f}°")
        print()
        print("⌨️  Keyboard Controls:")
        print("   w/s - Forward/Backward")
        print("   a/d - Turn Left/Right")
        print("   q/e - Arm Extend/Retract")
        print("   r/f - Gripper Open/Close")
        print("   t/g - Turret Left/Right")
        print("   space - Stop")
        print("   x - Emergency Stop")
        print("   c - Connect/Disconnect")
        print("   g - Initialize Gamepad")
        print("   Ctrl+C - Exit")
        print()
        print("="*60)

    async def connect_websocket(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔌 Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print("✅ Connected to robot!")
            self.connection_time = time.time()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False

    async def disconnect_websocket(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        print("🔌 Disconnected from robot")

    async def send_command(self, command):
        """Send command to robot"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(command))
            except Exception as e:
                print(f"❌ Send error: {e}")
                self.connected = False

    def init_gamepad(self):
        """Initialize gamepad"""
        if not GAMEPAD_AVAILABLE:
            print("❌ Pygame not available - install with: pip install pygame")
            return
        
        try:
            pygame.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() > 0:
                self.gamepad = pygame.joystick.Joystick(0)
                self.gamepad.init()
                self.gamepad_connected = True
                print(f"✅ Gamepad connected: {self.gamepad.get_name()}")
            else:
                print("❌ No gamepad found")
                
        except Exception as e:
            print(f"❌ Gamepad error: {e}")

    def process_gamepad(self):
        """Process gamepad input"""
        if not self.gamepad_connected or not self.gamepad:
            return
        
        try:
            pygame.event.pump()
            
            # Read analog sticks
            left_stick_x = self.gamepad.get_axis(0)  # Left stick X
            left_stick_y = self.gamepad.get_axis(1)  # Left stick Y
            right_stick_x = self.gamepad.get_axis(2)  # Right stick X
            right_stick_y = self.gamepad.get_axis(3)  # Right stick Y
            
            # Update movement from left stick
            self.v_linear = -left_stick_y  # Invert Y for forward/backward
            self.v_angular = left_stick_x
            
            # Update arm from right stick
            self.arm_extend = (right_stick_y + 1) / 2  # Normalize to 0-1
            self.turret_angle = right_stick_x * 180  # Convert to -180 to 180
            
            # Check for emergency stop (A button)
            if self.gamepad.get_button(0):
                self.emergency_stop_action()
                
        except Exception as e:
            print(f"❌ Gamepad error: {e}")
            self.gamepad_connected = False

    def process_keyboard(self, key):
        """Process keyboard input"""
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
        elif key == 'x':
            self.emergency_stop_action()
        elif key == 'c':
            if self.connected:
                asyncio.create_task(self.disconnect_websocket())
            else:
                asyncio.create_task(self.connect_websocket())
        elif key == '\x03':  # Ctrl+C
            self.running = False

    def emergency_stop_action(self):
        """Emergency stop action"""
        self.emergency_stop = True
        self.v_linear = 0.0
        self.v_angular = 0.0
        print("🚨 EMERGENCY STOP ACTIVATED!")

    async def websocket_loop(self):
        """WebSocket message receiving loop"""
        while self.running:
            if self.connected and self.websocket:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    data = json.loads(message)
                    
                    if data.get('type') == 'speed_info':
                        self.left_speed = data.get('leftSpeed', 0)
                        self.right_speed = data.get('rightSpeed', 0)
                        self.battery_voltage = data.get('batteryV', 12.0)
                        
                except asyncio.TimeoutError:
                    pass
                except websockets.exceptions.ConnectionClosed:
                    self.connected = False
                    print("❌ Connection lost")
                except Exception as e:
                    print(f"❌ WebSocket error: {e}")
                    self.connected = False
            
            await asyncio.sleep(0.05)

    async def control_loop(self):
        """Control command sending loop"""
        while self.running:
            if self.connected:
                # Send motor command
                motor_cmd = {
                    "type": "motor_command",
                    "vLinear": self.v_linear,
                    "vAngular": self.v_angular,
                    "emergency": self.emergency_stop
                }
                await self.send_command(motor_cmd)
                
                # Send arm command
                arm_cmd = {
                    "type": "arm_command",
                    "extend": self.arm_extend,
                    "gripper": self.gripper,
                    "turretAngle": self.turret_angle
                }
                await self.send_command(arm_cmd)
                
                # Reset emergency stop flag
                if self.emergency_stop:
                    self.emergency_stop = False
            
            await asyncio.sleep(0.05)  # 20Hz control rate

    async def ui_loop(self):
        """Main UI and input loop"""
        last_status_update = time.time()
        
        while self.running:
            # Process keyboard input
            key = self.get_key()
            if key:
                self.process_keyboard(key)
            
            # Process gamepad input
            if self.gamepad_connected:
                self.process_gamepad()
            
            # Update status display
            current_time = time.time()
            if current_time - last_status_update > 0.1:  # Update every 100ms
                if self.connected:
                    self.connection_time = current_time - self.connection_time
                self.print_status()
                last_status_update = current_time
            
            await asyncio.sleep(0.02)  # 50Hz input polling

    async def run(self):
        """Main run function"""
        print("🤖 RPi Robot Controller Starting...")
        print("Lightweight robot control for Raspberry Pi")
        print()
        
        self.setup_terminal()
        
        try:
            # Start background tasks
            tasks = [
                asyncio.create_task(self.websocket_loop()),
                asyncio.create_task(self.control_loop()),
                asyncio.create_task(self.ui_loop())
            ]
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.running = False
            self.restore_terminal()
            
            if self.websocket:
                await self.websocket.close()
            
            if self.gamepad_connected:
                pygame.quit()
            
            print("👋 Robot controller shutdown complete")

def main():
    """Main function"""
    controller = RPiRobotController()
    
    try:
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
