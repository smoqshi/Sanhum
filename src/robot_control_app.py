#!/usr/bin/env python3
"""
All-in-One Robot Control App
Unified application with gamepad control and WebSocket communication
"""

import asyncio
import json
import websockets
import time
import threading
import sys
import platform
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty

# Gamepad support
try:
    import pygame
    GAMEPAD_AVAILABLE = True
except ImportError:
    GAMEPAD_AVAILABLE = False
    print("⚠️  Pygame not installed - gamepad control disabled")
    print("Install with: pip install pygame")

class RobotControlApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Sanhum Robot Control")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # WebSocket connection
        self.websocket = None
        self.connected = False
        self.running = True
        self.RPI_IP = "192.168.0.140"
        self.WEBSOCKET_PORT = 8081
        self.uri = f"ws://{self.RPI_IP}:{self.WEBSOCKET_PORT}"
        
        # Robot state
        self.v_linear = 0.0
        self.v_angular = 0.0
        self.arm_extend = 0.5
        self.gripper = 0.3
        self.turret_angle = 0.0
        self.emergency_stop = False
        
        # Telemetry data
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.battery_voltage = 12.0
        self.speed_history = {'left': [], 'right': [], 'time': []}
        self.max_history_points = 100
        
        # Gamepad
        self.gamepad = None
        self.gamepad_connected = False
        
        # Setup UI
        self.setup_ui()
        
        # Start background tasks
        self.setup_background_tasks()

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection panel
        self.setup_connection_panel(main_frame)
        
        # Control panel
        self.setup_control_panel(main_frame)
        
        # Telemetry panel
        self.setup_telemetry_panel(main_frame)
        
        # Gamepad panel
        self.setup_gamepad_panel(main_frame)

    def setup_connection_panel(self, parent):
        """Setup connection control panel"""
        conn_frame = ttk.LabelFrame(parent, text="🔌 Connection", style='Dark.TLabelframe')
        conn_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=5)
        
        # IP and Port
        ttk.Label(conn_frame, text="RPi IP:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = ttk.Entry(conn_frame, textvariable=tk.StringVar(value=self.RPI_IP))
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
        self.port_entry = ttk.Entry(conn_frame, textvariable=tk.StringVar(value=str(self.WEBSOCKET_PORT)))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Connection button
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Status
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground='red')
        self.status_label.grid(row=0, column=5, padx=5, pady=5)

    def setup_control_panel(self, parent):
        """Setup robot control panel"""
        control_frame = ttk.LabelFrame(parent, text="🎮 Robot Control", style='Dark.TLabelframe')
        control_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # Movement controls
        ttk.Label(control_frame, text="Movement", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(control_frame, text="Linear Speed:").grid(row=1, column=0, sticky='w', padx=5)
        self.linear_scale = ttk.Scale(control_frame, from_=-1.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.linear_scale.set(0.0)
        self.linear_scale.grid(row=1, column=1, padx=5, pady=2)
        self.linear_label = ttk.Label(control_frame, text="0.00")
        self.linear_label.grid(row=1, column=2, padx=5)
        
        ttk.Label(control_frame, text="Angular Speed:").grid(row=2, column=0, sticky='w', padx=5)
        self.angular_scale = ttk.Scale(control_frame, from_=-1.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.angular_scale.set(0.0)
        self.angular_scale.grid(row=2, column=1, padx=5, pady=2)
        self.angular_label = ttk.Label(control_frame, text="0.00")
        self.angular_label.grid(row=2, column=2, padx=5)
        
        # Arm controls
        ttk.Label(control_frame, text="Arm Control", font=('Arial', 12, 'bold')).grid(row=3, column=0, columnspan=2, pady=(10,5))
        
        ttk.Label(control_frame, text="Extension:").grid(row=4, column=0, sticky='w', padx=5)
        self.arm_scale = ttk.Scale(control_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.arm_scale.set(0.5)
        self.arm_scale.grid(row=4, column=1, padx=5, pady=2)
        self.arm_label = ttk.Label(control_frame, text="0.50")
        self.arm_label.grid(row=4, column=2, padx=5)
        
        ttk.Label(control_frame, text="Gripper:").grid(row=5, column=0, sticky='w', padx=5)
        self.gripper_scale = ttk.Scale(control_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        self.gripper_scale.set(0.3)
        self.gripper_scale.grid(row=5, column=1, padx=5, pady=2)
        self.gripper_label = ttk.Label(control_frame, text="0.30")
        self.gripper_label.grid(row=5, column=2, padx=5)
        
        ttk.Label(control_frame, text="Turret Angle:").grid(row=6, column=0, sticky='w', padx=5)
        self.turret_scale = ttk.Scale(control_frame, from_=-180, to=180, orient=tk.HORIZONTAL, length=200)
        self.turret_scale.set(0.0)
        self.turret_scale.grid(row=6, column=1, padx=5, pady=2)
        self.turret_label = ttk.Label(control_frame, text="0°")
        self.turret_label.grid(row=6, column=2, padx=5)
        
        # Emergency stop
        self.emergency_btn = ttk.Button(control_frame, text="🚨 EMERGENCY STOP", command=self.emergency_stop_action)
        self.emergency_btn.grid(row=7, column=0, columnspan=3, pady=10)
        
        # Bind scale changes
        self.linear_scale.bind('<Motion>', self.on_control_change)
        self.angular_scale.bind('<Motion>', self.on_control_change)
        self.arm_scale.bind('<Motion>', self.on_control_change)
        self.gripper_scale.bind('<Motion>', self.on_control_change)
        self.turret_scale.bind('<Motion>', self.on_control_change)

    def setup_telemetry_panel(self, parent):
        """Setup telemetry display panel"""
        telemetry_frame = ttk.LabelFrame(parent, text="📊 Telemetry", style='Dark.TLabelframe')
        telemetry_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        
        # Status display
        status_frame = ttk.Frame(telemetry_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.speed_label = ttk.Label(status_frame, text="Speed: L=0.00m/s R=0.00m/s")
        self.speed_label.pack(anchor='w')
        
        self.battery_label = ttk.Label(status_frame, text="Battery: 12.0V")
        self.battery_label.pack(anchor='w')
        
        self.connection_time_label = ttk.Label(status_frame, text="Connected: 0s")
        self.connection_time_label.pack(anchor='w')
        
        # Speed graph
        self.fig, self.ax = plt.subplots(figsize=(6, 3), facecolor='#2e2e2e')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.set_xlabel('Time (s)', color='white')
        self.ax.set_ylabel('Speed (m/s)', color='white')
        self.ax.set_title('Real-time Speed', color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3)
        
        self.line_left, = self.ax.plot([], [], 'b-', label='Left', linewidth=2)
        self.line_right, = self.ax.plot([], [], 'r-', label='Right', linewidth=2)
        self.ax.legend(loc='upper right')
        
        self.canvas = FigureCanvasTkAgg(self.fig, telemetry_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Start animation
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=100, blit=False)

    def setup_gamepad_panel(self, parent):
        """Setup gamepad control panel"""
        gamepad_frame = ttk.LabelFrame(parent, text="🎮 Gamepad", style='Dark.TLabelframe')
        gamepad_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        
        # Gamepad status
        self.gamepad_status_label = ttk.Label(gamepad_frame, text="Gamepad: Not Connected", foreground='red')
        self.gamepad_status_label.pack(pady=5)
        
        # Gamepad info
        self.gamepad_info_label = ttk.Label(gamepad_frame, text="Connect a gamepad to use gamepad control")
        self.gamepad_info_label.pack(pady=5)
        
        # Initialize gamepad button
        self.init_gamepad_btn = ttk.Button(gamepad_frame, text="Initialize Gamepad", command=self.init_gamepad)
        self.init_gamepad_btn.pack(pady=5)

    def setup_background_tasks(self):
        """Setup background tasks"""
        # WebSocket connection task
        asyncio.create_task(self.websocket_loop())
        
        # Gamepad polling task
        if GAMEPAD_AVAILABLE:
            asyncio.create_task(self.gamepad_loop())
        
        # Control sending task
        asyncio.create_task(self.control_loop())

    async def websocket_loop(self):
        """Main WebSocket connection loop"""
        while self.running:
            if self.connected and self.websocket:
                try:
                    # Receive messages
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    data = json.loads(message)
                    
                    if data.get('type') == 'speed_info':
                        self.left_speed = data.get('leftSpeed', 0)
                        self.right_speed = data.get('rightSpeed', 0)
                        self.battery_voltage = data.get('batteryV', 12.0)
                        
                        # Update speed history
                        current_time = time.time()
                        self.speed_history['time'].append(current_time)
                        self.speed_history['left'].append(self.left_speed)
                        self.speed_history['right'].append(self.right_speed)
                        
                        # Limit history size
                        if len(self.speed_history['time']) > self.max_history_points:
                            self.speed_history['time'].pop(0)
                            self.speed_history['left'].pop(0)
                            self.speed_history['right'].pop(0)
                        
                except asyncio.TimeoutError:
                    pass
                except websockets.exceptions.ConnectionClosed:
                    self.connected = False
                    self.update_connection_status()
                except Exception as e:
                    print(f"WebSocket error: {e}")
                    self.connected = False
                    self.update_connection_status()
            
            await asyncio.sleep(0.05)

    async def gamepad_loop(self):
        """Gamepad polling loop"""
        if not GAMEPAD_AVAILABLE:
            return
            
        while self.running:
            if self.gamepad_connected and self.gamepad:
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
                    
                    # Update arm from right stick or triggers
                    if self.gamepad.get_numaxes() >= 5:
                        trigger_right = self.gamepad.get_axis(4)  # Right trigger
                        trigger_left = self.gamepad.get_axis(5)   # Left trigger
                        
                        # Use triggers for gripper control
                        self.gripper = (trigger_right + 1) / 2  # Normalize to 0-1
                    
                    # Update UI scales
                    self.linear_scale.set(self.v_linear)
                    self.angular_scale.set(self.v_angular)
                    self.gripper_scale.set(self.gripper)
                    
                    # Check for emergency stop
                    if self.gamepad.get_button(0):  # A button
                        self.emergency_stop_action()
                    
                except Exception as e:
                    print(f"Gamepad error: {e}")
                    self.gamepad_connected = False
                    self.update_gamepad_status()
            
            await asyncio.sleep(0.02)  # 50Hz polling

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

    def on_control_change(self, event=None):
        """Handle control slider changes"""
        self.v_linear = self.linear_scale.get()
        self.v_angular = self.angular_scale.get()
        self.arm_extend = self.arm_scale.get()
        self.gripper = self.gripper_scale.get()
        self.turret_angle = self.turret_scale.get()
        
        # Update labels
        self.linear_label.config(text=f"{self.v_linear:+.2f}")
        self.angular_label.config(text=f"{self.v_angular:+.2f}")
        self.arm_label.config(text=f"{self.arm_extend:.2f}")
        self.gripper_label.config(text=f"{self.gripper:.2f}")
        self.turret_label.config(text=f"{int(self.turret_angle)}°")

    def update_plot(self, frame):
        """Update speed plot"""
        if self.speed_history['time']:
            # Convert time to relative seconds
            times = np.array(self.speed_history['time'])
            if len(times) > 1:
                times = times - times[0]
                
                self.line_left.set_data(times, self.speed_history['left'])
                self.line_right.set_data(times, self.speed_history['right'])
                
                self.ax.set_xlim(0, max(times[-1], 10))
                self.ax.set_ylim(-1, 1)
                
        return self.line_left, self.line_right

    def update_connection_status(self):
        """Update connection status display"""
        if self.connected:
            self.status_label.config(text="Connected", foreground='green')
            self.connect_btn.config(text="Disconnect")
        else:
            self.status_label.config(text="Disconnected", foreground='red')
            self.connect_btn.config(text="Connect")

    def update_gamepad_status(self):
        """Update gamepad status display"""
        if self.gamepad_connected:
            self.gamepad_status_label.config(text="Gamepad: Connected", foreground='green')
            self.gamepad_info_label.config(text=f"Using: {pygame.joystick.Joystick(self.gamepad.get_id()).get_name()}")
        else:
            self.gamepad_status_label.config(text="Gamepad: Not Connected", foreground='red')
            self.gamepad_info_label.config(text="Connect a gamepad to use gamepad control")

    def update_telemetry_display(self):
        """Update telemetry display"""
        self.speed_label.config(text=f"Speed: L={self.left_speed:.2f}m/s R={self.right_speed:.2f}m/s")
        self.battery_label.config(text=f"Battery: {self.battery_voltage:.1f}V")

    async def send_command(self, command):
        """Send command to robot"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(command))
            except Exception as e:
                print(f"Send error: {e}")

    async def connect_websocket(self):
        """Connect to WebSocket server"""
        try:
            self.RPI_IP = self.ip_entry.get()
            self.WEBSOCKET_PORT = int(self.port_entry.get())
            self.uri = f"ws://{self.RPI_IP}:{self.WEBSOCKET_PORT}"
            
            print(f"Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print("✅ Connected to robot!")
            self.update_connection_status()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            self.update_connection_status()
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    async def disconnect_websocket(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        self.update_connection_status()

    def toggle_connection(self):
        """Toggle WebSocket connection"""
        if self.connected:
            asyncio.create_task(self.disconnect_websocket())
        else:
            asyncio.create_task(self.connect_websocket())

    def emergency_stop_action(self):
        """Emergency stop action"""
        self.emergency_stop = True
        self.v_linear = 0.0
        self.v_angular = 0.0
        self.linear_scale.set(0.0)
        self.angular_scale.set(0.0)
        self.on_control_change()

    def init_gamepad(self):
        """Initialize gamepad"""
        if not GAMEPAD_AVAILABLE:
            messagebox.showerror("Gamepad Error", "Pygame not installed. Install with: pip install pygame")
            return
        
        try:
            pygame.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() > 0:
                self.gamepad = pygame.joystick.Joystick(0)
                self.gamepad.init()
                self.gamepad_connected = True
                self.update_gamepad_status()
                messagebox.showinfo("Gamepad", f"Connected to: {self.gamepad.get_name()}")
            else:
                messagebox.showwarning("Gamepad", "No gamepad found. Connect a gamepad and try again.")
                
        except Exception as e:
            messagebox.showerror("Gamepad Error", f"Failed to initialize gamepad: {e}")

    def run(self):
        """Run the application"""
        # Configure ttk styles for dark theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme colors
        bg_color = '#2e2e2e'
        fg_color = 'white'
        select_color = '#404040'
        
        style.configure('Dark.TFrame', background=bg_color)
        style.configure('Dark.TLabelframe', background=bg_color, foreground=fg_color)
        style.configure('Dark.TLabelframe.Label', background=bg_color, foreground=fg_color)
        style.configure('Dark.TLabel', background=bg_color, foreground=fg_color)
        style.configure('Dark.TButton', background=select_color, foreground=fg_color)
        
        # Update telemetry periodically
        def update_telemetry():
            if self.running:
                self.update_telemetry_display()
                self.root.after(100, update_telemetry)
        
        update_telemetry()
        
        # Start asyncio event loop
        def run_asyncio():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        # Run asyncio in separate thread
        self.asyncio_thread = threading.Thread(target=run_asyncio, daemon=True)
        self.asyncio_thread.start()
        
        # Schedule asyncio tasks
        def schedule_asyncio():
            try:
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(self.setup_background_tasks)
            except:
                self.root.after(100, schedule_asyncio)
        
        self.root.after(1000, schedule_asyncio)
        
        # Handle window close
        def on_closing():
            self.running = False
            if self.websocket:
                asyncio.run_coroutine_threadsafe(self.disconnect_websocket(), asyncio.get_event_loop())
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the GUI
        self.root.mainloop()

def main():
    """Main function"""
    print("🤖 Sanhum Robot Control App")
    print("All-in-one robot control with gamepad support")
    print()
    
    app = RobotControlApp()
    app.run()

if __name__ == "__main__":
    main()
