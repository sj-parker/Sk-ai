/**
 * Интеграция улучшенной системы анимаций
 * Показывает, как заменить старую систему на новую
 */

import { AnimationPrioritySystem, BlendShapeManager, AnimationStateMachine } from './animation-system.js';

class AnimationIntegration {
    constructor(vrmApp) {
        this.vrmApp = vrmApp;
        
        // Инициализируем новые системы
        this.animationSystem = new AnimationPrioritySystem(vrmApp);
        this.blendShapeManager = new BlendShapeManager(vrmApp);
        this.stateMachine = new AnimationStateMachine(vrmApp);
        
        // Сохраняем ссылки на новые системы в основном приложении
        vrmApp.animationSystem = this.animationSystem;
        vrmApp.blendShapeManager = this.blendShapeManager;
        vrmApp.stateMachine = this.stateMachine;
        
        console.log('🔗 AnimationIntegration инициализирована');
    }
    
    /**
     * Мигрирует существующие анимации в новую систему
     */
    migrateExistingAnimations() {
        console.log('🔄 Миграция существующих анимаций...');
        
        // Регистрируем все существующие анимации
        Object.entries(this.vrmApp.movementAnimations).forEach(([name, clip]) => {
            this.animationSystem.registerAnimation(name, clip);
        });
        
        // Запускаем базовую анимацию
        this.animationSystem.playAnimation('idle');
        
        console.log('✅ Миграция завершена');
    }
    
    /**
     * Заменяет старую функцию playMovement
     */
    playMovement(movementName) {
        // Используем новую систему приоритетов
        return this.animationSystem.playAnimation(movementName);
    }
    
    /**
     * Заменяет старую функцию applyEmotion
     */
    applyEmotion(emotionName) {
        // Используем новую систему blend shapes
        return this.blendShapeManager.applyEmotion(emotionName);
    }
    
    /**
     * Заменяет старую функцию setLipsync
     */
    setLipsync(values) {
        // Используем новую систему blend shapes с высоким приоритетом
        return this.blendShapeManager.applyLipsync(values, 10);
    }
    
    /**
     * Обновляет все системы (вызывается в animate loop)
     */
    update(deltaTime) {
        this.animationSystem.update(deltaTime);
        this.blendShapeManager.update();
    }
}

/**
 * Примеры использования новой системы
 */

// Пример 1: Наложение анимаций
function exampleOverlappingAnimations() {
    const app = window.app;
    
    // Базовая анимация (idle) + жесты
    app.animationSystem.playAnimation('idle', app.animationSystem.layers.BASE);
    app.animationSystem.playAnimation('greeting', app.animationSystem.layers.GESTURE);
    
    // Результат: idle продолжается, greeting накладывается поверх
}

// Пример 2: Эмоции с приоритетами
function exampleEmotionPriorities() {
    const app = window.app;
    
    // Базовая эмоция
    app.blendShapeManager.applyEmotion('happy', 0.5, 5);
    
    // Временная эмоция с высоким приоритетом
    app.blendShapeManager.applyEmotion('surprised', 0.8, 8);
    
    // Через 2 секунды возвращаемся к базовой эмоции
    setTimeout(() => {
        app.blendShapeManager.applyEmotion('happy', 0.5, 5);
    }, 2000);
}

// Пример 3: Управление состояниями
function exampleStateManagement() {
    const app = window.app;
    
    // Переходы между состояниями
    app.stateMachine.transitionTo(app.stateMachine.states.TALKING);
    
    // Проверяем разрешенные переходы
    const allowed = app.stateMachine.getAllowedTransitions();
    console.log('Разрешенные переходы:', allowed);
    
    // Возврат к предыдущему состоянию
    setTimeout(() => {
        app.stateMachine.revertToPrevious();
    }, 5000);
}

// Пример 4: Комплексная анимация
function exampleComplexAnimation() {
    const app = window.app;
    
    // 1. Базовое состояние
    app.stateMachine.transitionTo(app.stateMachine.states.TALKING);
    
    // 2. Эмоция
    app.blendShapeManager.applyEmotion('excited', 0.7, 6);
    
    // 3. Жест поверх разговора
    app.animationSystem.playAnimation('greeting', app.animationSystem.layers.GESTURE);
    
    // 4. Липсинк с высоким приоритетом
    app.blendShapeManager.applyLipsync({
        'Fcl_MTH_A': 0.8,
        'Fcl_MTH_I': 0.2,
        'Fcl_MTH_U': 0.1
    }, 10);
    
    // Результат: talking + excited + greeting + lipsync одновременно
}

/**
 * Интеграция с WebSocket
 */

// Обработчик статуса с новой системой
function handleStatusWithNewSystem(message) {
    const app = window.app;
    
    switch (message.status) {
        case 'idle':
            app.stateMachine.transitionTo(app.stateMachine.states.IDLE);
            break;
        case 'talking':
            app.stateMachine.transitionTo(app.stateMachine.states.TALKING);
            break;
        case 'thinking':
            app.stateMachine.transitionTo(app.stateMachine.states.THINKING);
            break;
        case 'listening':
            app.stateMachine.transitionTo(app.stateMachine.states.LISTENING);
            break;
    }
}

// Обработчик эмоций с новой системой
function handleEmotionWithNewSystem(message) {
    const app = window.app;
    
    const emotion = message.emotion || 'neutral';
    const intensity = message.intensity || 1.0;
    const priority = message.priority || 5;
    
    app.blendShapeManager.applyEmotion(emotion, intensity, priority);
}

// Обработчик липсинка с новой системой
function handleLipsyncWithNewSystem(message) {
    const app = window.app;
    
    const values = {
        'Fcl_MTH_A': message.A || 0,
        'Fcl_MTH_I': message.I || 0,
        'Fcl_MTH_U': message.U || 0,
        'Fcl_MTH_E': message.E || 0,
        'Fcl_MTH_O': message.O || 0
    };
    
    app.blendShapeManager.applyLipsync(values, 10);
}

/**
 * Отладочные функции
 */

// Показать активные анимации
function showActiveAnimations() {
    const app = window.app;
    const active = app.animationSystem.getActiveAnimations();
    console.log('🎭 Активные анимации:', active);
}

// Показать активные blend shapes
function showActiveBlendShapes() {
    const app = window.app;
    const active = app.blendShapeManager.getActiveBlendShapes();
    console.log('🎭 Активные blend shapes:', active);
}

// Показать текущее состояние
function showCurrentState() {
    const app = window.app;
    const state = app.stateMachine.getCurrentState();
    const allowed = app.stateMachine.getAllowedTransitions();
    console.log('🎭 Текущее состояние:', state);
    console.log('🎭 Разрешенные переходы:', allowed);
}

// Экспорт функций для использования в консоли
window.AnimationExamples = {
    overlappingAnimations: exampleOverlappingAnimations,
    emotionPriorities: exampleEmotionPriorities,
    stateManagement: exampleStateManagement,
    complexAnimation: exampleComplexAnimation,
    showActiveAnimations,
    showActiveBlendShapes,
    showCurrentState
};

window.AnimationIntegration = AnimationIntegration; 