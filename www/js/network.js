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
    // HTTP polling completely disabled - use WebSocket only
    console.warn('HTTP pollStatus disabled - use WebSocket instead');
    return;
}

// Rate limiting to prevent overwhelming server
let lastBaseCommandTime = 0;
let lastArmCommandTime = 0;
const COMMAND_RATE_LIMIT = 200; // ms between commands (5 commands/sec max)

// Previous command values to avoid sending duplicates
let lastBaseCommand = { vLinear: 0, vAngular: 0 };
let lastArmCommand = { extend: 0, gripper: 0, turretAngle: 0 };

// Request queue management
let pendingRequests = new Set();
const MAX_PENDING_REQUESTS = 3;

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
    // HTTP commands completely disabled - use WebSocket only
    console.warn('HTTP sendArmCommand disabled - use WebSocket instead');
    return;
}

export async function pollJointState() {
    // HTTP polling completely disabled - use WebSocket only
    console.warn('HTTP pollJointState disabled - use WebSocket instead');
    return;
}
