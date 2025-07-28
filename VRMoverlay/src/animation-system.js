/**
 * Улучшенная система анимаций для VRM
 * Поддерживает наложение анимаций, приоритеты и плавные переходы
 */

class AnimationPrioritySystem {
    constructor(vrmApp) {
        this.vrmApp = vrmApp;
        this.mixer = new THREE.AnimationMixer(vrmApp.vrm.scene);
        
        // Слои приоритетов
        this.layers = {
            BASE: 0,        // idle, breathing - базовые анимации
            MOVEMENT: 1,    // talking, thinking - движения
            GESTURE: 2,     // greeting, surprise - жесты
            EMERGENCY: 3    // interrupt animations - прерывающие
        };
        
        this.activeAnimations = new Map();
        this.animationClips = new Map();
        this.blendTimes = new Map();
        
        // Настройки по умолчанию
        this.defaultBlendTime = 0.3;
        this.maxSimultaneousAnimations = 4;
        
        console.log('🎭 AnimationPrioritySystem инициализирована');
    }
    
    /**
     * Регистрирует анимацию в системе
     */
    registerAnimation(name, clip, priority = this.layers.MOVEMENT, blendTime = this.defaultBlendTime) {
        this.animationClips.set(name, clip);
        this.blendTimes.set(name, blendTime);
        
        // Определяем приоритет автоматически по имени
        if (name.includes('idle') || name.includes('breathing')) {
            priority = this.layers.BASE;
        } else if (name.includes('greeting') || name.includes('surprise')) {
            priority = this.layers.GESTURE;
        }
        
        console.log(`📝 Анимация "${name}" зарегистрирована с приоритетом ${priority}`);
    }
    
    /**
     * Воспроизводит анимацию с учетом приоритетов
     */
    playAnimation(name, priority = null, blendTime = null) {
        const clip = this.animationClips.get(name);
        if (!clip) {
            console.warn(`⚠️ Анимация "${name}" не найдена`);
            return false;
        }
        
        // Используем приоритет по умолчанию, если не указан
        if (priority === null) {
            priority = this.getDefaultPriority(name);
        }
        
        // Используем время перехода по умолчанию
        if (blendTime === null) {
            blendTime = this.blendTimes.get(name) || this.defaultBlendTime;
        }
        
        console.log(`▶️ Воспроизведение "${name}" с приоритетом ${priority}`);
        
        // Останавливаем анимации с меньшим или равным приоритетом
        this.stopLowerPriorityAnimations(priority);
        
        // Создаем действие анимации
        const action = this.mixer.clipAction(clip);
        action.setEffectiveWeight(1);
        action.setLoop(THREE.LoopRepeat);
        
        // Плавный переход
        if (blendTime > 0) {
            action.fadeIn(blendTime);
        }
        
        action.play();
        
        // Сохраняем активную анимацию
        this.activeAnimations.set(priority, {
            name,
            action,
            startTime: Date.now()
        });
        
        return true;
    }
    
    /**
     * Останавливает анимации с меньшим приоритетом
     */
    stopLowerPriorityAnimations(priority) {
        const toStop = [];
        
        for (const [animPriority, animation] of this.activeAnimations) {
            if (animPriority <= priority) {
                toStop.push(animPriority);
            }
        }
        
        toStop.forEach(priority => {
            const animation = this.activeAnimations.get(priority);
            if (animation) {
                animation.action.fadeOut(0.2);
                setTimeout(() => {
                    animation.action.stop();
                }, 200);
                this.activeAnimations.delete(priority);
                console.log(`⏹️ Остановлена анимация "${animation.name}" (приоритет ${priority})`);
            }
        });
    }
    
    /**
     * Останавливает конкретную анимацию
     */
    stopAnimation(name) {
        for (const [priority, animation] of this.activeAnimations) {
            if (animation.name === name) {
                animation.action.fadeOut(0.2);
                setTimeout(() => {
                    animation.action.stop();
                }, 200);
                this.activeAnimations.delete(priority);
                console.log(`⏹️ Остановлена анимация "${name}"`);
                return true;
            }
        }
        return false;
    }
    
    /**
     * Останавливает все анимации
     */
    stopAllAnimations() {
        this.activeAnimations.forEach((animation, priority) => {
            animation.action.fadeOut(0.2);
            setTimeout(() => {
                animation.action.stop();
            }, 200);
        });
        this.activeAnimations.clear();
        console.log('⏹️ Все анимации остановлены');
    }
    
    /**
     * Определяет приоритет по умолчанию для анимации
     */
    getDefaultPriority(name) {
        if (name.includes('idle') || name.includes('breathing')) {
            return this.layers.BASE;
        } else if (name.includes('talking') || name.includes('thinking')) {
            return this.layers.MOVEMENT;
        } else if (name.includes('greeting') || name.includes('surprise') || name.includes('excitement')) {
            return this.layers.GESTURE;
        } else {
            return this.layers.MOVEMENT;
        }
    }
    
    /**
     * Обновляет миксер (вызывается в animate loop)
     */
    update(deltaTime) {
        this.mixer.update(deltaTime);
    }
    
    /**
     * Получает список активных анимаций
     */
    getActiveAnimations() {
        const active = [];
        for (const [priority, animation] of this.activeAnimations) {
            active.push({
                name: animation.name,
                priority,
                duration: Date.now() - animation.startTime
            });
        }
        return active.sort((a, b) => b.priority - a.priority);
    }
    
    /**
     * Проверяет, активна ли анимация
     */
    isAnimationActive(name) {
        for (const animation of this.activeAnimations.values()) {
            if (animation.name === name) {
                return true;
            }
        }
        return false;
    }
}

class BlendShapeManager {
    constructor(vrmApp) {
        this.vrmApp = vrmApp;
        
        // Категории blend shapes
        this.categories = {
            EMOTIONS: ['Fcl_HAP_HAP', 'Fcl_SAD_SAD', 'Fcl_ANG_ANG', 'Fcl_SUR_SUR'],
            LIPSYNC: ['Fcl_MTH_A', 'Fcl_MTH_I', 'Fcl_MTH_U', 'Fcl_MTH_E', 'Fcl_MTH_O'],
            BLINKING: ['Fcl_EYE_CLOSE_L', 'Fcl_EYE_CLOSE_R'],
            CUSTOM: []
        };
        
        this.activeShapes = new Map();
        this.priorities = new Map();
        this.transitions = new Map();
        
        // Настройки по умолчанию
        this.defaultTransitionTime = 0.3;
        this.maxSimultaneousShapes = 10;
        
        console.log('🎭 BlendShapeManager инициализирован');
    }
    
    /**
     * Применяет blend shape с приоритетом и переходом
     */
    applyBlendShape(name, value, priority = 0, duration = this.defaultTransitionTime) {
        const target = Math.max(0, Math.min(1, value));
        const current = this.activeShapes.get(name) || 0;
        
        // Если значение не изменилось, ничего не делаем
        if (Math.abs(current - target) < 0.01) {
            return;
        }
        
        // Останавливаем предыдущий переход для этого blend shape
        if (this.transitions.has(name)) {
            this.transitions.get(name).stop();
        }
        
        // Создаем новый переход
        const tween = new TWEEN.Tween({ value: current })
            .to({ value: target }, duration * 1000)
            .easing(TWEEN.Easing.Quadratic.Out)
            .onUpdate((obj) => {
                this.setBlendShapeValue(name, obj.value);
            })
            .onComplete(() => {
                this.transitions.delete(name);
            });
        
        tween.start();
        this.transitions.set(name, tween);
        this.activeShapes.set(name, target);
        this.priorities.set(name, priority);
        
        console.log(`🎭 Blend shape "${name}": ${current.toFixed(2)} → ${target.toFixed(2)} (приоритет ${priority})`);
    }
    
    /**
     * Устанавливает значение blend shape напрямую
     */
    setBlendShapeValue(name, value) {
        this.vrmApp.vrm.scene.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                const index = child.morphTargetDictionary[name];
                if (typeof index !== 'undefined') {
                    child.morphTargetInfluences[index] = Math.max(0, Math.min(1, value));
                }
            }
        });
    }
    
    /**
     * Применяет эмоцию с приоритетом
     */
    applyEmotion(emotionName, intensity = 1.0, priority = 5) {
        const emotionValues = {
            'happy': { 'Fcl_HAP_HAP': 0.8 * intensity, 'Fcl_SAD_SAD': 0 },
            'sad': { 'Fcl_HAP_HAP': 0, 'Fcl_SAD_SAD': 0.7 * intensity },
            'angry': { 'Fcl_ANG_ANG': 0.8 * intensity },
            'surprised': { 'Fcl_SUR_SUR': 0.8 * intensity },
            'neutral': { 'Fcl_HAP_HAP': 0, 'Fcl_SAD_SAD': 0, 'Fcl_ANG_ANG': 0, 'Fcl_SUR_SUR': 0 }
        };
        
        const values = emotionValues[emotionName];
        if (!values) {
            console.warn(`⚠️ Эмоция "${emotionName}" не найдена`);
            return;
        }
        
        // Применяем все blend shapes для эмоции
        Object.entries(values).forEach(([shapeName, value]) => {
            this.applyBlendShape(shapeName, value, priority, 0.5);
        });
        
        console.log(`😊 Применена эмоция "${emotionName}" с интенсивностью ${intensity}`);
    }
    
    /**
     * Сбрасывает все эмоции
     */
    resetEmotions() {
        this.categories.EMOTIONS.forEach(shapeName => {
            this.applyBlendShape(shapeName, 0, 0, 0.3);
        });
        console.log('😊 Эмоции сброшены');
    }
    
    /**
     * Применяет липсинк с приоритетом
     */
    applyLipsync(values, priority = 10) {
        // Применяем гласные с высоким приоритетом
        this.categories.LIPSYNC.forEach(shapeName => {
            const value = values[shapeName] || 0;
            this.applyBlendShape(shapeName, value, priority, 0.1);
        });
    }
    
    /**
     * Обновляет переходы (вызывается в animate loop)
     */
    update() {
        TWEEN.update();
    }
    
    /**
     * Получает список активных blend shapes
     */
    getActiveBlendShapes() {
        const active = [];
        for (const [name, value] of this.activeShapes) {
            if (value > 0.01) {
                active.push({
                    name,
                    value,
                    priority: this.priorities.get(name) || 0
                });
            }
        }
        return active.sort((a, b) => b.priority - a.priority);
    }
    
    /**
     * Очищает все blend shapes
     */
    clearAll() {
        this.activeShapes.forEach((value, name) => {
            this.applyBlendShape(name, 0, 0, 0.2);
        });
        this.activeShapes.clear();
        this.priorities.clear();
    }
}

class AnimationStateMachine {
    constructor(vrmApp) {
        this.vrmApp = vrmApp;
        
        // Состояния анимации
        this.states = {
            IDLE: 'idle',
            TALKING: 'talking',
            THINKING: 'thinking',
            GESTURING: 'gesturing',
            EMOTIONAL: 'emotional',
            LISTENING: 'listening'
        };
        
        this.currentState = this.states.IDLE;
        this.previousState = null;
        this.transitions = new Map();
        this.stateAnimations = new Map();
        
        this.setupTransitions();
        this.setupStateAnimations();
        
        console.log('🎭 AnimationStateMachine инициализирована');
    }
    
    /**
     * Настраивает разрешенные переходы между состояниями
     */
    setupTransitions() {
        this.transitions.set(this.states.IDLE, [
            this.states.TALKING,
            this.states.THINKING,
            this.states.GESTURING,
            this.states.LISTENING
        ]);
        
        this.transitions.set(this.states.TALKING, [
            this.states.IDLE,
            this.states.EMOTIONAL,
            this.states.GESTURING
        ]);
        
        this.transitions.set(this.states.THINKING, [
            this.states.IDLE,
            this.states.TALKING
        ]);
        
        this.transitions.set(this.states.GESTURING, [
            this.states.IDLE,
            this.states.TALKING
        ]);
        
        this.transitions.set(this.states.EMOTIONAL, [
            this.states.IDLE,
            this.states.TALKING
        ]);
        
        this.transitions.set(this.states.LISTENING, [
            this.states.IDLE,
            this.states.TALKING
        ]);
    }
    
    /**
     * Настраивает анимации для каждого состояния
     */
    setupStateAnimations() {
        this.stateAnimations.set(this.states.IDLE, 'idle');
        this.stateAnimations.set(this.states.TALKING, 'talking');
        this.stateAnimations.set(this.states.THINKING, 'thinking_move');
        this.stateAnimations.set(this.states.GESTURING, 'greeting');
        this.stateAnimations.set(this.states.EMOTIONAL, 'excitement');
        this.stateAnimations.set(this.states.LISTENING, 'listening');
    }
    
    /**
     * Переходит в новое состояние
     */
    transitionTo(newState, blendTime = 0.5) {
        if (!this.canTransitionTo(newState)) {
            console.warn(`⚠️ Переход из "${this.currentState}" в "${newState}" не разрешен`);
            return false;
        }
        
        const oldState = this.currentState;
        this.previousState = oldState;
        this.currentState = newState;
        
        // Воспроизводим анимацию нового состояния
        const animationName = this.stateAnimations.get(newState);
        if (animationName && this.vrmApp.animationSystem) {
            this.vrmApp.animationSystem.playAnimation(animationName, null, blendTime);
        }
        
        console.log(`🔄 Переход: ${oldState} → ${newState}`);
        return true;
    }
    
    /**
     * Проверяет, возможен ли переход в новое состояние
     */
    canTransitionTo(newState) {
        const allowedTransitions = this.transitions.get(this.currentState);
        return allowedTransitions && allowedTransitions.includes(newState);
    }
    
    /**
     * Возвращается к предыдущему состоянию
     */
    revertToPrevious() {
        if (this.previousState) {
            return this.transitionTo(this.previousState);
        }
        return false;
    }
    
    /**
     * Получает текущее состояние
     */
    getCurrentState() {
        return this.currentState;
    }
    
    /**
     * Получает список разрешенных переходов из текущего состояния
     */
    getAllowedTransitions() {
        return this.transitions.get(this.currentState) || [];
    }
}

// Экспорт классов
window.AnimationPrioritySystem = AnimationPrioritySystem;
window.BlendShapeManager = BlendShapeManager;
window.AnimationStateMachine = AnimationStateMachine; 