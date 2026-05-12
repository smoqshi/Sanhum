#!/usr/bin/env python3
"""
Sanhum Robot - All-in-One Application
Can run as both server (RPi) and client (Windows) with gamepad support
"""

import asyncio
import json
import websockets
import time
import sys
import os
import signal
import platform
import argparse
from typing import Optional, Dict, Any

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
    import tkinter as tk
    from tkinter import ttk, messagebox
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.animation import FuncAnimation
        import numpy as np
        GUI_AVAILABLE = True
    except ImportError:
        print("⚠️  GUI libraries not available - running in terminal mode")
        GUI_AVAILABLE = False
else:
    import termios
    import tty
    import select
    GUI_AVAILABLE = False

# Gamepad support
try:
    import pygame
    GAMEPAD_AVAILABLE = True
except ImportError:
    GAMEPAD_AVAILABLE = False
    print("⚠️  Pygame not found - gamepad support disabled")
    print("💡 Install pygame for gamepad support: pip install pygame")

# GPIO support (RPi only)
try:
    import gpiod
    from gpiod.line import Direction, Value
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

class SanhumRobot:
    def __init__(self, mode="client"):
        self.mode = mode  # "server" or "client"
        self.running = True
        
        # Network settings
        self.RPI_IP = "192.168.0.140"
        self.WEBSOCKET_PORT = 8081
        self.websocket = None
        self.connected = False
        self.clients = set()  # For server mode
        
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
        
        # GUI (Windows only)
        self.root = None
        self.gui_components = {}
        
        # Terminal settings
        self.old_settings = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down Sanhum Robot...")
        self.running = False

    # ========== NETWORKING ==========
    
    async def start_server(self):
        """Start WebSocket server (RPi mode)"""
        print(f"🚀 Starting WebSocket server on {self.RPI_IP}:{self.WEBSOCKET_PORT}")
        
        try:
            async with websockets.serve(self.handle_client, self.RPI_IP, self.WEBSOCKET_PORT):
                print(f"✅ Server running on ws://{self.RPI_IP}:{self.WEBSOCKET_PORT}")
                await asyncio.Future()  # Run forever
        except Exception as e:
            print(f"❌ Server error: {e}")

    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections (server mode)"""
        print(f"🔗 Client connected: {websocket.remote_address}")
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_command(data)
        except websockets.exceptions.ConnectionClosed:
            print(f"🔗 Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)

    async def connect_client(self):
        """Connect to WebSocket server (client mode)"""
        uri = f"ws://{self.RPI_IP}:{self.WEBSOCKET_PORT}"
        
        try:
            print(f"🔌 Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print("✅ Connected to robot!")
            self.connection_time = time.time()
            
            # Start receiving messages
            await self.receive_messages()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False

    async def receive_messages(self):
        """Receive messages from server (client mode)"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.process_telemetry(data)
        except websockets.exceptions.ConnectionClosed:
            print("❌ Connection lost")
            self.connected = False

    async def send_message(self, message: Dict[str, Any]):
        """Send message (server or client mode)"""
        if self.mode == "server":
            # Send to all connected clients
            if self.clients:
                await asyncio.gather(
                    *[client.send(json.dumps(message)) for client in self.clients],
                    return_exceptions=True
                )
        else:
            # Send to server
            if self.connected and self.websocket:
                try:
                    await self.websocket.send(json.dumps(message))
                except Exception as e:
                    print(f"❌ Send error: {e}")
                    self.connected = False

    # ========== ROBOT CONTROL ==========
    
    async def process_command(self, data: Dict[str, Any]):
        """Process incoming command (server mode)"""
        cmd_type = data.get("type")
        
        if cmd_type == "motor_command":
            self.v_linear = data.get("vLinear", 0.0)
            self.v_angular = data.get("vAngular", 0.0)
            self.emergency_stop = data.get("emergency", False)
            
            # Control actual motors (if GPIO available)
            if GPIO_AVAILABLE:
                await self.control_motors()
                
        elif cmd_type == "arm_command":
            self.arm_extend = data.get("extend", 0.5)
            self.gripper = data.get("gripper", 0.3)
            self.turret_angle = data.get("turretAngle", 0.0)
            
            # Control actual arm (if GPIO available)
            if GPIO_AVAILABLE:
                await self.control_arm()
        
        # Send telemetry back
        await self.send_telemetry()

    async def control_motors(self):
        """Control actual motors (RPi only)"""
        # Motor control implementation would go here
        # This is where you'd interface with actual motor drivers
        pass

    async def control_arm(self):
        """Control actual arm (RPi only)"""
        # Arm control implementation would go here
        # This is where you'd interface with actual arm servos
        pass

    def process_telemetry(self, data: Dict[str, Any]):
        """Process telemetry data (client mode)"""
        if data.get("type") == "speed_info":
            self.left_speed = data.get("leftSpeed", 0.0)
            self.right_speed = data.get("rightSpeed", 0.0)
            self.battery_voltage = data.get("batteryV", 12.0)
            
            # Update GUI if available
            if GUI_AVAILABLE and self.root:
                self.update_gui_telemetry()

    async def send_telemetry(self):
        """Send telemetry data (server mode)"""
        if self.mode == "server":
            # Read actual sensor data (if available)
            if GPIO_AVAILABLE:
                # Read battery voltage, sensors, etc.
                pass
            
            telemetry = {
                "type": "speed_info",
                "leftSpeed": self.left_speed,
                "rightSpeed": self.right_speed,
                "batteryV": self.battery_voltage,
                "timestamp": time.time()
            }
            
            await self.send_message(telemetry)

    # ========== INPUT HANDLING ==========
    
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

    def init_gamepad(self):
        """Initialize gamepad"""
        if not GAMEPAD_AVAILABLE:
            print("❌ Gamepad not available - pygame not installed")
            print("💡 To enable gamepad support, install pygame:")
            print("   pip install pygame")
            return False
        
        try:
            pygame.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                print("❌ No gamepad found")
                print("💡 Connect a gamepad and try again")
                return False
            
            self.gamepad = pygame.joystick.Joystick(0)
            self.gamepad.init()
            self.gamepad_connected = True
            print(f"✅ Gamepad connected: {self.gamepad.get_name()}")
            print(f"📊 Axes: {self.gamepad.get_numaxes()}, Buttons: {self.gamepad.get_numbuttons()}")
            self.calibrate_gamepad()
            return True
                
        except Exception as e:
            print(f"❌ Gamepad initialization error: {e}")
            self.gamepad_connected = False
            return False

    def calibrate_gamepad(self):
        """Calibrate gamepad axes"""
        if not self.gamepad_connected:
            return
        
        print("🎮 Calibrating gamepad...")
        print("Move all sticks to center position, then press any button...")
        
        # Wait for button press to center
        waiting = True
        while waiting and self.running:
            pygame.event.pump()
            for i in range(self.gamepad.get_numbuttons()):
                if self.gamepad.get_button(i):
                    waiting = False
                    break
            time.sleep(0.1)
        
        # Record center values
        pygame.event.pump()
        self.center_values = []
        for i in range(self.gamepad.get_numaxes()):
            self.center_values.append(self.gamepad.get_axis(i))
        
        print("✅ Gamepad calibrated!")
        print(f"🎯 Center values: {[f'{v:.2f}' for v in self.center_values]}")

    def get_calibrated_axis(self, axis):
        """Get calibrated axis value"""
        if not self.gamepad_connected or axis >= self.gamepad.get_numaxes():
            return 0.0
        
        raw_value = self.gamepad.get_axis(axis)
        if hasattr(self, 'center_values') and axis < len(self.center_values):
            # Subtract center value and normalize
            centered = raw_value - self.center_values[axis]
            # Deadzone
            if abs(centered) < 0.1:
                return 0.0
            return centered
        return raw_value

    def process_gamepad(self):
        """Process gamepad input"""
        if not self.gamepad_connected or not self.gamepad:
            return
        
        try:
            pygame.event.pump()
            
            # Read calibrated analog sticks
            left_stick_x = self.get_calibrated_axis(0)
            left_stick_y = self.get_calibrated_axis(1)
            right_stick_x = self.get_calibrated_axis(2)
            right_stick_y = self.get_calibrated_axis(3)
            
            # Update controls with calibrated values
            self.v_linear = -left_stick_y
            self.v_angular = left_stick_x
            self.arm_extend = (right_stick_y + 1) / 2
            self.turret_angle = right_stick_x * 180
            
            # Check for emergency stop (A button)
            if self.gamepad.get_button(0):
                self.emergency_stop_action()
                
            # Check for recalibration (Select button, usually button 6)
            if self.gamepad.get_button(6):
                print("🎮 Recalibrating gamepad...")
                self.calibrate_gamepad()
                
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
        elif key == 'g':
            self.init_gamepad()

    def emergency_stop_action(self):
        """Emergency stop action"""
        self.emergency_stop = True
        self.v_linear = 0.0
        self.v_angular = 0.0
        print("🚨 EMERGENCY STOP ACTIVATED!")

    # ========== GUI (Windows only) ==========
    
    def setup_gui(self):
        """Setup GUI interface (Windows only)"""
        if not GUI_AVAILABLE:
            return False
        
        self.root = tk.Tk()
        self.root.title("🤖 Sanhum Robot Control")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection panel
        conn_frame = ttk.LabelFrame(main_frame, text="🔌 Connection")
        conn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(conn_frame, text="RPi IP:").grid(row=0, column=0, padx=5)
        self.gui_components['ip_entry'] = ttk.Entry(conn_frame)
        self.gui_components['ip_entry'].insert(0, self.RPI_IP)
        self.gui_components['ip_entry'].grid(row=0, column=1, padx=5)
        
        self.gui_components['connect_btn'] = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.gui_components['connect_btn'].grid(row=0, column=2, padx=5)
        
        self.gui_components['status_label'] = ttk.Label(conn_frame, text="Disconnected", foreground='red')
        self.gui_components['status_label'].grid(row=0, column=3, padx=5)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Controls")
        control_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Movement controls
        ttk.Label(control_frame, text="Linear Speed:").grid(row=0, column=0, sticky='w')
        self.gui_components['linear_scale'] = ttk.Scale(control_frame, from_=-1.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.gui_components['linear_scale'].set(0.0)
        self.gui_components['linear_scale'].grid(row=0, column=1, padx=5)
        self.gui_components['linear_label'] = ttk.Label(control_frame, text="0.00")
        self.gui_components['linear_label'].grid(row=0, column=2, padx=5)
        
        ttk.Label(control_frame, text="Angular Speed:").grid(row=1, column=0, sticky='w')
        self.gui_components['angular_scale'] = ttk.Scale(control_frame, from_=-1.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.gui_components['angular_scale'].set(0.0)
        self.gui_components['angular_scale'].grid(row=1, column=1, padx=5)
        self.gui_components['angular_label'] = ttk.Label(control_frame, text="0.00")
        self.gui_components['angular_label'].grid(row=1, column=2, padx=5)
        
        # Arm controls
        ttk.Label(control_frame, text="Arm Extend:").grid(row=2, column=0, sticky='w')
        self.gui_components['arm_scale'] = ttk.Scale(control_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.gui_components['arm_scale'].set(0.5)
        self.gui_components['arm_scale'].grid(row=2, column=1, padx=5)
        self.gui_components['arm_label'] = ttk.Label(control_frame, text="0.50")
        self.gui_components['arm_label'].grid(row=2, column=2, padx=5)
        
        ttk.Label(control_frame, text="Gripper:").grid(row=3, column=0, sticky='w')
        self.gui_components['gripper_scale'] = ttk.Scale(control_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.gui_components['gripper_scale'].set(0.3)
        self.gui_components['gripper_scale'].grid(row=3, column=1, padx=5)
        self.gui_components['gripper_label'] = ttk.Label(control_frame, text="0.30")
        self.gui_components['gripper_label'].grid(row=3, column=2, padx=5)
        
        # Emergency stop
        self.gui_components['emergency_btn'] = ttk.Button(control_frame, text="🚨 EMERGENCY STOP", command=self.emergency_stop_action)
        self.gui_components['emergency_btn'].grid(row=4, column=0, columnspan=3, pady=10)
        
        # Bind scale changes
        self.gui_components['linear_scale'].bind('<Motion>', self.on_gui_control_change)
        self.gui_components['angular_scale'].bind('<Motion>', self.on_gui_control_change)
        self.gui_components['arm_scale'].bind('<Motion>', self.on_gui_control_change)
        self.gui_components['gripper_scale'].bind('<Motion>', self.on_gui_control_change)
        
        # Gamepad button
        self.gui_components['gamepad_btn'] = ttk.Button(control_frame, text="🎮 Initialize Gamepad", command=self.init_gamepad)
        self.gui_components['gamepad_btn'].grid(row=5, column=0, columnspan=3, pady=5)
        
        return True

    def on_gui_control_change(self, event=None):
        """Handle GUI control changes"""
        self.v_linear = self.gui_components['linear_scale'].get()
        self.v_angular = self.gui_components['angular_scale'].get()
        self.arm_extend = self.gui_components['arm_scale'].get()
        self.gripper = self.gui_components['gripper_scale'].get()
        
        self.gui_components['linear_label'].config(text=f"{self.v_linear:+.2f}")
        self.gui_components['angular_label'].config(text=f"{self.v_angular:+.2f}")
        self.gui_components['arm_label'].config(text=f"{self.arm_extend:.2f}")
        self.gui_components['gripper_label'].config(text=f"{self.gripper:.2f}")

    def update_gui_telemetry(self):
        """Update GUI telemetry display"""
        if self.gui_components.get('speed_label'):
            self.gui_components['speed_label'].config(text=f"Speed: L={self.left_speed:.2f} R={self.right_speed:.2f}")

    def toggle_connection(self):
        """Toggle connection from GUI"""
        if self.connected:
            self.connected = False
            if self.websocket:
                asyncio.create_task(self.websocket.close())
        else:
            self.RPI_IP = self.gui_components['ip_entry'].get()
            asyncio.create_task(self.connect_client())

    def update_gui_status(self):
        """Update GUI connection status"""
        if self.gui_components.get('status_label'):
            if self.connected:
                self.gui_components['status_label'].config(text="Connected", foreground='green')
                self.gui_components['connect_btn'].config(text="Disconnect")
            else:
                self.gui_components['status_label'].config(text="Disconnected", foreground='red')
                self.gui_components['connect_btn'].config(text="Connect")

    # ========== MAIN LOOPS ==========
    
    async def control_loop(self):
        """Main control loop"""
        while self.running:
            if self.mode == "client":
                # Send commands to server
                if self.connected:
                    motor_cmd = {
                        "type": "motor_command",
                        "vLinear": self.v_linear,
                        "vAngular": self.v_angular,
                        "emergency": self.emergency_stop
                    }
                    await self.send_message(motor_cmd)
                    
                    arm_cmd = {
                        "type": "arm_command",
                        "extend": self.arm_extend,
                        "gripper": self.gripper,
                        "turretAngle": self.turret_angle
                    }
                    await self.send_message(arm_cmd)
                    
                    if self.emergency_stop:
                        self.emergency_stop = False
            
            await asyncio.sleep(0.05)  # 20Hz

    async def input_loop(self):
        """Input processing loop"""
        if GUI_AVAILABLE and self.root:
            # GUI mode - handle gamepad
            while self.running:
                if self.gamepad_connected:
                    self.process_gamepad()
                    self.on_gui_control_change()
                await asyncio.sleep(0.02)
        else:
            # Terminal mode
            self.setup_terminal()
            try:
                while self.running:
                    key = self.get_key()
                    if key:
                        self.process_keyboard(key)
                    
                    if self.gamepad_connected:
                        self.process_gamepad()
                    
                    await asyncio.sleep(0.02)
            finally:
                self.restore_terminal()

    def print_status(self):
        """Print terminal status"""
        if not GUI_AVAILABLE:
            os.system('clear' if platform.system() != "Windows" else 'cls')
            print("="*60)
            print(f"🤖 Sanhum Robot - {self.mode.upper()}")
            print("="*60)
            print(f"🔌 Connection: {'✅ Connected' if self.connected else '❌ Disconnected'}")
            print(f"🎮 Gamepad: {'✅ Connected' if self.gamepad_connected else '❌ Not Connected'}")
            print()
            print("📊 Telemetry:")
            print(f"   Left Speed:  {self.left_speed:+.2f} m/s")
            print(f"   Right Speed: {self.right_speed:+.2f} m/s")
            print(f"   Battery:     {self.battery_voltage:.1f}V")
            print()
            print("🎮 Current Controls:")
            print(f"   Linear:      {self.v_linear:+.2f}")
            print(f"   Angular:     {self.v_angular:+.2f}")
            print(f"   Arm Extend:  {self.arm_extend:.2f}")
            print(f"   Gripper:     {self.gripper:.2f}")
            print(f"   Turret:      {self.turret_angle:+.0f}°")
            print()
            print("⌨️  Controls: w/s/a/d, q/e/r/f/t/g, space=stop, x=emergency, g=gamepad")
            print("="*60)

    async def status_loop(self):
        """Status update loop"""
        while self.running:
            if not GUI_AVAILABLE:
                self.print_status()
            else:
                self.update_gui_status()
            await asyncio.sleep(0.1)

    # ========== MAIN RUN ==========
    
    async def run(self):
        """Main run function"""
        print(f"🤖 Sanhum Robot - {self.mode.upper()} Mode")
        
        # Setup GUI if available and in client mode
        if GUI_AVAILABLE and self.mode == "client":
            if not self.setup_gui():
                print("❌ Failed to setup GUI")
                return
        
        # Start appropriate mode
        tasks = []
        
        if self.mode == "server":
            tasks.append(asyncio.create_task(self.start_server()))
        else:
            tasks.append(asyncio.create_task(self.connect_client()))
        
        # Add common loops
        tasks.append(asyncio.create_task(self.control_loop()))
        tasks.append(asyncio.create_task(self.input_loop()))
        tasks.append(asyncio.create_task(self.status_loop()))
        
        try:
            # Run GUI in main thread if available
            if GUI_AVAILABLE and self.root:
                def run_asyncio():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(asyncio.gather(*tasks))
                
                import threading
                asyncio_thread = threading.Thread(target=run_asyncio, daemon=True)
                asyncio_thread.start()
                
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                self.root.mainloop()
            else:
                await asyncio.gather(*tasks)
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()

    def on_closing(self):
        """Handle GUI closing"""
        self.running = False
        if self.root:
            self.root.destroy()

    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        
        if self.websocket:
            asyncio.create_task(self.websocket.close())
        
        if self.gamepad_connected:
            pygame.quit()
        
        if self.old_settings:
            self.restore_terminal()
        
        print("👋 Sanhum Robot shutdown complete")

async def test_gamepad():
    """Test gamepad functionality"""
    print("🎮 Gamepad Test Tool")
    print("="*50)
    
    if not GAMEPAD_AVAILABLE:
        print("❌ Pygame not available - gamepad support disabled")
        print("💡 To enable gamepad support, install pygame:")
        print("   pip install pygame")
        print()
        print("📋 After installing pygame, run:")
        print("   python3 sanhum_robot.py --mode gamepad-test")
        return
    
    try:
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            print("❌ No gamepad found")
            print("Connect a gamepad and try again")
            return
        
        gamepad = pygame.joystick.Joystick(0)
        gamepad.init()
        
        print(f"✅ Gamepad connected: {gamepad.get_name()}")
        print(f"📊 Axes: {gamepad.get_numaxes()}")
        print(f"🔘 Buttons: {gamepad.get_numbuttons()}")
        print(f"🎯 Hats: {gamepad.get_numhats()}")
        print()
        print("🎮 Move sticks and press buttons to test...")
        print("Press Ctrl+C to exit")
        print("="*50)
        
        while True:
            pygame.event.pump()
            
            # Display axes
            print("\r📊 Axes: ", end="")
            for i in range(gamepad.get_numaxes()):
                value = gamepad.get_axis(i)
                print(f"A{i}:{value:+.2f} ", end="")
            
            # Display buttons
            print("🔘 Buttons: ", end="")
            for i in range(min(gamepad.get_numbuttons(), 10)):  # Limit to first 10 buttons
                if gamepad.get_button(i):
                    print(f"B{i} ", end="")
            
            # Display hats
            for i in range(gamepad.get_numhats()):
                hat = gamepad.get_hat(i)
                if hat != (0, 0):
                    print(f"H{i}:{hat} ", end="")
            
            print(" " * 20, end="\r")  # Clear line
            await asyncio.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n👋 Gamepad test completed")
    except Exception as e:
        print(f"❌ Gamepad test error: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Sanhum Robot Control")
    parser.add_argument("--mode", choices=["server", "client", "gamepad-test"], default="client",
                       help="Run mode: server (RPi), client (Windows), or gamepad-test")
    parser.add_argument("--ip", default="192.168.0.140", help="RPi IP address")
    parser.add_argument("--port", type=int, default=8081, help="WebSocket port")
    
    args = parser.parse_args()
    
    if args.mode == "gamepad-test":
        asyncio.run(test_gamepad())
        return
    
    robot = SanhumRobot(mode=args.mode)
    robot.RPI_IP = args.ip
    robot.WEBSOCKET_PORT = args.port
    
    try:
        asyncio.run(robot.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
