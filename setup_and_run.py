#!/usr/bin/env python3
"""
Sanhum RPi Setup and Run Automation Script
Automates the build and deployment of Sanhum robot control application on Raspberry Pi
"""

import os
import sys
import subprocess
import socket
import time
import signal
from pathlib import Path

class SanhumSetup:
    def __init__(self, project_path=None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.build_dir = self.project_path / "build"
        self.process = None
        
    def print_banner(self):
        """Print setup banner"""
        print("=" * 60)
        print("🤖 Sanhum RPi Setup and Run Automation")
        print("=" * 60)
        
    def get_ip_addresses(self):
        """Get all IP addresses including hotspot"""
        ips = []
        
        try:
            # Get hostname and local IPs
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            ips.append(f"Local: {local_ip}")
        except:
            pass
            
        # Check for common network interfaces
        interfaces = ['wlan0', 'eth0', 'lo', 'usb0', 'uap0']  # uap0 is common for hotspot
            
        for interface in interfaces:
            try:
                result = subprocess.run(['ip', 'addr', 'show', interface], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'inet ' in line and '127.0.0.1' not in line:
                            ip = line.split()[1].split('/')[0]
                            if interface == 'uap0' or interface == 'wlan0':
                                ips.append(f"🔥 Hotspot ({interface}): {ip}")
                            else:
                                ips.append(f"{interface}: {ip}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        return ips if ips else ["No network interfaces found"]
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("📋 Checking dependencies...")
        
        required_commands = ['qmake', 'make', 'python3']
        missing = []
        
        for cmd in required_commands:
            try:
                subprocess.run(['which', cmd], capture_output=True, check=True)
                print(f"✅ {cmd} found")
            except subprocess.CalledProcessError:
                missing.append(cmd)
                print(f"❌ {cmd} missing")
                
        if missing:
            print(f"\n📦 Installing missing dependencies: {', '.join(missing)}")
            try:
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 
                              'qt5-qmake', 'qtbase5-dev', 'qtbase5-dev-tools',
                              'build-essential', 'python3', 'python3-pip',
                              'libgpiod2', 'libgpiod-dev'], check=True)
                print("✅ Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                return False
                
        return True
        
    def build_project(self):
        """Build the Sanhum project"""
        print("\n🔨 Building Sanhum project...")
        
        # Create build directory
        self.build_dir.mkdir(exist_ok=True)
        os.chdir(self.build_dir)
        
        try:
            # Run qmake
            print("📝 Running qmake...")
            result = subprocess.run(['qmake', '../Sanhum.pro'], 
                                  capture_output=True, text=True, check=True)
            print("✅ qmake completed")
            
            # Run make
            print("⚙️ Running make...")
            result = subprocess.run(['make'], capture_output=True, text=True, check=True)
            print("✅ Build completed successfully")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
            
    def run_application(self):
        """Run the Sanhum application"""
        print("\n🚀 Starting Sanhum application...")
        
        executable = self.build_dir / "Sanhum"
        if not executable.exists():
            print(f"❌ Executable not found: {executable}")
            return False
            
        try:
            # Start the application
            self.process = subprocess.Popen([str(executable)], 
                                          cwd=self.build_dir,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          bufsize=1)
            
            print("✅ Sanhum application started!")
            print("📡 HTTP server should be available on port 8080")
            
            # Monitor output for a few seconds
            print("\n📊 Monitoring startup logs (10 seconds)...")
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.process.poll() is not None:
                    # Process has terminated
                    break
                    
                output = self.process.stdout.readline()
                if output:
                    print(f"[Sanhum] {output.strip()}")
                    
                time.sleep(0.1)
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to start application: {e}")
            return False
            
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n🛑 Shutting down...")
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        sys.exit(0)
        
    def run(self):
        """Main setup and run sequence"""
        self.print_banner()
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Print IP addresses
        print("\n🌐 Network Information:")
        ips = self.get_ip_addresses()
        for ip in ips:
            print(f"   {ip}")
            
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed. Exiting.")
            return False
            
        # Build project
        if not self.build_project():
            print("❌ Build failed. Exiting.")
            return False
            
        # Run application
        if not self.run_application():
            print("❌ Failed to start application. Exiting.")
            return False
            
        print("\n" + "=" * 60)
        print("🎉 Sanhum is running!")
        print("📱 Access the web interface at: http://<your-ip>:8080")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        # Keep the script running and monitor the process
        try:
            while True:
                if self.process and self.process.poll() is not None:
                    print(f"\n❌ Sanhum process terminated with exit code: {self.process.returncode}")
                    break
                    
                # Check for any new output
                if self.process:
                    output = self.process.stdout.readline()
                    if output:
                        print(f"[Sanhum] {output.strip()}")
                        
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
            
        return True

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        setup = SanhumSetup(project_path)
    else:
        setup = SanhumSetup()
        
    setup.run()

if __name__ == "__main__":
    main()
