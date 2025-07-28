/**
 * Модуль оптимизации производительности для VRM Overlay
 * Автоматически настраивает параметры для оптимальной работы на слабых ПК
 */

class PerformanceOptimizer {
    constructor() {
        this.settings = {
            // Настройки рендеринга
            renderScale: 1.0,
            maxFPS: 60,
            enableVSync: true,
            enableAntialiasing: true,
            shadowQuality: 'medium',
            
            // Настройки анимаций
            animationUpdateRate: 60,
            enableComplexAnimations: true,
            enableMicroMovements: true,
            enableBreathing: true,
            
            // Настройки освещения
            enableShadows: true,
            shadowMapSize: 1024,
            lightQuality: 'medium',
            
            // Настройки модели
            modelLOD: 'high',
            enableBlendShapes: true,
            enableLipsync: true,
            
            // Настройки WebSocket
            websocketUpdateRate: 30,
            enableDetailedLogging: false
        };
        
        this.performanceMode = 'auto'; // 'auto', 'low', 'medium', 'high'
        this.fpsHistory = [];
        this.lastFpsCheck = 0;
        this.adaptiveMode = true;
        
        this.init();
    }
    
    init() {
        console.log('🎯 Инициализация оптимизатора производительности...');
        this.detectHardware();
        this.loadSettings();
        this.setupAdaptiveOptimization();
    }
    
    detectHardware() {
        // Определяем характеристики системы
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (gl) {
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (debugInfo) {
                const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                console.log('🎮 GPU:', renderer);
                
                // Определяем производительность GPU
                if (renderer.includes('Intel') || renderer.includes('HD Graphics')) {
                    this.performanceMode = 'low';
                    console.log('📉 Обнаружена интегрированная графика, режим: LOW');
                } else if (renderer.includes('GTX') || renderer.includes('RTX')) {
                    this.performanceMode = 'high';
                    console.log('📈 Обнаружена дискретная графика, режим: HIGH');
                } else {
                    this.performanceMode = 'medium';
                    console.log('📊 Режим производительности: MEDIUM');
                }
            }
        }
        
        // Проверяем количество ядер CPU
        if (navigator.hardwareConcurrency) {
            const cores = navigator.hardwareConcurrency;
            console.log('🖥️ CPU ядер:', cores);
            
            if (cores <= 2) {
                this.performanceMode = 'low';
                console.log('📉 Маломощный CPU, режим: LOW');
            }
        }
        
        // Проверяем память
        if (navigator.deviceMemory) {
            const memory = navigator.deviceMemory;
            console.log('💾 RAM:', memory, 'GB');
            
            if (memory <= 4) {
                this.performanceMode = 'low';
                console.log('📉 Малый объем RAM, режим: LOW');
            }
        }
    }
    
    loadSettings() {
        // Загружаем сохраненные настройки
        const saved = localStorage.getItem('vrm_performance_settings');
        if (saved) {
            try {
                const loaded = JSON.parse(saved);
                this.settings = { ...this.settings, ...loaded };
                console.log('💾 Загружены сохраненные настройки производительности');
            } catch (error) {
                console.error('❌ Ошибка загрузки настроек:', error);
            }
        }
        
        // Применяем настройки в зависимости от режима
        this.applyPerformanceMode();
    }
    
    applyPerformanceMode() {
        const modes = {
            low: {
                renderScale: 0.75,
                maxFPS: 30,
                enableVSync: true,
                enableAntialiasing: false,
                shadowQuality: 'low',
                animationUpdateRate: 30,
                enableComplexAnimations: false,
                enableMicroMovements: false,
                enableBreathing: false,
                enableShadows: false,
                shadowMapSize: 512,
                lightQuality: 'low',
                modelLOD: 'low',
                enableBlendShapes: true,
                enableLipsync: true,
                websocketUpdateRate: 15,
                enableDetailedLogging: false
            },
            medium: {
                renderScale: 0.9,
                maxFPS: 45,
                enableVSync: true,
                enableAntialiasing: true,
                shadowQuality: 'medium',
                animationUpdateRate: 45,
                enableComplexAnimations: true,
                enableMicroMovements: true,
                enableBreathing: true,
                enableShadows: true,
                shadowMapSize: 1024,
                lightQuality: 'medium',
                modelLOD: 'medium',
                enableBlendShapes: true,
                enableLipsync: true,
                websocketUpdateRate: 30,
                enableDetailedLogging: false
            },
            high: {
                renderScale: 1.0,
                maxFPS: 60,
                enableVSync: true,
                enableAntialiasing: true,
                shadowQuality: 'high',
                animationUpdateRate: 60,
                enableComplexAnimations: true,
                enableMicroMovements: true,
                enableBreathing: true,
                enableShadows: true,
                shadowMapSize: 2048,
                lightQuality: 'high',
                modelLOD: 'high',
                enableBlendShapes: true,
                enableLipsync: true,
                websocketUpdateRate: 60,
                enableDetailedLogging: true
            }
        };
        
        if (modes[this.performanceMode]) {
            this.settings = { ...this.settings, ...modes[this.performanceMode] };
            console.log(`⚙️ Применен режим производительности: ${this.performanceMode.toUpperCase()}`);
        }
    }
    
    setupAdaptiveOptimization() {
        if (!this.adaptiveMode) return;
        
        // Адаптивная оптимизация каждые 5 секунд
        setInterval(() => {
            this.checkPerformance();
        }, 5000);
        
        console.log('🔄 Адаптивная оптимизация включена');
    }
    
    checkPerformance() {
        const now = performance.now();
        if (now - this.lastFpsCheck < 1000) return;
        
        // Получаем текущий FPS
        const currentFPS = this.getCurrentFPS();
        if (currentFPS === null) return;
        
        this.fpsHistory.push(currentFPS);
        if (this.fpsHistory.length > 10) {
            this.fpsHistory.shift();
        }
        
        const avgFPS = this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length;
        const targetFPS = this.settings.maxFPS;
        
        // Адаптивная настройка
        if (avgFPS < targetFPS * 0.8) {
            this.degradePerformance();
        } else if (avgFPS > targetFPS * 0.95) {
            this.improvePerformance();
        }
        
        this.lastFpsCheck = now;
    }
    
    getCurrentFPS() {
        // Получаем FPS из основного приложения
        if (window.app && window.app.currentFPS) {
            return window.app.currentFPS;
        }
        return null;
    }
    
    degradePerformance() {
        console.log('📉 Снижение качества для улучшения производительности');
        
        // Снижаем качество рендеринга
        if (this.settings.renderScale > 0.5) {
            this.settings.renderScale = Math.max(0.5, this.settings.renderScale - 0.1);
        }
        
        // Отключаем сложные эффекты
        if (this.settings.enableAntialiasing) {
            this.settings.enableAntialiasing = false;
        }
        
        if (this.settings.enableShadows) {
            this.settings.enableShadows = false;
        }
        
        // Снижаем частоту обновлений
        if (this.settings.animationUpdateRate > 20) {
            this.settings.animationUpdateRate = Math.max(20, this.settings.animationUpdateRate - 10);
        }
        
        this.applySettings();
    }
    
    improvePerformance() {
        console.log('📈 Улучшение качества при хорошей производительности');
        
        // Улучшаем качество рендеринга
        if (this.settings.renderScale < 1.0) {
            this.settings.renderScale = Math.min(1.0, this.settings.renderScale + 0.05);
        }
        
        // Включаем эффекты обратно
        if (!this.settings.enableAntialiasing && this.performanceMode !== 'low') {
            this.settings.enableAntialiasing = true;
        }
        
        if (!this.settings.enableShadows && this.performanceMode !== 'low') {
            this.settings.enableShadows = true;
        }
        
        // Увеличиваем частоту обновлений
        if (this.settings.animationUpdateRate < this.settings.maxFPS) {
            this.settings.animationUpdateRate = Math.min(this.settings.maxFPS, this.settings.animationUpdateRate + 5);
        }
        
        this.applySettings();
    }
    
    applySettings() {
        // Применяем настройки к рендереру
        if (window.app && window.app.renderer) {
            const renderer = window.app.renderer;
            
            // Настройка рендерера
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            
            if (!this.settings.enableAntialiasing) {
                renderer.antialias = false;
            }
            
            // Настройка теней
            if (this.settings.enableShadows) {
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            } else {
                renderer.shadowMap.enabled = false;
            }
        }
        
        // Сохраняем настройки
        this.saveSettings();
    }
    
    saveSettings() {
        try {
            localStorage.setItem('vrm_performance_settings', JSON.stringify(this.settings));
        } catch (error) {
            console.error('❌ Ошибка сохранения настроек:', error);
        }
    }
    
    // Публичные методы для управления
    setPerformanceMode(mode) {
        if (['low', 'medium', 'high', 'auto'].includes(mode)) {
            this.performanceMode = mode;
            this.applyPerformanceMode();
            this.applySettings();
            console.log(`🎯 Режим производительности изменен на: ${mode.toUpperCase()}`);
        }
    }
    
    getSettings() {
        return { ...this.settings };
    }
    
    updateSetting(key, value) {
        if (key in this.settings) {
            this.settings[key] = value;
            this.applySettings();
            console.log(`⚙️ Настройка обновлена: ${key} = ${value}`);
        }
    }
    
    getPerformanceInfo() {
        return {
            mode: this.performanceMode,
            settings: this.settings,
            fpsHistory: [...this.fpsHistory],
            avgFPS: this.fpsHistory.length > 0 ? 
                this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length : 0
        };
    }
    
    // Методы для интеграции с основным приложением
    optimizeRenderer(renderer) {
        if (!renderer) return;
        
        console.log('🎨 Оптимизация рендерера...');
        
        // Настройка качества рендеринга
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.antialias = this.settings.enableAntialiasing;
        
        // Настройка теней
        if (this.settings.enableShadows) {
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        } else {
            renderer.shadowMap.enabled = false;
        }
        
        // Настройка размера рендера
        const width = window.innerWidth * this.settings.renderScale;
        const height = window.innerHeight * this.settings.renderScale;
        renderer.setSize(width, height);
        
        console.log('✅ Рендерер оптимизирован');
    }
    
    optimizeLights(lights) {
        if (!lights) return;
        
        console.log('💡 Оптимизация освещения...');
        
        // Настройка качества теней
        if (lights.directional) {
            lights.directional.castShadow = this.settings.enableShadows;
            if (this.settings.enableShadows) {
                lights.directional.shadow.mapSize.width = this.settings.shadowMapSize;
                lights.directional.shadow.mapSize.height = this.settings.shadowMapSize;
            }
        }
        
        // Настройка интенсивности в зависимости от качества
        const intensityMultiplier = {
            low: 0.8,
            medium: 1.0,
            high: 1.2
        }[this.settings.lightQuality] || 1.0;
        
        if (lights.ambient) lights.ambient.intensity *= intensityMultiplier;
        if (lights.directional) lights.directional.intensity *= intensityMultiplier;
        if (lights.point) lights.point.intensity *= intensityMultiplier;
        
        console.log('✅ Освещение оптимизировано');
    }
    
    optimizeAnimations(mixer) {
        if (!mixer) return;
        
        console.log('🎭 Оптимизация анимаций...');
        
        // Настройка частоты обновления анимаций
        mixer.timeScale = this.settings.animationUpdateRate / 60;
        
        console.log('✅ Анимации оптимизированы');
    }
}

// Экспорт для использования в других модулях
window.PerformanceOptimizer = PerformanceOptimizer; 