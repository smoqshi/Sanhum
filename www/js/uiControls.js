import { tank } from './robotState.js';

import { sendBaseCommand, sendArmCommand } from './network.js';



let vLinearSlider, vAngularSlider, turretSlider, armSlider, gripperSlider;

let lblVLinear, lblVAngular, lblTurret, lblArm, lblGripper;

let gamepadStatusLabel;



let gamepadIndex = null;



export function initUI() {

    vLinearSlider   = document.getElementById('vLinear');

    vAngularSlider  = document.getElementById('vAngular');

    turretSlider    = document.getElementById('turretAngle');

    armSlider       = document.getElementById('armExtend');

    gripperSlider   = document.getElementById('gripper');



    const vLinearValue  = document.getElementById('vLinearValue');

    const vAngularValue = document.getElementById('vAngularValue');

    const turretValue   = document.getElementById('turretAngleValue');

    const armValue      = document.getElementById('armExtendValue');

    const gripperValue  = document.getElementById('gripperValue');



    lblVLinear  = document.getElementById('lblVLinear');

    lblVAngular = document.getElementById('lblVAngular');

    lblTurret   = document.getElementById('lblTurret');

    lblArm      = document.getElementById('lblArm');

    lblGripper  = document.getElementById('lblGripper');



    gamepadStatusLabel = document.getElementById('gamepadStatus');



    if (vLinearSlider && vLinearValue) {

        vLinearSlider.addEventListener('input', () => {

            const v = parseFloat(vLinearSlider.value) || 0;

            tank.vLinearCmd = v;

            vLinearValue.textContent = v.toFixed(2);

            sendBase();

        });

    }

    if (vAngularSlider && vAngularValue) {

        vAngularSlider.addEventListener('input', () => {

            const v = parseFloat(vAngularSlider.value) || 0;

            tank.vAngularCmdDeg = v;

            vAngularValue.textContent = v.toFixed(0);

            sendBase();

        });

    }

    if (turretSlider && turretValue) {

        turretSlider.addEventListener('input', () => {

            const v = parseFloat(turretSlider.value) || 0;

            tank.turretAngle = v;

            turretValue.textContent = v.toFixed(0);

            sendArm();

        });

    }

    if (armSlider && armValue) {

        armSlider.addEventListener('input', () => {

            const v = parseFloat(armSlider.value) || 0;

            tank.armExtension = v / 100.0;

            armValue.textContent = v.toFixed(0);

            sendArm();

        });

    }

    if (gripperSlider && gripperValue) {

        gripperSlider.addEventListener('input', () => {

            const v = parseFloat(gripperSlider.value) || 0;

            tank.gripper = v / 100.0;

            gripperValue.textContent = v.toFixed(0);

            sendArm();

        });

    }



    wireControlButtons();

    initGamepadEvents();

}



// вызывается из main.js каждый кадр

export function updateControls(dt) {

    pollGamepad(dt);

}



function wireControlButtons() {

    const buttons = Array.from(document.querySelectorAll('.controls-column button'));

    buttons.forEach(btn => {

        const text = btn.textContent || '';

        const label = text.toLowerCase();



        if (label.includes('forward')) {

            btn.addEventListener('click', () => {

                tank.vLinearCmd = +0.5;

                tank.vAngularCmdDeg = 0;

                sendBase();

            });

        } else if (label.includes('back')) {

            btn.addEventListener('click', () => {

                tank.vLinearCmd = -0.5;

                tank.vAngularCmdDeg = 0;

                sendBase();

            });

        } else if (label.includes('rotate left')) {

            btn.addEventListener('click', () => {

                tank.vLinearCmd = 0;

                tank.vAngularCmdDeg = +30;

                sendBase();

            });

        } else if (label.includes('rotate right')) {

            btn.addEventListener('click', () => {

                tank.vLinearCmd = 0;

                tank.vAngularCmdDeg = -30;

                sendBase();

            });

        } else if (label.includes('stop')) {

            btn.addEventListener('click', () => {

                tank.vLinearCmd = 0;

                tank.vAngularCmdDeg = 0;

                sendBase(true);

            });

        } else if (label.includes('turret left')) {

            btn.addEventListener('click', () => {

                tank.turretAngle -= 5;

                sendArm();

            });

        } else if (label.includes('turret right')) {

            btn.addEventListener('click', () => {

                tank.turretAngle += 5;

                sendArm();

            });

        } else if (label.includes('arm extend')) {

            btn.addEventListener('click', () => {

                tank.armExtension = clamp01(tank.armExtension + 0.05);

                sendArm();

            });

        } else if (label.includes('arm retract')) {

            btn.addEventListener('click', () => {

                tank.armExtension = clamp01(tank.armExtension - 0.05);

                sendArm();

            });

        } else if (label.includes('gripper close')) {

            btn.addEventListener('click', () => {

                tank.gripper = clamp01(tank.gripper + 0.1);

                sendArm();

            });

        } else if (label.includes('gripper open')) {

            btn.addEventListener('click', () => {

                tank.gripper = clamp01(tank.gripper - 0.1);

                sendArm();

            });

        }

    });



    const resetBtn = document.getElementById('btnResetPose');

    if (resetBtn) {

        resetBtn.addEventListener('click', () => {

            tank.resetPose();

            sendBase(true);

            sendArm();

        });

    }

}



function sendBase(emergency = false) {
    const vLin = tank.vLinearCmd;
    const vAng = tank.vAngularCmdDeg * Math.PI / 180.0;
    
    // Only use UDP - no HTTP fallback to prevent ERR_INSUFFICIENT_RESOURCES
    if (isUdpConnected()) {
        sendUdpCommand(vLin, vAng, emergency);
    }
    // If UDP is not connected, don't send anything to prevent errors
}


function sendArm() {
    const extend = tank.armExtension;
    const grip = tank.gripper;
    const turret = tank.turretAngle;
    
    // Only use UDP - no HTTP fallback to prevent ERR_INSUFFICIENT_RESOURCES
    if (isUdpConnected()) {
        sendUdpArmCommand(extend, grip, turret);
    }
    // If UDP is not connected, don't send anything to prevent errors
}


export function updateDashboardFromState() {

    if (lblVLinear) {

        lblVLinear.textContent = `${tank.vLinear.toFixed(2)} m/s`;

    }

    if (lblVAngular) {

        lblVAngular.textContent = `${tank.vAngular.toFixed(1)} °/s`;

    }

    if (lblTurret) {

        lblTurret.textContent = `${tank.turretAngle.toFixed(1)} °`;

    }

    if (lblArm) {

        lblArm.textContent = `${(tank.armExtension * 100).toFixed(1)} %`;

    }

    if (lblGripper) {

        lblGripper.textContent = `${(tank.gripper * 100).toFixed(1)} %`;

    }



    if (turretSlider) {

        turretSlider.value = tank.turretAngle.toFixed(0);

    }

    if (armSlider) {

        armSlider.value = (tank.armExtension * 100).toFixed(0);

    }

    if (gripperSlider) {

        gripperSlider.value = (tank.gripper * 100).toFixed(0);

    }



    if (gamepadStatusLabel) {

        gamepadStatusLabel.textContent = tank.gamepadConnected

            ? 'Gamepad: connected'

            : 'Gamepad: not connected';

    }

}



/* ---------- Gamepad API ---------- */



function initGamepadEvents() {

    window.addEventListener('gamepadconnected', (e) => {

        const gp = e.gamepad;

        gamepadIndex = gp.index;

        tank.gamepadConnected = true;

        if (gamepadStatusLabel) {

            gamepadStatusLabel.textContent = 'Gamepad: connected';

        }

    });



    window.addEventListener('gamepaddisconnected', (e) => {

        if (gamepadIndex === e.gamepad.index) {

            gamepadIndex = null;

            tank.gamepadConnected = false;

            if (gamepadStatusLabel) {

                gamepadStatusLabel.textContent = 'Gamepad: not connected';

            }

        }

    });

}



function pollGamepad(dt) {

    const gps = navigator.getGamepads ? navigator.getGamepads() : [];

    const gp = (gps && gamepadIndex !== null) ? gps[gamepadIndex] : null;



    if (!gp) {

        tank.gamepadConnected = false;

        return;

    }



    tank.gamepadConnected = true;



    const lx = gp.axes[0] || 0;

    const ly = gp.axes[1] || 0;

    const rx = gp.axes[2] || 0;

    const ry = gp.axes[3] || 0;

    const lt = gp.buttons[6] ? gp.buttons[6].value : 0;

    const rt = gp.buttons[7] ? gp.buttons[7].value : 0;



    // Apply deadzone and scale properly

    const dead = 0.15; // Reduced deadzone for better sensitivity

    const maxLinearSpeed = 1.4; // Max 1.4 m/s (based on 333 rpm motor, 40mm wheel)

    const maxAngularSpeed = 30.0; // Max 30 deg/s

    

    // Helper function to apply deadzone and scale

    function applyDeadzoneAndScale(value, deadzone, maxOutput) {

        if (Math.abs(value) < deadzone) {

            return 0;

        }

        // Scale from [deadzone, 1] to [0, maxOutput]

        const sign = value > 0 ? 1 : -1;

        const normalizedValue = (Math.abs(value) - deadzone) / (1.0 - deadzone);

        return sign * normalizedValue * maxOutput;

    }

    

    const ax = applyDeadzoneAndScale(lx, dead, maxAngularSpeed);

    const ay = applyDeadzoneAndScale(ly, dead, maxLinearSpeed);

    const axR = applyDeadzoneAndScale(rx, dead, 25.0); // turret speed

    const ayR = applyDeadzoneAndScale(ry, dead, 0.25); // arm speed



    // база: LS

    tank.vLinearCmd = -ay; // Invert Y axis (forward is negative on most gamepads)

    tank.vAngularCmdDeg = ax;



    // манипулятор - use already scaled values

    tank.turretAngle += axR * dt; // axR already includes speed scaling

    tank.armExtension = clamp01(

        tank.armExtension - ayR * dt // ayR already includes speed scaling

    );

    const gripDelta = (rt - lt) * 0.4 * dt; // Keep trigger scaling

    tank.gripper = clamp01(tank.gripper + gripDelta);



    // всегда отправляем команды роботу

    sendBase();

    sendArm();

}



function clamp01(x) {

    if (x < 0) return 0;

    if (x > 1) return 1;

    return x;

}



// Connection control functionality

export function initConnectionControls() {

    // Connection control buttons

    const btnStartConnection = document.getElementById('btnStartConnection');

    const btnResetOutput = document.getElementById('btnResetOutput');

    const btnRefreshStatus = document.getElementById('btnRefreshStatus');

    

    if (btnStartConnection) {

        btnStartConnection.addEventListener('click', () => {

            import('./network.js').then(module => {

                module.enableConnectionTest();

                btnStartConnection.textContent = 'Connecting...';

                btnStartConnection.style.background = '#15803d';

                btnStartConnection.style.borderColor = '#15803d';

                

                // Update button text when connection is established

                setTimeout(() => {

                    btnStartConnection.textContent = 'Connection Active';

                }, 2000);

            });

        });

    }

    

    if (btnResetOutput) {

        btnResetOutput.addEventListener('click', () => {

            // Reset all output values to 0

            document.getElementById('lblVLinear').textContent = '0.00 m/s';

            document.getElementById('lblVAngular').textContent = '0.0 °/s';

            document.getElementById('lblTurret').textContent = '0.0 °';

            document.getElementById('lblArm').textContent = '0.0 %';

            document.getElementById('lblGripper').textContent = '0.0 %';

            

            // Reset sliders

            document.getElementById('vLinear').value = 0;

            document.getElementById('vAngular').value = 0;

            document.getElementById('turretAngle').value = 0;

            document.getElementById('armExtend').value = 0;

            document.getElementById('gripper').value = 0;

            

            // Update slider value displays

            document.getElementById('vLinearValue').textContent = '0.00';

            document.getElementById('vAngularValue').textContent = '0';

            document.getElementById('turretAngleValue').textContent = '0';

            document.getElementById('armExtendValue').textContent = '0';

            document.getElementById('gripperValue').textContent = '0';

            

            // Reset tank state

            tank.resetPose();

            

            // Visual feedback

            btnResetOutput.style.background = '#dc2626';

            btnResetOutput.style.borderColor = '#dc2626';

            setTimeout(() => {

                btnResetOutput.style.background = '#111827';

                btnResetOutput.style.borderColor = '#374151';

            }, 500);

        });

    }

    

    if (btnRefreshStatus) {

        btnRefreshStatus.addEventListener('click', () => {

            pollStatus();

        });

    }

}







