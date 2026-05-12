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

// Test server connection - completely disabled
async function checkConnection() {
    // HTTP connection testing completely disabled
    return 'disabled';
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
    // HTTP commands completely disabled - use WebSocket only
    console.warn('HTTP sendBaseCommand disabled - use WebSocket instead');
    return;
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
