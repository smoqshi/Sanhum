import { tank } from './robotState.js';

export function initNetwork() {
    const btn = document.getElementById('btnRefreshStatus');
    if (btn) {
        btn.addEventListener('click', () => {
            pollStatus();
        });
    }

    // Камеры: если поток MJPEG не грузится, показываем "no signal"
    const stereoImg = document.getElementById('stereoVideo');
    const stereoNoSig = document.getElementById('stereoNoSignal');
    if (stereoImg && stereoNoSig) {
        stereoImg.addEventListener('error', () => {
            stereoNoSig.style.display = 'block';
        });
        stereoImg.addEventListener('load', () => {
            stereoNoSig.style.display = 'none';
        });
    }

    const csiImg = document.getElementById('csiVideo');
    const csiNoSig = document.getElementById('csiNoSignal');
    if (csiImg && csiNoSig) {
        csiImg.addEventListener('error', () => {
            csiNoSig.style.display = 'block';
        });
        csiImg.addEventListener('load', () => {
            csiNoSig.style.display = 'none';
        });
    }
}

export async function pollStatus() {
    try {
        const r = await fetch('/api/status', { signal: AbortSignal.timeout(500) });
        if (!r.ok) return;
        const d = await r.json();

        const { cpu_temp_c, board_temp_c, cpu_load_percent,
                battery_v, current_total_a, current_5v_a, current_12v_a,
                current_motors_a, current_gpio_ma, wifi_ssid, wifi_rssi_dbm } = d;

        const cpuTemp = document.getElementById('statusCpuTemp');
        const boardTemp = document.getElementById('statusBoardTemp');
        const cpuLoad = document.getElementById('statusCpuLoad');
        const battery = document.getElementById('statusBattery');
        const currentTotal = document.getElementById('statusCurrentTotal');
        const current5V = document.getElementById('statusCurrent5V');
        const current12V = document.getElementById('statusCurrent12V');
        const currentMotors = document.getElementById('statusCurrentMotors');
        const currentGpio = document.getElementById('statusCurrentGpio');
        const wifiSsidEl = document.getElementById('statusWifiSsid');
        const wifiRssiEl = document.getElementById('statusWifiRssi');

        if (cpuTemp) cpuTemp.textContent = (cpu_temp_c !== undefined && cpu_temp_c !== null) ? `${cpu_temp_c.toFixed(1)} °C` : '-- °C';
        if (boardTemp) boardTemp.textContent = (board_temp_c !== undefined && board_temp_c !== null) ? `${board_temp_c.toFixed(1)} °C` : '-- °C';
        if (cpuLoad) cpuLoad.textContent = (cpu_load_percent !== undefined && cpu_load_percent !== null) ? `${cpu_load_percent.toFixed(1)} %` : '-- %';
        if (battery) battery.textContent = (battery_v !== undefined && battery_v !== null) ? `${battery_v.toFixed(1)} V` : '-- V';
        if (currentTotal) currentTotal.textContent = (current_total_a !== undefined && current_total_a !== null) ? `${current_total_a.toFixed(2)} A` : '-- A';
        if (current5V) current5V.textContent = (current_5v_a !== undefined && current_5v_a !== null) ? `${current_5v_a.toFixed(2)} A` : '-- A';
        if (current12V) current12V.textContent = (current_12v_a !== undefined && current_12v_a !== null) ? `${current_12v_a.toFixed(2)} A` : '-- A';
        if (currentMotors) currentMotors.textContent = (current_motors_a !== undefined && current_motors_a !== null) ? `${current_motors_a.toFixed(2)} A` : '-- A';
        if (currentGpio) currentGpio.textContent = (current_gpio_ma !== undefined && current_gpio_ma !== null) ? `${current_gpio_ma.toFixed(0)} mA` : '-- mA';
        if (wifiSsidEl) wifiSsidEl.textContent = (wifi_ssid !== undefined && wifi_ssid !== null) ? wifi_ssid : '--';
        if (wifiRssiEl) wifiRssiEl.textContent = (wifi_rssi_dbm !== undefined && wifi_rssi_dbm !== null) ? `${wifi_rssi_dbm} dBm` : '-- dBm';
    } catch (e) {
        console.error('pollStatus error', e);
    }
}

// Rate limiting to prevent overwhelming the server
let lastBaseCommandTime = 0;
let lastArmCommandTime = 0;
const COMMAND_RATE_LIMIT = 200; // ms between commands (5 commands/sec max)

// Previous command values to avoid sending duplicates
let lastBaseCommand = { vLinear: 0, vAngular: 0 };
let lastArmCommand = { extend: 0, gripper: 0, turretAngle: 0 };

// Connection status tracking - completely disabled until server is confirmed
let connectionStatus = 'disabled'; // Start as completely disabled
let lastConnectionCheck = 0;
const CONNECTION_CHECK_INTERVAL = 5000; // Check connection every 5 seconds
let consecutiveFailures = 0;
const MAX_CONSECUTIVE_FAILURES = 3;

// Manual connection test - user must enable this
let manualConnectionTest = false;

// Test server connection
async function checkConnection() {
    if (!manualConnectionTest) {
        return 'disabled';
    }
    
    const now = Date.now();
    if (now - lastConnectionCheck < CONNECTION_CHECK_INTERVAL) {
        return connectionStatus;
    }
    lastConnectionCheck = now;

    try {
        const response = await fetch('/api/status', {
            method: 'GET',
            signal: AbortSignal.timeout(500) // Shorter timeout
        });
        
        if (response.ok) {
            if (connectionStatus !== 'connected') {
                console.log('WEB: Server connection established');
                consecutiveFailures = 0;
            }
            connectionStatus = 'connected';
        } else {
            consecutiveFailures++;
            connectionStatus = 'disconnected';
        }
    } catch (e) {
        consecutiveFailures++;
        if (consecutiveFailures === 1) {
            console.log('WEB: Server connection lost -', e.message);
        }
        connectionStatus = 'disconnected';
    }
    
    return connectionStatus;
}

// Manual function to enable connection testing
export function enableConnectionTest() {
    console.log('WEB: Connection testing enabled - checking for server...');
    manualConnectionTest = true;
    connectionStatus = 'unknown';
}

// Export connection status for UI controls
export function getConnectionStatus() {
    return connectionStatus;
}

export async function sendBaseCommand(vLinear, vAngular, emergency = false) {
    const now = Date.now();
    if (now - lastBaseCommandTime < COMMAND_RATE_LIMIT && !emergency) {
        return; // Skip this command due to rate limiting
    }

    // Skip duplicate commands (except emergency)
    if (!emergency && 
        Math.abs(vLinear - lastBaseCommand.vLinear) < 0.01 && 
        Math.abs(vAngular - lastBaseCommand.vAngular) < 0.01) {
        return;
    }

    // Skip zero commands unless it's a change from non-zero
    if (!emergency && 
        Math.abs(vLinear) < 0.01 && Math.abs(vAngular) < 0.01 &&
        Math.abs(lastBaseCommand.vLinear) < 0.01 && Math.abs(lastBaseCommand.vAngular) < 0.01) {
        return;
    }

    lastBaseCommandTime = now;
    lastBaseCommand = { vLinear, vAngular };

    // Skip all commands if connection is disabled
    if (connectionStatus === 'disabled') {
        return;
    }

    // Skip non-emergency commands if we've had too many failures
    if (!emergency && consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
        return;
    }

    // Only check connection if we're not already sure it's disconnected
    if (!emergency && connectionStatus !== 'disconnected') {
        const status = await checkConnection();
        if (status === 'disconnected' || status === 'disabled') {
            return; // Skip command if server is not available
        }
    }

    try {
        const payload = emergency ? { emergency: true } : { vLinear, vAngular };
        
        const response = await fetch('/api/base', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: AbortSignal.timeout(800) // Shorter timeout
        });
        
        if (!response.ok) {
            consecutiveFailures++;
            connectionStatus = 'disconnected';
            return;
        }
        
        // Success - reset failure counter and confirm connection
        consecutiveFailures = 0;
        connectionStatus = 'connected';
        
    } catch (e) {
        consecutiveFailures++;
        connectionStatus = 'disconnected';
        
        // Don't log every single error to reduce console spam
        if (consecutiveFailures === 1 || consecutiveFailures % 10 === 0) {
            console.log('WEB: Connection issues detected, pausing commands...');
        }
        return;
    }
}

export async function sendArmCommand(extend, gripper, turretAngle) {
    const now = Date.now();
    if (now - lastArmCommandTime < COMMAND_RATE_LIMIT) {
        return; // Skip this command due to rate limiting
    }

    // Skip duplicate commands
    if (Math.abs(extend - lastArmCommand.extend) < 0.01 && 
        Math.abs(gripper - lastArmCommand.gripper) < 0.01 && 
        Math.abs(turretAngle - lastArmCommand.turretAngle) < 0.01) {
        return;
    }

    lastArmCommandTime = now;
    lastArmCommand = { extend, gripper, turretAngle };

    // Skip all commands if connection is disabled
    if (connectionStatus === 'disabled') {
        return;
    }

    // Skip commands if we've had too many failures
    if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
        return;
    }

    // Only check connection if we're not already sure it's disconnected
    if (connectionStatus !== 'disconnected') {
        const status = await checkConnection();
        if (status === 'disconnected' || status === 'disabled') {
            return; // Skip command if server is not available
        }
    }

    try {
        const response = await fetch('/api/arm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ extend, gripper, turretAngle }),
            signal: AbortSignal.timeout(800) // Shorter timeout
        });
        
        if (!response.ok) {
            consecutiveFailures++;
            connectionStatus = 'disconnected';
            return;
        }
        
        // Success - reset failure counter and confirm connection
        consecutiveFailures = 0;
        connectionStatus = 'connected';
        
    } catch (e) {
        consecutiveFailures++;
        connectionStatus = 'disconnected';
        return;
    }
}

export async function pollJointState() {
    // Skip all polling if connection is disabled
    if (connectionStatus === 'disabled') {
        return;
    }
    
    try {
        const r = await fetch('/api/joint_state', { signal: AbortSignal.timeout(500) });
        if (!r.ok) return;
        const d = await r.json();

        if (d.arm) {
            const { turret_deg, arm_ext, gripper } = d.arm;
            const turretEl = document.getElementById('lblTurret');
            const armEl = document.getElementById('lblArm');
            const gripEl = document.getElementById('lblGripper');

            if (turretEl) turretEl.textContent = `${turret_deg.toFixed(1)} °`;
            if (armEl) armEl.textContent = `${(arm_ext * 100).toFixed(1)} %`;
            if (gripEl) gripEl.textContent = `${(gripper * 100).toFixed(1)} %`;
        }
    } catch (e) {
        console.error('pollJointState error', e);
    }
}
