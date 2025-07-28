// === СТЕК ТЕКСТОВЫХ СООБЩЕНИЙ ===
// let textOverlayQueue = [];

// function showTextOverlay(text, duration) {
//     // Добавляем новое сообщение в очередь, если оно не пустое
//     if (text && text.trim()) {
//         textOverlayQueue.push({ text, timestamp: Date.now() });
//     }
//     // Оставляем только последние 2 сообщения
//     if (textOverlayQueue.length > 2) {
//         textOverlayQueue.shift();
//     }
//
//     // Рендерим все сообщения
//     let overlay = document.getElementById('text-overlay-multi');
//     if (!overlay) {
//         overlay = document.createElement('div');
//         overlay.id = 'text-overlay-multi';
//         overlay.style.cssText = `
//             position: fixed;
//             bottom: 25vh;
//             left: 50%;
//             transform: translateX(-50%);
//             z-index: 1000;
//             display: flex;
//             flex-direction: column;
//             align-items: center;
//             pointer-events: none;
//         `;
//         document.body.appendChild(overlay);
//     }
//
//     // Очищаем overlay
//     overlay.innerHTML = '';
//     textOverlayQueue.forEach((msg, idx) => {
//         const div = document.createElement('div');
//         div.textContent = msg.text;
//         div.style.cssText = `
//             background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(102, 126, 234, 0.9) 100%);
//             color: white;
//             padding: 1.2rem 2rem;
//             border-radius: 12px;
//             font-size: 1.5em;
//             font-weight: 600;
//             margin-bottom: 10px;
//             opacity: 1;
//             transition: opacity 0.5s;
//             max-width: 80vw;
//             text-align: center;
//             box-shadow: 0 8px 32px rgba(0,0,0,0.6);
//         `;
//         overlay.appendChild(div);
//
//         // Fade out самое старое сообщение через duration
//         if (idx === 0 && textOverlayQueue.length === 2) {
//             setTimeout(() => {
//                 div.style.opacity = '0';
//                 setTimeout(() => {
//                     if (overlay.contains(div)) overlay.removeChild(div);
//                 }, 500);
//             }, duration);
//         }
//     });
//
//     // Удаляем самое старое сообщение из очереди после duration
//     if (textOverlayQueue.length === 2) {
//         setTimeout(() => {
//             if (textOverlayQueue.length > 0) {
//                 textOverlayQueue.shift();
//                 // Перерисовать overlay
//                 showTextOverlay('', 0);
//             }
//         }, duration);
//     }
// }

// WebSocket интеграция для VRM с ассистентом
window.vrmTimingHistory = window.vrmTimingHistory || [];
function logVrmTiming(type, received, applied) {
    window.vrmTimingHistory.push({
        type,
        received,
        applied,
        delay: applied - received
    });
    if (window.vrmTimingHistory.length > 10) window.vrmTimingHistory.shift();
}

class VRMWebSocketClient {
    constructor(vrmApp) {
        this.vrmApp = vrmApp;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.isConnected = false;
        this.hasSentInitialMessage = false;
        this.lastPingTime = 0;
        this.pingInterval = null;
        
        // Настройки подключения
        this.wsHost = '192.168.1.4'; // Измените на ваш IP
        this.wsPort = 31992; // Порт WebSocket ассистента
        this.textWsPort = 31993; // Порт для текстового overlay
        
        // Настройки текстового оверлея
        this.textOverlayConfig = {
            defaultDuration: 12000, // 12 секунд по умолчанию
            minDuration: 3000,      // Минимум 3 секунды
            maxDuration: 30000,     // Максимум 30 секунд
            fadeInTime: 300,        // Время появления
            fadeOutTime: 500        // Время исчезновения
        };
        
        this.init();
    }
    
    init() {
        this.connect();
        this.setupEventListeners();
    }
    
    connect() {
        try {
            const wsUrl = `ws://${this.wsHost}:${this.wsPort}`;
            console.log(`🔌 Подключение к WebSocket: ${wsUrl}`);
            console.log(`🔌 Хост: ${this.wsHost}, Порт: ${this.wsPort}`);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket подключен к ассистенту');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateStatus('connected');
                
                // Отправляем идентификатор VRM клиента только при первом подключении
                if (!this.hasSentInitialMessage) {
                    this.sendMessage({
                        type: 'vrm_client',
                        client: 'vrm_overlay',
                        version: '1.0',
                        reconnect: false
                    });
                    this.hasSentInitialMessage = true;
                } else {
                                    // При переподключении отправляем сообщение о реконнекте
                this.sendMessage({
                    type: 'vrm_client',
                    client: 'vrm_overlay',
                    version: '1.0',
                    reconnect: true
                });
                
                // Запускаем периодическую проверку соединения
                this.startPingInterval();
            }
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onclose = (event) => {
                console.log(`❌ WebSocket соединение закрыто. Код: ${event.code}, Причина: ${event.reason}`);
                this.isConnected = false;
                this.stopPingInterval();
                this.updateStatus('disconnected');
                
                // Не переподключаемся при нормальном закрытии (код 1000)
                if (event.code !== 1000) {
                this.scheduleReconnect();
                } else {
                    console.log('✅ WebSocket закрыт нормально, переподключение не требуется');
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket ошибка:', error);
                this.updateStatus('error');
                
                // В режиме OBS не показываем ошибки пользователю
                if (!window.IS_OBS_MODE) {
                    console.warn('⚠️ WebSocket не подключен. Ассистент может быть не запущен.');
                }
            };
            
        } catch (error) {
            console.error('❌ Ошибка создания WebSocket:', error);
            this.scheduleReconnect();
        }
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            console.log('📨 Получено сообщение от ассистента:', message);
            const received = performance.now();
            switch (message.type) {
                case 'emotion':
                    this.handleEmotion(message, received);
                    break;
                case 'animation':
                    this.handleAnimation(message, received);
                    break;
//                case 'text':
//                    this.handleText(message);
//                    break;
                case 'status':
                    this.handleStatus(message, received);
                    break;
                case 'speech':
                    this.handleSpeech(message, received);
                    break;
                case 'lipsync':
                    this.handleLipsyncMessage(message, received);
                    break;
                case 'camera_control':
                    this.handleCameraControl(message, received);
                    break;
                case 'pose_control':
                    this.handlePoseControl(message, received);
                    break;
                case 'light_control':
                    this.handleLightControl(message, received);
                    break;
                case 'pong':
                    // Ответ на ping
                    const pingTime = Date.now() - this.lastPingTime;
                    console.log(`🏓 Получен pong, время отклика: ${pingTime}ms`);
                    break;
                case 'client_ack':
                    // Ассистент подтвердил подключение клиента
                    console.log('✅ Ассистент подтвердил подключение VRM клиента');
                    break;
                default:
                    console.log('❓ Неизвестный тип сообщения:', message.type);
            }
        } catch (error) {
            console.error('❌ Ошибка обработки сообщения:', error);
        }
    }
    
    handleEmotion(message, received) {
        const { emotion, intensity = 1.0, duration = 2000, priority = 5 } = message;
        console.log(`😊 Применяем эмоцию: ${emotion} (интенсивность: ${intensity}, приоритет: ${priority})`);
        const applied = performance.now();
        logVrmTiming('emotion', received, applied);
        
        if (this.vrmApp) {
            try {
                // Используем новую систему blend shapes
                if (this.vrmApp.blendShapeManager) {
                    this.vrmApp.blendShapeManager.applyEmotion(emotion, intensity, priority);
                } else if (this.vrmApp.applyEmotion) {
                    // Fallback к старой системе
                    this.vrmApp.applyEmotion(emotion);
                }
            } catch (error) {
                console.error('❌ Ошибка применения эмоции:', error);
                // Fallback к старой системе
                if (this.vrmApp.applyEmotion) {
            this.vrmApp.applyEmotion(emotion);
                }
            }
        }
        
        // Автоматически сбрасываем эмоцию через указанное время
        if (duration > 0) {
            setTimeout(() => {
                if (this.vrmApp) {
                    try {
                        if (this.vrmApp.blendShapeManager) {
                            this.vrmApp.blendShapeManager.resetEmotions();
                        } else if (this.vrmApp.resetEmotions) {
                    this.vrmApp.resetEmotions();
                        }
                    } catch (error) {
                        console.error('❌ Ошибка сброса эмоций:', error);
                    }
                }
            }, duration);
        }
    }
    
    handleAnimation(message, received) {
        const { animation, duration = 5000 } = message;
        console.log(`🎭 Воспроизводим анимацию: ${animation}`);
        const applied = performance.now();
        logVrmTiming('animation', received, applied);
        
        // Воспроизводим анимацию
        if (this.vrmApp && this.vrmApp.playMovement) {
            this.vrmApp.playMovement(animation);
        }
        
        // Автоматически возвращаемся к idle через указанное время
        if (duration > 0) {
            setTimeout(() => {
                if (this.vrmApp && this.vrmApp.playMovement) {
                    this.vrmApp.playMovement('idle');
                }
            }, duration);
        }
    }
    
//    handleText(message) {
//        const { text, duration } = message;
//        const finalDuration = this.validateDuration(duration || this.textOverlayConfig.defaultDuration);
//        console.log(`💬 Отображаем текст: ${text} (${finalDuration}ms)`);
//        showTextOverlay(text, finalDuration);
//    }
    
    handleStatus(message, received) {
        const { status } = message;
        console.log(`📊 Статус ассистента: ${status}`);
        const applied = performance.now();
        logVrmTiming('status', received, applied);
        
        if (this.vrmApp) {
            // Используем новую систему state machine
            if (this.vrmApp.stateMachine) {
                try {
                    this.vrmApp.stateMachine.transitionTo(status);
                } catch (error) {
                    console.error('❌ Ошибка в state machine:', error);
                    // Fallback к старой системе
                    this.handleStatusFallback(status);
                }
            } else {
                // Fallback к старой системе
                this.handleStatusFallback(status);
            }
        }
    }
    
    handleStatusFallback(status) {
        if (!this.vrmApp || !this.vrmApp.playMovement) return;
        
        switch (status) {
            case 'idle':
                    this.vrmApp.playMovement('idle');
                break;
            case 'talking':
                    this.vrmApp.playMovement('talking');
                break;
            case 'thinking':
                    this.vrmApp.playMovement('thinking_move');
                break;
            case 'waiting':
                    this.vrmApp.playMovement('idle');
                break;
            default:
                console.log(`⚠️ Неизвестный статус: ${status}`);
        }
    }
    
    handleSpeech(message, received) {
        const { isSpeaking, text } = message;
        console.log(`🗣️ Речь: ${isSpeaking ? 'началась' : 'закончилась'} - ${text}`);
        const applied = performance.now();
        logVrmTiming('speech', received, applied);
        
        if (isSpeaking) {
            // Начинаем анимацию речи
            if (this.vrmApp && this.vrmApp.playMovement) {
                this.vrmApp.playMovement('talking');
            }
            
            // Показываем текст речи
            if (text) {
                const duration = this.textOverlayConfig.defaultDuration;
                this.showTextOverlay(text, duration);
            }
        } else {
            // Заканчиваем анимацию речи
            if (this.vrmApp && this.vrmApp.playMovement) {
                this.vrmApp.playMovement('idle');
            }
        }
    }
    
    handleLipsyncMessage(message, received) {
        if (!this.vrmApp) return;
        
        const applied = performance.now();
        logVrmTiming('lipsync', received, applied);
        
        try {
            // Используем новую систему blend shapes
            if (this.vrmApp.blendShapeManager) {
                const values = {
                    'Fcl_MTH_A': message.A || 0,
                    'Fcl_MTH_I': message.I || 0,
                    'Fcl_MTH_U': message.U || 0,
                    'Fcl_MTH_E': message.E || 0,
                    'Fcl_MTH_O': message.O || 0,
                    'energy': message.energy || 0
                };
                
        // Если есть energy — используем energy lipsync
        if (typeof message.energy !== 'undefined') {
                    values['Fcl_MTH_A'] = 0;
                    values['Fcl_MTH_I'] = 0;
                    values['Fcl_MTH_U'] = 0;
                    values['Fcl_MTH_E'] = 0;
                    values['Fcl_MTH_O'] = 0;
                }
                
                this.vrmApp.blendShapeManager.applyLipsync(values, 10);
            } else if (this.vrmApp.setLipsync) {
                // Fallback к старой системе
                if (typeof message.energy !== 'undefined') {
                    this.vrmApp.setLipsync({
                        'Fcl_MTH_A': 0,
                        'Fcl_MTH_I': 0,
                        'Fcl_MTH_U': 0,
                        'Fcl_MTH_E': 0,
                        'Fcl_MTH_O': 0,
                        'energy': message.energy
                    });
                }
            }
        } catch (error) {
            console.error('❌ Ошибка обработки липсинка:', error);
            // Fallback к старой системе
            if (this.vrmApp.setLipsync && typeof message.energy !== 'undefined') {
            this.vrmApp.setLipsync({
                'Fcl_MTH_A': 0,
                'Fcl_MTH_I': 0,
                'Fcl_MTH_U': 0,
                'Fcl_MTH_E': 0,
                'Fcl_MTH_O': 0,
                'energy': message.energy
            });
        }
        }
    }
    
    updateStatus(status) {
        // Обновляем индикатор статуса подключения
        const statusIndicator = document.getElementById('ws-status');
        if (statusIndicator) {
            statusIndicator.textContent = `WebSocket: ${status}`;
            statusIndicator.className = `status-${status}`;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts} через ${this.reconnectDelay}ms`);
            
            // Увеличиваем задержку с каждой попыткой
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            setTimeout(() => {
                console.log(`🔄 Выполняем попытку переподключения ${this.reconnectAttempts}...`);
                this.connect();
            }, delay);
        } else {
            console.error('❌ Превышено максимальное количество попыток переподключения');
            this.updateStatus('failed');
            
            // Сбрасываем счетчик попыток через некоторое время для возможности повторного подключения
            setTimeout(() => {
                this.reconnectAttempts = 0;
                console.log('🔄 Сброс счетчика попыток переподключения');
            }, 30000); // 30 секунд
        }
    }
    
    setupEventListeners() {
        // Добавляем обработчики событий для тестирования
        window.addEventListener('beforeunload', () => {
            if (this.ws) {
                this.ws.close();
            }
        });
        
        // Проверяем соединение при возвращении на вкладку
        window.addEventListener('focus', () => {
            if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
                console.log('🔄 Проверка соединения при возвращении на вкладку');
                this.testConnection();
            }
        });
    }
    
    startPingInterval() {
        // Останавливаем предыдущий интервал
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }
        
        // Запускаем новый интервал проверки каждые 30 секунд
        this.pingInterval = setInterval(() => {
            if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.testConnection();
            } else {
                console.log('⚠️ Соединение потеряно, пытаемся переподключиться...');
                this.isConnected = false;
                this.scheduleReconnect();
            }
        }, 30000); // 30 секунд
    }
    
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    sendMessage(message) {
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('⚠️ WebSocket не подключен, сообщение не отправлено');
        }
    }
    
    // Методы для отправки команд ассистенту
    requestEmotion(emotion, intensity = 1.0) {
        this.sendMessage({
            type: 'request_emotion',
            emotion: emotion,
            intensity: intensity
        });
    }
    
    requestAnimation(animation, duration = 5000) {
        this.sendMessage({
            type: 'request_animation',
            animation: animation,
            duration: duration
        });
    }
    
    // Метод для тестирования подключения
    testConnection() {
        if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.log('⚠️ WebSocket не подключен для ping');
            return false;
        }
        
        this.lastPingTime = Date.now();
        this.sendMessage({
            type: 'ping',
            timestamp: this.lastPingTime
        });
        
        console.log('🏓 Отправлен ping для проверки соединения');
        return true;
    }
    
    validateDuration(duration) {
        const { minDuration, maxDuration } = this.textOverlayConfig;
        return Math.max(minDuration, Math.min(maxDuration, duration));
    }

    // === НОВЫЕ ОБРАБОТЧИКИ ДЛЯ УПРАВЛЕНИЯ ===
    
    handleCameraControl(message, received) {
        const { action, value } = message;
        console.log(`📷 Управление камерой: ${action} = ${value}`);
        const applied = performance.now();
        logVrmTiming('camera_control', received, applied);
        
        if (!this.vrmApp) return;
        
        switch (action) {
            case 'distance':
                if (this.vrmApp.camera) {
                    this.vrmApp.camera.position.z = parseFloat(value);
                }
                break;
            case 'rotation':
                if (this.vrmApp.rotationGroup) {
                    this.vrmApp.rotationGroup.rotation.y = THREE.MathUtils.degToRad(parseFloat(value));
                }
                break;
            case 'position':
                if (this.vrmApp.camera && value.x !== undefined && value.y !== undefined && value.z !== undefined) {
                    this.vrmApp.camera.position.set(value.x, value.y, value.z);
                }
                break;
        }
    }
    
    handlePoseControl(message, received) {
        const { bone, axis, value } = message;
        console.log(`🧍 Управление позой: ${bone}.${axis} = ${value}`);
        const applied = performance.now();
        logVrmTiming('pose_control', received, applied);
        
        if (!this.vrmApp) return;
        
        const boneObj = this.vrmApp.findBoneByName(bone);
        if (boneObj) {
            switch (axis) {
                case 'x':
                    boneObj.rotation.x = parseFloat(value);
                    break;
                case 'y':
                    boneObj.rotation.y = parseFloat(value);
                    break;
                case 'z':
                    boneObj.rotation.z = parseFloat(value);
                    break;
            }
        }
    }
    
    handleLightControl(message, received) {
        const { action, value } = message;
        console.log(`💡 Управление освещением: ${action} = ${value}`);
        const applied = performance.now();
        logVrmTiming('light_control', received, applied);
        
        if (!this.vrmApp || !this.vrmApp.lights) return;
        
        const intensity = parseFloat(value);
        
        switch (action) {
            case 'ambient':
                if (this.vrmApp.lights.ambient) {
                    this.vrmApp.lights.ambient.intensity = intensity * 0.6;
                }
                break;
            case 'directional':
                if (this.vrmApp.lights.directional) {
                    this.vrmApp.lights.directional.intensity = intensity;
                }
                break;
            case 'point':
                if (this.vrmApp.lights.point) {
                    this.vrmApp.lights.point.intensity = intensity * 0.5;
                }
                break;
            case 'all':
                if (this.vrmApp.lights.ambient) this.vrmApp.lights.ambient.intensity = intensity * 0.6;
                if (this.vrmApp.lights.directional) this.vrmApp.lights.directional.intensity = intensity;
                if (this.vrmApp.lights.point) this.vrmApp.lights.point.intensity = intensity * 0.5;
                break;
        }
    }
}

// Экспортируем класс для использования в main.js
window.VRMWebSocketClient = VRMWebSocketClient; 