import { initNetwork, pollStatus, pollJointState, getConnectionStatus } from './network.js';
import { initChassis, drawChassis, updateBase } from './chassis.js';
import { initManipulator, drawManipulator } from './manipulator.js';
import { initUI, updateControls, updateDashboardFromState, initConnectionControls } from './uiControls.js';

let canvas, ctx;
let lastTime = 0;
let statusInterval, jointInterval;

function init() {
    canvas = document.getElementById('tankCanvas');
    if (!canvas) {
        console.error('Canvas with id "tankCanvas" not found');
        return;
    }
    ctx = canvas.getContext('2d');

    initChassis(canvas);
    initManipulator();
    initNetwork();
    initUI();
    initConnectionControls();

    requestAnimationFrame(loop);

    // периодический опрос статуса и суставов
    statusInterval = setInterval(() => {
        if (getConnectionStatus() !== 'disabled') {
            pollStatus();
        }
    }, 500);
    
    jointInterval = setInterval(() => {
        if (getConnectionStatus() !== 'disabled') {
            pollJointState();
        }
    }, 200);
}

function loop(timestamp) {
    const dt = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    updateControls(dt);        // обновление команд оператора
    updateBase(dt);            // интеграция движения базы

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawChassis(ctx);          // отрисовка корпуса
    drawManipulator(ctx);      // отрисовка манипулятора

    updateDashboardFromState(); // обновление правого блока

    requestAnimationFrame(loop);
}

window.addEventListener('load', init);
