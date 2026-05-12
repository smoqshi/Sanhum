// UDP Network Communication for real-time control
// Reduces delays compared to HTTP requests

let udpSocket = null;
let udpServerPort = 8081; // Different from HTTP port 8080
let udpServerHost = '192.168.0.140'; // RPi IP

// UDP connection state
let udpConnected = false;
let lastUdpSend = 0;
const UDP_SEND_RATE = 50; // 20Hz command rate (50ms)

// Speed info from RPi via UDP
let lastSpeedInfo = {
    leftSpeed: 0,
    rightSpeed: 0,
    batteryV: 12.0,
    timestamp: Date.now()
};

export function initUdpNetwork() {
    try {
        // Create UDP socket for commands
        udpSocket = new WebSocket(`ws://${udpServerHost}:${udpServerPort + 1}`);
        
        udpSocket.onopen = () => {
            console.log('UDP WebSocket connected');
            udpConnected = true;
        };
        
        udpSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'speed_info') {
                    lastSpeedInfo = {
                        leftSpeed: data.leftSpeed || 0,
                        rightSpeed: data.rightSpeed || 0,
                        batteryV: data.batteryV || 12.0,
                        timestamp: Date.now()
                    };
                    updateSpeedDisplay();
                }
            } catch (e) {
                console.error('UDP message parse error:', e);
            }
        };
        
        udpSocket.onerror = (error) => {
            console.error('UDP WebSocket error:', error);
            udpConnected = false;
        };
        
        udpSocket.onclose = () => {
            console.log('UDP WebSocket disconnected');
            udpConnected = false;
        };
        
    } catch (e) {
        console.error('Failed to initialize UDP network:', e);
    }
}

export function sendUdpCommand(vLinear, vAngular, emergency = false) {
    if (!udpConnected || !udpSocket) {
        return false;
    }
    
    const now = Date.now();
    if (now - lastUdpSend < UDP_SEND_RATE && !emergency) {
        return true; // Rate limited but successful
    }
    
    lastUdpSend = now;
    
    try {
        const command = {
            type: 'motor_command',
            vLinear: vLinear,
            vAngular: vAngular,
            emergency: emergency || false,
            timestamp: now
        };
        
        udpSocket.send(JSON.stringify(command));
        return true;
    } catch (e) {
        console.error('UDP send error:', e);
        return false;
    }
}

export function sendUdpArmCommand(extend, gripper, turretAngle) {
    if (!udpConnected || !udpSocket) {
        return false;
    }
    
    try {
        const command = {
            type: 'arm_command',
            extend: extend,
            gripper: gripper,
            turretAngle: turretAngle,
            timestamp: Date.now()
        };
        
        udpSocket.send(JSON.stringify(command));
        return true;
    } catch (e) {
        console.error('UDP arm send error:', e);
        return false;
    }
}

export function getUdpSpeedInfo() {
    return lastSpeedInfo;
}

export function isUdpConnected() {
    return udpConnected;
}

function updateSpeedDisplay() {
    const leftSpeedEl = document.getElementById('statusLeftSpeed');
    const rightSpeedEl = document.getElementById('statusRightSpeed');
    const batteryEl = document.getElementById('statusBattery');
    
    if (leftSpeedEl) {
        leftSpeedEl.textContent = `${lastSpeedInfo.leftSpeed.toFixed(2)} m/s`;
    }
    if (rightSpeedEl) {
        rightSpeedEl.textContent = `${lastSpeedInfo.rightSpeed.toFixed(2)} m/s`;
    }
    if (batteryEl) {
        batteryEl.textContent = `${lastSpeedInfo.batteryV.toFixed(1)} V`;
    }
}

export function closeUdpNetwork() {
    if (udpSocket) {
        udpSocket.close();
        udpSocket = null;
        udpConnected = false;
    }
}
