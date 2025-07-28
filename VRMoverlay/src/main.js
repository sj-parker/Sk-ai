// Three.js загружается через CDN в HTML
// VRMWebSocketClient теперь доступен через window.VRMWebSocketClient
// AnimationIntegration теперь доступен через window.AnimationIntegration

class VRMStreamingApp {
    constructor() {
        console.log('🚀 Инициализация VRMStreamingApp...');
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.vrm = null;
        this.clock = new THREE.Clock();
        this.controls = {};
        this.isLoaded = false;
        this.animations = [];
        this.currentAnimation = null;
        this.mixer = null;
        this.blendShapes = [];
        this.currentBlendShapes = {};
        this.movementAnimations = {};
        this.currentMovement = null;
        this.movementMixer = null;
        this.originalColors = [];
        this.naturalPose = null;
        this.blinkInterval = null;
        this.isBlinking = false;
        
        // Добавляем переменные для FPS
        this.frameCount = 0;
        this.lastFpsUpdate = 0;
        this.currentFPS = 0;
        this.lastFrameTime = 0;
        
        // Добавляем состояние для липсинка
        this.lipsyncBlendShapes = {
            'Fcl_MTH_A': 0,
            'Fcl_MTH_I': 0,
            'Fcl_MTH_U': 0,
            'Fcl_MTH_E': 0,
            'Fcl_MTH_O': 0,
            'energy': 0 // новое поле для амплитуды
        };

        // Добавляем интерполятор для плавности
        this.lipsyncLerp = {
            target: { ...this.lipsyncBlendShapes },
            current: { ...this.lipsyncBlendShapes },
            speed: 0.3 // Скорость интерполяции
        };
        
        // Инициализируем новую систему анимаций
        try {
            this.animationIntegration = new window.AnimationIntegration(this);
            console.log('✅ Новая система анимаций инициализирована');
        } catch (error) {
            console.error('❌ Ошибка инициализации новой системы анимаций:', error);
            this.animationIntegration = null;
        }
        
        // Инициализируем оптимизатор производительности
        try {
            this.performanceOptimizer = new PerformanceOptimizer();
            console.log('✅ Оптимизатор производительности инициализирован');
        } catch (error) {
            console.error('❌ Ошибка инициализации оптимизатора:', error);
            this.performanceOptimizer = null;
        }
        
        console.log('✅ Конструктор завершен, вызываем init()...');
        this.init();
    }

    init() {
        console.log('🔧 Начинаем инициализацию...');
        try {
            this.setupScene();
            console.log('✅ Сцена настроена');
            
            this.setupCamera();
            console.log('✅ Камера настроена');
            
            this.setupRenderer();
            console.log('✅ Рендерер настроен');
            
            this.setupLights();
            console.log('✅ Освещение настроено');
            
            this.setupControls();
            console.log('✅ Элементы управления настроены');
            
            this.loadVRMModel();
            console.log('✅ Загрузка модели запущена');
            
            this.animate();
            console.log('✅ Анимация запущена');
            
            this.updateInfo();
            console.log('✅ Информация обновлена');
            
            // Инициализируем FPS
            this.lastFpsUpdate = Date.now();
            this.frameCount = 0;
            this.currentFPS = 0;
            
            // === Новый WebSocket клиент ===
            try {
                this.wsClient = new window.VRMWebSocketClient(this);
                console.log('✅ WebSocket клиент инициализирован');
                
                // Восстанавливаем последнее состояние при переподключении
                this.restoreLastState();
            } catch (error) {
                console.error('❌ Ошибка инициализации WebSocket клиента:', error);
                this.wsClient = null;
            }
            
            console.log('🎉 Инициализация завершена успешно!');
        } catch (error) {
            console.error('❌ Ошибка при инициализации:', error);
        }
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = null; // Прозрачный фон для OBS
    }

    setupCamera() {
        this.camera = new THREE.PerspectiveCamera(
            45,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 1.5, 3);
        this.camera.lookAt(0, 1, 0);
    }

    setupRenderer() {
        const canvas = document.getElementById('canvas');
        
        // Получаем настройки от оптимизатора
        const settings = this.performanceOptimizer ? this.performanceOptimizer.getSettings() : {
            enableAntialiasing: true,
            enableShadows: true,
            renderScale: 1.0
        };
        
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: canvas,
            antialias: settings.enableAntialiasing,
            alpha: true
        });
        
        // Применяем оптимизации к рендереру
        if (this.performanceOptimizer) {
            this.performanceOptimizer.optimizeRenderer(this.renderer);
        } else {
            // Базовые настройки без оптимизатора
        this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            this.renderer.shadowMap.enabled = settings.enableShadows;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        }
        
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    }

    setupLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 5, 5);
        
        // Получаем настройки от оптимизатора
        const settings = this.performanceOptimizer ? this.performanceOptimizer.getSettings() : {
            enableShadows: true,
            shadowMapSize: 1024
        };
        
        directionalLight.castShadow = settings.enableShadows;
        if (settings.enableShadows) {
            directionalLight.shadow.mapSize.width = settings.shadowMapSize;
            directionalLight.shadow.mapSize.height = settings.shadowMapSize;
        }
        
        this.scene.add(directionalLight);

        const pointLight = new THREE.PointLight(0xffffff, 0.5);
        pointLight.position.set(-5, 5, 5);
        this.scene.add(pointLight);

        this.lights = {
            ambient: ambientLight,
            directional: directionalLight,
            point: pointLight
        };
        
        // Применяем оптимизации к освещению
        if (this.performanceOptimizer) {
            this.performanceOptimizer.optimizeLights(this.lights);
        }
    }

    setupControls() {
        // Проверяем, находимся ли мы в режиме OBS
        if (window.IS_OBS_MODE) {
            console.log('🎭 OBS режим: элементы управления отключены');
            return;
        }

        // Используем уже существующий контейнер .controls из index.html
        const controlsContainer = document.querySelector('.controls');
        if (!controlsContainer) {
            console.log('⚠️ Контейнер .controls не найден');
            return;
        }

        // Добавляем кнопку для тестирования липсинка
        const lipsyncTestButton = document.createElement('button');
        lipsyncTestButton.textContent = '👄 Тест липсинка';
        lipsyncTestButton.onclick = () => this.testLipsync();
        controlsContainer.appendChild(lipsyncTestButton);

        // Добавляем кнопки для тестирования новой системы анимаций
        const newSystemGroup = document.createElement('div');
        newSystemGroup.className = 'control-group';
        newSystemGroup.innerHTML = `
            <h3 style="margin: 10px 0 5px 0; color: #223; font-size:15px;">🎭 Новая система анимаций</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-bottom: 10px;">
                <button class="btn" onclick="window.app.testOverlappingAnimations()">Наложение</button>
                <button class="btn" onclick="window.app.testEmotionPriorities()">Приоритеты</button>
                <button class="btn" onclick="window.app.testStateMachine()">State Machine</button>
                <button class="btn" onclick="window.app.showDebugInfo()">Отладка</button>
            </div>
        `;
        controlsContainer.appendChild(newSystemGroup);

        console.log('Настройка элементов управления...');
        
        this.controls.cameraDistance = document.getElementById('cameraDistance');
        this.controls.rotationSpeed = document.getElementById('rotationSpeed');
        this.controls.lightIntensity = document.getElementById('lightIntensity');
        this.controls.fullscreenBtn = document.getElementById('fullscreenBtn');
        this.controls.screenshotBtn = document.getElementById('screenshotBtn');
        this.controls.performanceBtn = document.getElementById('performanceBtn');
        this.controls.websocketTestBtn = document.getElementById('websocketTestBtn');
        this.controls.resetLightBtn = document.getElementById('resetLightBtn');
        this.controls.faceCameraBtn = document.getElementById('faceCameraBtn');

        if (this.controls.cameraDistance) {
            this.controls.cameraDistance.addEventListener('input', (e) => {
                const distance = parseFloat(e.target.value);
                this.camera.position.z = distance;
                
                // Убираем автоматическую отправку команд - теперь только по кнопке "Применить к OBS"
            });
        }

        if (this.controls.rotationSpeed) {
            this.controls.rotationSpeed.addEventListener('input', (e) => {
                const rotationAngle = parseFloat(e.target.value);
                const rotationRadians = THREE.MathUtils.degToRad(rotationAngle);
                
                if (this.rotationGroup) {
                    this.rotationGroup.rotation.y = rotationRadians;
                }
                
                // Убираем автоматическую отправку команд - теперь только по кнопке "Применить к OBS"
                
                console.log(`Поворот модели: ${rotationAngle}° (${rotationRadians.toFixed(3)} рад)`);
            });
        }

        if (this.controls.lightIntensity) {
            this.controls.lightIntensity.addEventListener('input', (e) => {
                const intensity = parseFloat(e.target.value);
                
                if (this.lights && this.lights.ambient && this.lights.directional && this.lights.point) {
                    this.lights.ambient.intensity = intensity * 0.6;
                    this.lights.directional.intensity = intensity;
                    this.lights.point.intensity = intensity * 0.5;
                    
                    // Убираем автоматическую отправку команд - теперь только по кнопке "Применить к OBS"
                    
                    console.log('Интенсивность света изменена:', intensity);
                }
            });
        }

        if (this.controls.resetLightBtn) {
            this.controls.resetLightBtn.addEventListener('click', () => {
                this.resetLight();
            });
        }

        if (this.controls.fullscreenBtn) {
            this.controls.fullscreenBtn.addEventListener('click', () => {
                this.toggleFullscreen();
            });
        }

        if (this.controls.screenshotBtn) {
            this.controls.screenshotBtn.addEventListener('click', () => {
                this.takeScreenshot();
            });
        }

        if (this.controls.performanceBtn) {
            this.controls.performanceBtn.addEventListener('click', () => {
                this.openPerformancePanel();
            });
        }

        if (this.controls.websocketTestBtn) {
            this.controls.websocketTestBtn.addEventListener('click', () => {
                this.openWebSocketTest();
            });
        }

        if (this.controls.faceCameraBtn) {
            this.controls.faceCameraBtn.addEventListener('click', () => {
                this.faceCamera();
            });
        }
    }

    async loadVRMModel() {
        try {
            const statusBar = document.getElementById('statusBar');
            const loading = document.getElementById('loading');
            
            if (statusBar && !window.IS_OBS_MODE) {
                statusBar.textContent = 'Загрузка VRM модели...';
            }
            
            console.log('Начинаем загрузку VRM модели...');
            let gltf;
            
                            // Проверяем, доступен ли GLTFLoader
            if (typeof THREE.GLTFLoader === 'undefined') {
                console.error('❌ THREE.GLTFLoader не найден!');
                console.log('Доступные свойства THREE:', Object.keys(THREE));
                throw new Error('GLTFLoader не загружен. Проверьте CDN ссылки.');
            }
            
            const basicLoader = new THREE.GLTFLoader();
            gltf = await basicLoader.loadAsync('/public/mSkai_art.vrm');
            console.log('GLTF загружен:', gltf);
            
            console.log('Создаем объект модели...');
            this.vrm = { scene: gltf.scene, update: () => {} };
            console.log('Объект модели создан:', this.vrm);
            
            this.rotationGroup = new THREE.Group();
            this.rotationGroup.add(this.vrm.scene);
            this.scene.add(this.rotationGroup);
            
            this.vrm.scene.position.set(0, 0, 0);
            this.vrm.scene.scale.setScalar(1);
            
            this.rotationGroup.rotation.y = Math.PI;
            console.log('Модель загружена, начальный поворот:', THREE.MathUtils.radToDeg(this.rotationGroup.rotation.y).toFixed(1) + '°');
            
            this.vrm.scene.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });

            // === ВЫВОДИМ ВСЕ BLEND SHAPES (morph targets) ===
            console.log('==== BLEND SHAPES (morph targets) ПО МЕШАМ ====' );
            this.vrm.scene.traverse((child) => {
                if (child.isMesh && child.morphTargetDictionary) {
                    console.log(`Mesh: ${child.name}`);
                    console.log('BlendShapes:', Object.keys(child.morphTargetDictionary));
                }
            });
            // === КОНЕЦ ВЫВОДА ===

            this.scene.add(this.rotationGroup);
            
            if (gltf.animations && gltf.animations.length > 0) {
                console.log('Найдены анимации:', gltf.animations.length);
                this.setupAnimations(gltf.animations);
            } else {
                console.log('Анимации не найдены в модели');
            }

            this.setupBlendShapes();
            this.setupBlinking();
            this.setupMovementAnimations();

            if (loading && !window.IS_OBS_MODE) {
                loading.style.display = 'none';
            }
            
            const blendShapeInfo = this.blendShapes.length > 0 ? ` (${this.blendShapes.length} BlendShapes)` : '';
            const statusText = `VRM модель загружена успешно!${this.animations.length > 0 ? ` (${this.animations.length} анимаций)` : ''}${blendShapeInfo}`;
            
            if (statusBar && !window.IS_OBS_MODE) {
                statusBar.textContent = statusText;
            }
            
            console.log(statusText);
            this.isLoaded = true;

            this.updateInfo();

        } catch (error) {
            console.error('Ошибка загрузки VRM модели:', error);
            console.error('Стек ошибки:', error.stack);
            
            const statusBar = document.getElementById('statusBar');
            if (statusBar && !window.IS_OBS_MODE) {
                statusBar.textContent = 'Ошибка загрузки модели: ' + error.message;
            }
        }
    }

    animate() {
        // Получаем настройки от оптимизатора
        const settings = this.performanceOptimizer ? this.performanceOptimizer.getSettings() : {
            maxFPS: 60
        };
        
        // Ограничиваем FPS
        const targetFrameTime = 1000 / settings.maxFPS;
        const now = performance.now();
        
        if (now - this.lastFrameTime < targetFrameTime) {
        requestAnimationFrame(() => this.animate());
            return;
        }
        
        this.lastFrameTime = now;
        requestAnimationFrame(() => this.animate());
        
        const delta = this.clock.getDelta();
        
        try {
            // Обновляем новую систему анимаций
            if (this.animationIntegration) {
                this.animationIntegration.update(delta);
            }
            
        if (this.vrm && this.isLoaded) {
            this.vrm.update(delta);
            this.updateLipsync(delta);
        }
        if (this.mixer) {
            this.mixer.update(delta);
        }
        if (this.movementMixer && !this.pauseAnimation) {
            this.movementMixer.update(delta);
        }
        this.updateInfo();
        this.applyLimbControls();
        this.renderer.render(this.scene, this.camera);
        } catch (error) {
            console.error('❌ Ошибка в animate loop:', error);
        }
    }

    updateInfo() {
        // В режиме OBS не обновляем информационную панель
        if (window.IS_OBS_MODE) {
            return;
        }

        const resolution = document.getElementById('resolution');
        const fps = document.getElementById('fps');
        const status = document.getElementById('status');
        
        if (resolution) {
            resolution.textContent = `${window.innerWidth}x${window.innerHeight}`;
        }
        
        if (fps) {
            this.frameCount++;
            const now = Date.now();
            if (now - this.lastFpsUpdate > 1000) {
                this.currentFPS = Math.round(this.frameCount / ((now - this.lastFpsUpdate) / 1000));
                fps.textContent = this.currentFPS;
                this.lastFpsUpdate = now;
                this.frameCount = 0;
            }
        }
        
        if (status) {
            status.textContent = this.isLoaded ? 'Готово к трансляции' : 'Загрузка...';
        }
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    takeScreenshot() {
        this.renderer.render(this.scene, this.camera);
        const canvas = this.renderer.domElement;
        const link = document.createElement('a');
        link.download = 'vrm-screenshot.png';
        link.href = canvas.toDataURL();
        link.click();
    }

    openPerformancePanel() {
        window.open('performance-panel.html', '_blank', 'width=800,height=600');
    }

    openWebSocketTest() {
        window.open('websocket-debug.html', '_blank', 'width=900,height=700');
    }

    setupAnimations(animations) {
        this.animations = animations;
        this.mixer = new THREE.AnimationMixer(this.vrm.scene);
        this.createAnimationControls();
    }

    createAnimationControls() {
        // Проверяем, находимся ли мы в режиме OBS
        if (window.IS_OBS_MODE) {
            return;
        }

        const controlsContainer = document.querySelector('.controls');
        if (!controlsContainer) {
            return;
        }
        
        if (this.animations.length > 0) {
            const animationGroup = document.createElement('div');
            animationGroup.className = 'control-group';
            animationGroup.innerHTML = `
                <label for="animationSelect">Анимации:</label>
                <select id="animationSelect">
                    <option value="">Без анимации</option>
                    ${this.animations.map((anim, index) => 
                        `<option value="${index}">${anim.name || `Анимация ${index + 1}`}</option>`
                    ).join('')}
                </select>
            `;
            
            const existingGroups = controlsContainer.querySelectorAll('.control-group');
            const insertAfter = existingGroups[existingGroups.length - 1];
            controlsContainer.insertBefore(animationGroup, insertAfter.nextSibling);
            
            this.setupAnimationEventHandlers();
        }
    }

    setupAnimationEventHandlers() {
        const animationSelect = document.getElementById('animationSelect');
        if (animationSelect) {
            animationSelect.addEventListener('change', (e) => {
                const selectedIndex = parseInt(e.target.value);
                if (selectedIndex >= 0 && selectedIndex < this.animations.length) {
                    this.playAnimation(selectedIndex);
                } else {
                    this.stopAnimation();
                }
            });
        }
    }

    playAnimation(index) {
        if (this.currentAnimation) {
            this.mixer.stopAllAction();
        }
        
        const animation = this.animations[index];
        this.currentAnimation = this.mixer.clipAction(animation);
        this.currentAnimation.play();
        
        console.log(`Воспроизводится анимация: ${animation.name || `Анимация ${index + 1}`}`);
    }

    stopAnimation() {
        if (this.currentAnimation) {
            this.mixer.stopAllAction();
            this.currentAnimation = null;
            console.log('Анимация остановлена');
        }
    }

    setupBlendShapes() {
        console.log('Настройка BlendShapes...');
        
        this.blendShapes = [];
        this.vrm.scene.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                this.blendShapes.push(child);
                console.log(`Найден меш с BlendShapes: ${child.name}`);
            }
        });
        
        console.log(`Найдено ${this.blendShapes.length} мешей с BlendShapes`);
        this.createEmotionButtons();
    }

    findEyeBlendShapes() {
        console.log('🔍 Автоматический поиск blend shapes для моргания...');
        
        const eyeKeywords = ['eye', 'blink', 'close', 'lid', 'eyelid', 'brow', 'eyebrow'];
        
        const foundEyeShapes = this.findBlendShapesByKeywords(eyeKeywords);
        
        if (foundEyeShapes.length > 0) {
            console.log('✅ Найдены потенциальные blend shapes для глаз:', foundEyeShapes);
            
            console.log('📋 Список найденных blend shapes для глаз:');
            foundEyeShapes.forEach((shape, index) => {
                console.log(`${index + 1}. ${shape.mesh} -> ${shape.blendShape}`);
            });
        } else {
            console.log('❌ Blend shapes для глаз не найдены');
        }
    }

    findBlendShapesByKeywords(keywords) {
        console.log('🔍 Поиск blend shapes по ключевым словам:', keywords);
        
        if (!this.blendShapes || this.blendShapes.length === 0) {
            console.log('❌ BlendShapes не найдены в модели');
            return [];
        }
        
        const foundShapes = [];
        
        this.blendShapes.forEach(mesh => {
            if (mesh.morphTargetDictionary) {
                const blendShapeNames = Object.keys(mesh.morphTargetDictionary);
                
                blendShapeNames.forEach(blendShapeName => {
                    const lowerName = blendShapeName.toLowerCase();
                    const isMatch = keywords.some(keyword => 
                        lowerName.includes(keyword.toLowerCase())
                    );
                    
                    if (isMatch) {
                        foundShapes.push({
                            mesh: mesh.name,
                            blendShape: blendShapeName,
                            index: mesh.morphTargetDictionary[blendShapeName]
                        });
                    }
                });
            }
        });
        
        console.log(`✅ Найдено ${foundShapes.length} blend shapes по ключевым словам:`, foundShapes);
        return foundShapes;
    }

    setupBlinking() {
        console.log('Настройка автоматического моргания...');
        
        let leftEyeClose = null;
        let rightEyeClose = null;
        
        const eyeBlendShapes = [
            'Fcl_ALL_Sorrow',
            'Fcl_ALL_Angry',
            'Fcl_EYE_Close_L', 'Fcl_EYE_Close_R',
            'Fcl_EYE_Close',
            'Eye_Close_L', 'Eye_Close_R',
            'Eye_Close',
            'Blink_L', 'Blink_R',
            'Blink',
            'EyeBlink_L', 'EyeBlink_R',
            'EyeBlink',
            'Eyes_Close_L', 'Eyes_Close_R',
            'Eyes_Close'
        ];
        
        this.blendShapes.forEach(mesh => {
            eyeBlendShapes.forEach(blendShapeName => {
                if (mesh.morphTargetDictionary[blendShapeName]) {
                    if (blendShapeName === 'Fcl_ALL_Sorrow') {
                        leftEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                        rightEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                        console.log(`✅ Найден правильный blend shape для моргания: ${blendShapeName}`);
                    } else if (blendShapeName.includes('_L') || blendShapeName.includes('Left')) {
                        leftEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                    } else if (blendShapeName.includes('_R') || blendShapeName.includes('Right')) {
                        rightEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                    } else if (!leftEyeClose && !rightEyeClose) {
                        leftEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                        rightEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                    }
                }
            });
        });
        
        console.log('Найденные blend shapes для глаз:', {
            leftEyeClose: leftEyeClose ? `${leftEyeClose.mesh.name}[${leftEyeClose.index}]` : 'не найден',
            rightEyeClose: rightEyeClose ? `${rightEyeClose.mesh.name}[${rightEyeClose.index}]` : 'не найден'
        });
        
        if (!leftEyeClose || !rightEyeClose) {
            console.log('Поиск альтернативных blend shapes для глаз...');
            const eyeKeywords = ['eye', 'blink', 'close', 'lid', 'eyelid'];
            
            this.blendShapes.forEach(mesh => {
                const blendShapeNames = Object.keys(mesh.morphTargetDictionary);
                blendShapeNames.forEach(blendShapeName => {
                    const lowerName = blendShapeName.toLowerCase();
                    const isEyeRelated = eyeKeywords.some(keyword => lowerName.includes(keyword));
                    
                    if (isEyeRelated) {
                        if (!leftEyeClose) {
                            leftEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                            console.log(`Найден левый глаз: ${mesh.name} -> ${blendShapeName}`);
                        } else if (!rightEyeClose) {
                            rightEyeClose = { mesh, index: mesh.morphTargetDictionary[blendShapeName] };
                            console.log(`Найден правый глаз: ${mesh.name} -> ${blendShapeName}`);
                        }
                    }
                });
            });
        }
        
        this.eyeBlendShapes = { leftEyeClose, rightEyeClose };
        
        if (leftEyeClose && rightEyeClose) {
            console.log('✅ Blend shapes для моргания найдены и настроены');
            
            const performBlink = () => {
                if (this.isBlinking) return;
                
                console.log('Выполняется автоматическое моргание');
                
                const closeEyes = () => {
                    this.blendShapes.forEach(mesh => {
                        const index = mesh.morphTargetDictionary['Fcl_EYE_Close'];
                        if (index !== undefined) {
                            mesh.morphTargetInfluences[index] = 0.7;
                        }
                    });
                    this.isBlinking = true;
                };
                
                const openEyes = () => {
                    this.blendShapes.forEach(mesh => {
                        const index = mesh.morphTargetDictionary['Fcl_EYE_Close'];
                        if (index !== undefined) {
                            mesh.morphTargetInfluences[index] = 0;
                        }
                    });
                    this.isBlinking = false;
                };
                
                closeEyes();
                setTimeout(openEyes, 150);
            };
            
            this.blinkInterval = setInterval(performBlink, Math.random() * 4000 + 3000);
        } else {
            console.log('❌ Blend shapes для моргания не найдены');
        }
    }

    manualBlink() {
        console.log('Ручное моргание');
        
        if (!this.vrm || !this.blendShapes || this.blendShapes.length === 0) {
            console.log('VRM модель не загружена или BlendShapes не найдены');
            return;
        }
        
        const closeEyes = () => {
            this.blendShapes.forEach(mesh => {
                const index = mesh.morphTargetDictionary['Fcl_EYE_Close'];
                if (index !== undefined) {
                    mesh.morphTargetInfluences[index] = 0.7;
                }
            });
        };
        
        const openEyes = () => {
            this.blendShapes.forEach(mesh => {
                const index = mesh.morphTargetDictionary['Fcl_EYE_Close'];
                if (index !== undefined) {
                    mesh.morphTargetInfluences[index] = 0;
                }
            });
        };
        
        closeEyes();
        setTimeout(openEyes, 150);
    }

    createEmotionButtons() {
        // Проверяем, находимся ли мы в режиме OBS
        if (window.IS_OBS_MODE) {
            return;
        }

        const controlsContainer = document.querySelector('.controls');
        if (!controlsContainer) {
            return;
        }
        
        const emotionGroup = document.createElement('div');
        emotionGroup.className = 'control-group';
        emotionGroup.innerHTML = `
            <h3 style="margin: 10px 0 5px 0; color: #fff;">😊 Эмоции</h3>
            <button class="btn" data-action="setEmotion" data-emotion="happy">😊 Радость</button>
            <button class="btn" data-action="setEmotion" data-emotion="sad">😢 Грусть</button>
            <button class="btn" data-action="setEmotion" data-emotion="angry">😠 Злость</button>
            <button class="btn" data-action="setEmotion" data-emotion="surprised">😲 Удивление</button>
            <button class="btn" data-action="setEmotion" data-emotion="wink">😉 Подмигивание</button>
            <button class="btn" data-action="setEmotion" data-emotion="blink">😴 Моргание</button>
            <button class="btn" data-action="manualBlink">👁️ Моргнуть сейчас</button>
            <button class="btn" data-action="resetEmotions">🔄 Сбросить эмоции</button>
        `;
        
        const existingGroups = controlsContainer.querySelectorAll('.control-group');
        const insertAfter = existingGroups[existingGroups.length - 1];
        controlsContainer.insertBefore(emotionGroup, insertAfter.nextSibling);
    }

    applyEmotion(emotionName) {
        // Используем новую систему blend shapes
        if (this.animationIntegration) {
            const result = this.animationIntegration.applyEmotion(emotionName);
            // Сохраняем состояние
            this.currentEmotion = emotionName;
            this.saveState();
            return result;
        } else {
            // Fallback к старой системе
        console.log('Применяем эмоцию:', emotionName);
        
        if (!this.vrm || !this.blendShapes || this.blendShapes.length === 0) {
            console.log('VRM модель не загружена или BlendShapes не найдены');
            return;
        }
        
        this.resetEmotions();
        
        const emotionBlendShapes = {
            'happy': ['Fcl_ALL_Joy', 'Fcl_ALL_Fun'],
            'sad': ['Fcl_ALL_Sorrow'],
            'angry': ['Fcl_ALL_Angry'],
            'surprised': ['Fcl_ALL_Surprised'],
            'neutral': [], // Нейтральная эмоция - без BlendShapes
            'wink': ['Fcl_EYE_Close_R', 'Fcl_EYE_Close_L'],
            'blink': ['Fcl_EYE_Close']
        };
        
        const blendShapes = emotionBlendShapes[emotionName];
        if (blendShapes) {
            blendShapes.forEach(blendShapeName => {
                this.blendShapes.forEach(mesh => {
                    const index = mesh.morphTargetDictionary[blendShapeName];
                    if (index !== undefined) {
                        mesh.morphTargetInfluences[index] = 1.0;
                        console.log(`Применен BlendShape: ${blendShapeName} к мешу ${mesh.name}`);
                    }
                });
            });
            
            console.log(`Эмоция "${emotionName}" применена`);
                
                // Сохраняем состояние
                this.currentEmotion = emotionName;
                this.saveState();
        } else {
            console.log(`Неизвестная эмоция: ${emotionName}`);
            }
        }
    }

    resetEmotions() {
        console.log('Сбрасываем все эмоции');
        
        if (!this.vrm || !this.blendShapes || this.blendShapes.length === 0) {
            console.log('VRM модель не загружена или BlendShapes не найдены');
            return;
        }
        
        this.blendShapes.forEach(mesh => {
            if (mesh.morphTargetInfluences) {
                mesh.morphTargetInfluences.fill(0);
            }
        });
        
        console.log('Все эмоции сброшены');
    }

    setupMovementAnimations() {
        this.movementMixer = new THREE.AnimationMixer(this.vrm.scene);
        
        const currentRotation = this.rotationGroup ? this.rotationGroup.rotation.y : 0;
        
        this.setNaturalPose();
        
        this.createIdleAnimation();
        this.createTalkingAnimation();
        this.createActiveTalkingAnimation();
        this.createThinkingAnimation();
        this.createGreetingAnimation();
        this.createBreathingAnimation();
        this.createStretchingAnimation();
        this.createSurpriseAnimation();
        this.createExcitementAnimation();
        this.createListeningAnimation();
        this.createHeadMicroMovements();
        
        if (this.rotationGroup) {
            this.rotationGroup.rotation.y = currentRotation;
        }
        
        this.createMovementControls();
        
        this.createArmControls();
        
        // Мигрируем анимации в новую систему
        if (this.animationIntegration) {
            try {
                this.animationIntegration.migrateExistingAnimations();
                console.log('✅ Анимации настроены с новой системой');
            } catch (error) {
                console.error('❌ Ошибка миграции анимаций:', error);
                // Запускаем базовую анимацию через старую систему
        this.playMovement('idle');
            }
        } else {
            console.log('⚠️ Новая система не инициализирована, используем старую');
            this.playMovement('idle');
        }
    }

    setNaturalPose() {
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const leftForeArm = this.findBoneByName('J_Bip_L_LowerArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        const leftHand = this.findBoneByName('J_Bip_L_Hand');
        const rightHand = this.findBoneByName('J_Bip_R_Hand');
        
        const loadedFromStorage = this.loadNaturalPoseFromStorage();
        
        if (this.naturalPose && loadedFromStorage) {
            if (leftArm) leftArm.rotation.copy(this.naturalPose.leftArm);
            if (rightArm) rightArm.rotation.copy(this.naturalPose.rightArm);
            if (leftForeArm) leftForeArm.rotation.copy(this.naturalPose.leftForeArm);
            if (rightForeArm) rightForeArm.rotation.copy(this.naturalPose.rightForeArm);
            if (leftHand) leftHand.rotation.copy(this.naturalPose.leftHand);
            if (rightHand) rightHand.rotation.copy(this.naturalPose.rightHand);
            
            console.log('Установлена сохраненная естественная поза');
        } else {
            if (leftArm) leftArm.rotation.set(0, 0, 1.35);
            if (rightArm) rightArm.rotation.set(0, 0, -1.35);
            if (leftForeArm) leftForeArm.rotation.set(0, 0, 0);
            if (rightForeArm) rightForeArm.rotation.set(0, 0, 0);
            if (leftHand) leftHand.rotation.set(0, 0, 0);
            if (rightHand) rightHand.rotation.set(0, 0, 0);
            
            console.log('Установлена базовая естественная поза');
        }
    }

    createIdleAnimation() {
        const idleAnimation = new THREE.AnimationClip('idle', 4, []);

        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const spine = this.findBoneByName('J_Bip_C_Spine'); // добавим дыхание

        if (leftArm && rightArm) {
            const leftArmTrack = new THREE.VectorKeyframeTrack(
                `${leftArm.name}.rotation[x]`,
                [0, 1, 2, 3, 4],
                [0, 0.03, 0, -0.03, 0]
            );

            const rightArmTrack = new THREE.VectorKeyframeTrack(
                `${rightArm.name}.rotation[x]`,
                [0, 1, 2, 3, 4],
                [0, -0.03, 0, 0.03, 0]
            );

            idleAnimation.tracks.push(leftArmTrack, rightArmTrack);
        }

        // === Лёгкое дыхание (scale по Y для позвоночника) ===
        if (spine) {
            const spineBreathTrack = new THREE.VectorKeyframeTrack(
                `${spine.name}.scale[y]`,
                [0, 1, 2, 3, 4],
                [1, 1.008, 1, 0.992, 1] // очень небольшая амплитуда
            );
            idleAnimation.tracks.push(spineBreathTrack);
        }

        this.movementAnimations['idle'] = idleAnimation;
        console.log('Анимация ожидания создана с лёгким дыханием');
    }

    createTalkingAnimation() {
        const talkingAnimation = new THREE.AnimationClip('talking', 3, []);
        
        const head = this.findBoneByName('J_Bip_C_Head');
        const neck = this.findBoneByName('J_Bip_C_Neck');
        
        if (head) {
            // Простые микродвижения головы во время разговора
            const headTiltTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[z]`,
                [0, 0.5, 1, 1.5, 2, 2.5, 3],
                [0, 0.005, -0.003, 0.008, -0.005, 0.003, 0]
            );
            
            const headNodTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[x]`,
                [0, 0.75, 1.5, 2.25, 3],
                [0, 0.003, -0.001, 0.005, 0]
            );
            
            talkingAnimation.tracks.push(headTiltTrack, headNodTrack);
        }
        
        if (neck) {
            // Соответствующие микродвижения шеи
            const neckTiltTrack = new THREE.VectorKeyframeTrack(
                `${neck.name}.rotation[z]`,
                [0, 0.5, 1, 1.5, 2, 2.5, 3],
                [0, 0.003, -0.002, 0.004, -0.003, 0.002, 0]
            );
            
            talkingAnimation.tracks.push(neckTiltTrack);
        }
        
        this.movementAnimations['talking'] = talkingAnimation;
        console.log('Анимация разговора создана - простые микродвижения');
    }

    createActiveTalkingAnimation() {
        const activeTalkingAnimation = new THREE.AnimationClip('activeTalking_move', 2, []);
        
        const head = this.findBoneByName('J_Bip_C_Head');
        const neck = this.findBoneByName('J_Bip_C_Neck');
        
        if (head) {
            // Более активные движения головы для эмоциональной речи
            const headTiltTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[z]`,
                [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
                [0, 0.01, -0.005, 0.015, -0.01, 0.005, -0.015, 0.01, 0]
            );
            
            const headNodTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[x]`,
                [0, 0.5, 1, 1.5, 2],
                [0, 0.008, -0.003, 0.012, 0]
            );
            
            activeTalkingAnimation.tracks.push(headTiltTrack, headNodTrack);
        }
        
        if (neck) {
            // Соответствующие движения шеи для активной речи
            const neckTiltTrack = new THREE.VectorKeyframeTrack(
                `${neck.name}.rotation[z]`,
                [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
                [0, 0.006, -0.003, 0.008, -0.005, 0.003, -0.008, 0.005, 0]
            );
            
            activeTalkingAnimation.tracks.push(neckTiltTrack);
        }
        
        this.movementAnimations['activeTalking_move'] = activeTalkingAnimation;
        console.log('Анимация активного разговора создана');
    }

    createThinkingAnimation() {
        const thinkingAnimation = new THREE.AnimationClip('thinking_move', 4, []);
        
        // Находим кости головы и шеи
        const head = this.findBoneByName('J_Bip_C_Head');
        const neck = this.findBoneByName('J_Bip_C_Neck');
        const spine = this.findBoneByName('J_Bip_C_Spine');
        
        // Анимация наклона головы вбок (как при размышлении)
        if (head) {
            // Наклон головы влево-вправо (Z-ось) - УМЕНЬШЕННАЯ АМПЛИТУДА
            const headTiltTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[z]`,
                [0, 1, 2, 3, 4],
                [0, 0.05, -0.03, 0.04, 0]
            );
            
            // Легкий наклон головы вперед (X-ось) - УМЕНЬШЕННАЯ АМПЛИТУДА
            const headForwardTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[x]`,
                [0, 1, 2, 3, 4],
                [0, 0.02, 0.03, 0.02, 0]
            );
            
            // Легкое покачивание головой (Y-ось) - УМЕНЬШЕННАЯ АМПЛИТУДА
            const headNodTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[y]`,
                [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4],
                [0, 0.01, -0.005, 0.015, -0.01, 0.005, -0.015, 0.01, 0]
            );
            
            thinkingAnimation.tracks.push(headTiltTrack, headForwardTrack, headNodTrack);
        }
        
        // Анимация шеи (если найдена) - УМЕНЬШЕННАЯ АМПЛИТУДА
        if (neck) {
            // Легкое движение шеи в такт с головой
            const neckTiltTrack = new THREE.VectorKeyframeTrack(
                `${neck.name}.rotation[z]`,
                [0, 1, 2, 3, 4],
                [0, 0.03, -0.02, 0.025, 0]
            );
            
            const neckForwardTrack = new THREE.VectorKeyframeTrack(
                `${neck.name}.rotation[x]`,
                [0, 1, 2, 3, 4],
                [0, 0.015, 0.025, 0.015, 0]
            );
            
            thinkingAnimation.tracks.push(neckTiltTrack, neckForwardTrack);
        }
        
        // Анимация позвоночника для более естественного движения - УМЕНЬШЕННАЯ АМПЛИТУДА
        if (spine) {
            const spineTrack = new THREE.VectorKeyframeTrack(
                `${spine.name}.rotation[x]`,
                [0, 1, 2, 3, 4],
                [0, 0.01, 0.015, 0.01, 0]
            );
            
            thinkingAnimation.tracks.push(spineTrack);
        }
        
        // Сохраняем анимацию рук (как было) - УМЕНЬШЕННАЯ АМПЛИТУДА
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        const rightHand = this.findBoneByName('J_Bip_R_Hand');
        
        if (rightArm && rightForeArm && rightHand) {
            const armTrack = new THREE.VectorKeyframeTrack(
                `${rightArm.name}.rotation[x]`,
                [0, 1.5, 3, 4],
                [0, -0.3, -0.3, 0]
            );
            
            const foreArmTrack = new THREE.VectorKeyframeTrack(
                `${rightForeArm.name}.rotation[x]`,
                [0, 1.5, 3, 4],
                [0, -0.2, -0.2, 0]
            );
            
            thinkingAnimation.tracks.push(armTrack, foreArmTrack);
        }
        
        this.movementAnimations['thinking_move'] = thinkingAnimation;
        console.log('Улучшенная анимация размышления создана (с движениями головы и шеи) - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createGreetingAnimation() {
        const greetingAnimation = new THREE.AnimationClip('greeting_move', 2, []);
        
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        
        if (rightArm && rightForeArm) {
            const armTrack = new THREE.VectorKeyframeTrack(
                `${rightArm.name}.rotation[x]`,
                [0, 0.5, 1, 1.5, 2],
                [0, -0.5, -0.5, 0, 0]
            );
            
            const foreArmTrack = new THREE.VectorKeyframeTrack(
                `${rightForeArm.name}.rotation[x]`,
                [0, 0.5, 1, 1.5, 2],
                [0, -0.25, -0.25, 0, 0]
            );
            
            greetingAnimation.tracks.push(armTrack, foreArmTrack);
        }
        
        this.movementAnimations['greeting_move'] = greetingAnimation;
        console.log('Анимация приветствия создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createBreathingAnimation() {
        const breathingAnimation = new THREE.AnimationClip('breathing', 3, []);
        
        const spine = this.findBoneByName('J_Bip_C_Spine');
        
        if (spine) {
            const spineTrack = new THREE.VectorKeyframeTrack(
                '.scale[y]',
                [0, 1.5, 3],
                [1, 1.01, 1]
            );
            
            breathingAnimation.tracks.push(spineTrack);
        }
        
        this.movementAnimations['breathing'] = breathingAnimation;
        console.log('Анимация дыхания создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createStretchingAnimation() {
        const stretchingAnimation = new THREE.AnimationClip('stretching', 3, []);
        
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        
        if (leftArm && rightArm) {
            const leftArmTrack = new THREE.VectorKeyframeTrack(
                `${leftArm.name}.rotation[x]`,
                [0, 1.5, 3],
                [0, -0.5, 0]
            );
            
            const rightArmTrack = new THREE.VectorKeyframeTrack(
                `${rightArm.name}.rotation[x]`,
                [0, 1.5, 3],
                [0, -0.5, 0]
            );
            
            stretchingAnimation.tracks.push(leftArmTrack, rightArmTrack);
        }
        
        this.movementAnimations['stretching'] = stretchingAnimation;
        console.log('Анимация растяжки создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createSurpriseAnimation() {
        const surpriseAnimation = new THREE.AnimationClip('surprise_move', 1, []);
        
        const head = this.findBoneByName('J_Bip_C_Head');
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        
        if (head) {
            const headTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[y]`,
                [0, 0.5, 1],
                [0, 0.1, 0]
            );
            
            surpriseAnimation.tracks.push(headTrack);
        }
        
        if (leftArm && rightArm) {
            const leftArmTrack = new THREE.VectorKeyframeTrack(
                `${leftArm.name}.rotation[x]`,
                [0, 0.5, 1],
                [0, -0.3, 0]
            );
            
            const rightArmTrack = new THREE.VectorKeyframeTrack(
                `${rightArm.name}.rotation[x]`,
                [0, 0.5, 1],
                [0, -0.3, 0]
            );
            
            surpriseAnimation.tracks.push(leftArmTrack, rightArmTrack);
        }
        
        this.movementAnimations['surprise_move'] = surpriseAnimation;
        console.log('Анимация удивления создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createExcitementAnimation() {
        const excitementAnimation = new THREE.AnimationClip('excitement_move', 2, []);
        
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        
        if (leftArm && rightArm) {
            const leftArmTrack = new THREE.VectorKeyframeTrack(
                `${leftArm.name}.rotation[x]`,
                [0, 0.5, 1, 1.5, 2],
                [0, -0.4, 0, -0.4, 0]
            );
            
            const rightArmTrack = new THREE.VectorKeyframeTrack(
                `${rightArm.name}.rotation[x]`,
                [0, 0.5, 1, 1.5, 2],
                [0, -0.4, 0, -0.4, 0]
            );
            
            excitementAnimation.tracks.push(leftArmTrack, rightArmTrack);
        }
        
        this.movementAnimations['excitement_move'] = excitementAnimation;
        console.log('Анимация волнения создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createListeningAnimation() {
        const listeningAnimation = new THREE.AnimationClip('listening', 4, []);
        
        const head = this.findBoneByName('J_Bip_C_Head');
        const spine = this.findBoneByName('J_Bip_C_Spine');
        
        if (head) {
            const headTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[y]`,
                [0, 1, 2, 3, 4],
                [0, 0.03, 0, -0.03, 0]
            );
            
            listeningAnimation.tracks.push(headTrack);
        }
        
        if (spine) {
            const spineTrack = new THREE.VectorKeyframeTrack(
                `${spine.name}.rotation[x]`,
                [0, 2, 4],
                [0, 0.03, 0]
            );
            
            listeningAnimation.tracks.push(spineTrack);
        }
        
        this.movementAnimations['listening'] = listeningAnimation;
        console.log('Анимация слушания создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    createHeadMicroMovements() {
        const microMovementsAnimation = new THREE.AnimationClip('headMicroMovements', 6, []);
        
        const head = this.findBoneByName('J_Bip_C_Head');
        const neck = this.findBoneByName('J_Bip_C_Neck');
        
        if (head) {
            // Очень легкие микродвижения головы для естественности - УМЕНЬШЕННАЯ АМПЛИТУДА
            const headMicroTiltTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[z]`,
                [0, 1, 2, 3, 4, 5, 6],
                [0, 0.008, -0.004, 0.012, -0.008, 0.004, 0]
            );
            
            const headMicroNodTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[x]`,
                [0, 1.5, 3, 4.5, 6],
                [0, 0.005, -0.002, 0.008, 0]
            );
            
            const headMicroTurnTrack = new THREE.VectorKeyframeTrack(
                `${head.name}.rotation[y]`,
                [0, 2, 4, 6],
                [0, 0.003, -0.005, 0]
            );
            
            microMovementsAnimation.tracks.push(headMicroTiltTrack, headMicroNodTrack, headMicroTurnTrack);
        }
        
        if (neck) {
            // Соответствующие микродвижения шеи - УМЕНЬШЕННАЯ АМПЛИТУДА
            const neckMicroTiltTrack = new THREE.VectorKeyframeTrack(
                `${neck.name}.rotation[z]`,
                [0, 1, 2, 3, 4, 5, 6],
                [0, 0.004, -0.002, 0.006, -0.004, 0.002, 0]
            );
            
            const neckMicroNodTrack = new THREE.VectorKeyframeTrack(
                `${neck.name}.rotation[x]`,
                [0, 1.5, 3, 4.5, 6],
                [0, 0.003, -0.001, 0.004, 0]
            );
            
            microMovementsAnimation.tracks.push(neckMicroTiltTrack, neckMicroNodTrack);
        }
        
        this.movementAnimations['headMicroMovements'] = microMovementsAnimation;
        console.log('Анимация микродвижений головы создана - УМЕНЬШЕННАЯ АМПЛИТУДА');
    }

    findBoneByName(name) {
        if (!this.vrm || !this.vrm.scene) return null;
        let foundBone = null;
        this.vrm.scene.traverse((child) => {
            if (child.isBone && child.name === name) {
                foundBone = child;
            }
        });
        return foundBone;
    }

    createMovementControls() {
        // Проверяем, находимся ли мы в режиме OBS
        if (window.IS_OBS_MODE) {
            return;
        }

        const controlsContainer = document.querySelector('.controls');
        if (!controlsContainer) {
            return;
        }
        
        const movementGroup = document.createElement('div');
        movementGroup.className = 'control-group';
        movementGroup.innerHTML = `
            <label for="movementSelect">Движения:</label>
            <select id="movementSelect">
                <option value="idle">Ожидание</option>
                <option value="talking">Разговор</option>
                <option value="activeTalking_move">Активный разговор</option>
                <option value="thinking_move">Размышление</option>
                <option value="greeting_move">Приветствие</option>
                <option value="breathing">Дыхание</option>
                <option value="stretching">Растяжка</option>
                <option value="surprise_move">Удивление</option>
                <option value="excitement_move">Волнение</option>
                <option value="listening">Слушание</option>
                <option value="headMicroMovements">Микродвижения головы</option>
            </select>
        `;
        
        const existingGroups = controlsContainer.querySelectorAll('.control-group');
        const insertAfter = existingGroups[existingGroups.length - 1];
        controlsContainer.insertBefore(movementGroup, insertAfter.nextSibling);
        
        const movementSelect = document.getElementById('movementSelect');
        if (movementSelect) {
            movementSelect.addEventListener('change', (e) => {
                this.playMovement(e.target.value);
            });
        }
    }

    playMovement(movementName) {
        // Используем новую систему приоритетов
        if (this.animationIntegration) {
            const result = this.animationIntegration.playMovement(movementName);
            // Сохраняем состояние
            this.saveState();
            return result;
        } else {
            // Fallback к старой системе
        if (this.currentMovement) {
            this.movementMixer.stopAllAction();
        }
        
        const animation = this.movementAnimations[movementName];
        if (animation) {
            this.currentMovement = this.movementMixer.clipAction(animation);
            this.currentMovement.play();
                this.currentMovement = movementName;
            console.log(`Воспроизводится движение: ${movementName}`);
                
                // Сохраняем состояние
                this.saveState();
        } else {
            console.log(`Движение "${movementName}" не найдено`);
            }
        }
    }

    resetLight() {
        if (this.lights) {
            this.lights.ambient.intensity = 0.6;
            this.lights.directional.intensity = 1.0;
            this.lights.point.intensity = 0.5;
            
            if (this.controls.lightIntensity) {
                this.controls.lightIntensity.value = 1.0;
            }
            
            console.log('Освещение сброшено к значениям по умолчанию');
        }
    }

    faceCamera() {
        if (this.rotationGroup) {
            this.rotationGroup.rotation.y = 0;
            
            if (this.controls.rotationSpeed) {
                this.controls.rotationSpeed.value = 0;
            }
            
            console.log('Модель повернута лицом к камере');
        }
    }

    resetAllBones() {
        console.log('🔄 Сброс костей рук в исходное положение...');
        
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const leftForeArm = this.findBoneByName('J_Bip_L_LowerArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        const leftHand = this.findBoneByName('J_Bip_L_Hand');
        const rightHand = this.findBoneByName('J_Bip_R_Hand');
        
        if (leftArm) leftArm.rotation.set(0, 0, 0.3);
        if (rightArm) rightArm.rotation.set(0, 0, -0.3);
        if (leftForeArm) leftForeArm.rotation.set(0, 0, 0);
        if (rightForeArm) rightForeArm.rotation.set(0, 0, 0);
        if (leftHand) leftHand.rotation.set(0, 0, 0);
        if (rightHand) rightHand.rotation.set(0, 0, 0);
        
        // Обновляем ползунки
        this.updateArmControlSliders();
        
        console.log('✅ Кости рук сброшены в естественную позу');
    }

    createArmControls() {
        // Проверяем, находимся ли мы в режиме OBS
        if (window.IS_OBS_MODE) {
            return;
        }

        // Вставляем bone controls в основную панель управления
        const controlsContainer = document.querySelector('.controls');
        if (!controlsContainer) {
            return;
        }
        
        const armGroup = document.createElement('div');
        armGroup.className = 'control-group';
        // --- ЧЕКБОКС ПАУЗЫ АНИМАЦИИ ---
        const pauseAnimId = 'pauseAnimationCheckbox';
        armGroup.innerHTML = `
            <div style=\"margin-bottom:10px;\">
                <label style=\"font-size:15px;display:flex;align-items:center;gap:7px;\">
                    <input type=\"checkbox\" id=\"${pauseAnimId}\" style=\"width:18px;height:18px;\">
                    ⏸️ Пауза анимации
                </label>
            </div>
            <style>
            .btn-mini { font-size: 15px; padding: 4px 12px; border-radius: 3px; border: 1px solid #ccc; background: #f8f8ff; cursor: pointer; }
            .btn-mini:active { background: #e0e0ff; }
            .btn-reset { color: #a00; border-color: #a00; background: #fff0f0; }
            .arm-section { margin-bottom: 14px; }
            .arm-controls, .leg-controls, .body-controls { margin-bottom: 16px; display: flex; flex-direction: column; gap: 0; }
            .control-group { max-width: 400px; overflow-y: auto; max-height: 70vh; }
            input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
            input[type=number] { -moz-appearance: textfield; }
            </style>
            <h3 style=\"margin: 10px 0 5px 0; color: #223; font-size:15px;\">🧍 Корпус и голова</h3>
            <div class=\"body-controls\">
                <div class=\"arm-section\">${boneControlHtml('head', 'Голова')}</div>
                <div class=\"arm-section\">${boneControlHtml('neck', 'Шея')}</div>
                <div class=\"arm-section\">${boneControlHtml('chest', 'Грудная клетка')}</div>
                <div class=\"arm-section\">${boneControlHtml('hips', 'Таз')}</div>
                <div class=\"arm-section\">${boneControlHtml('leftShoulder', 'Левое плечо')}</div>
                <div class=\"arm-section\">${boneControlHtml('rightShoulder', 'Правое плечо')}</div>
            </div>
            <h3 style=\"margin: 10px 0 5px 0; color: #223; font-size:15px;\">🦾 Руки</h3>
            <div class=\"arm-controls\">
                <div class=\"arm-section\">
                    <h4 style=\"margin-bottom:4px; font-size:11px;\">Левая рука</h4>
                    ${boneControlHtml('leftArm', 'Плечо')}
                    ${boneControlHtml('leftForeArm', 'Локоть')}
                    ${boneControlHtml('leftHand', 'Кисть')}
                </div>
                <div class=\"arm-section\">
                    <h4 style=\"margin-bottom:4px; font-size:11px;\">Правая рука</h4>
                    ${boneControlHtml('rightArm', 'Плечо')}
                    ${boneControlHtml('rightForeArm', 'Локоть')}
                    ${boneControlHtml('rightHand', 'Кисть')}
                </div>
            </div>
            <h3 style=\"margin: 16px 0 5px 0; color: #223; font-size:15px;\">🦿 Ноги</h3>
            <div class=\"leg-controls\">
                <div class=\"arm-section\">
                    <h4 style=\"margin-bottom:4px; font-size:11px;\">Левая нога</h4>
                    ${boneControlHtml('leftLeg', 'Бедро')}
                    ${boneControlHtml('leftLowerLeg', 'Голень')}
                    ${boneControlHtml('leftFoot', 'Стопа')}
                </div>
                <div class=\"arm-section\">
                    <h4 style=\"margin-bottom:4px; font-size:11px;\">Правая нога</h4>
                    ${boneControlHtml('rightLeg', 'Бедро')}
                    ${boneControlHtml('rightLowerLeg', 'Голень')}
                    ${boneControlHtml('rightFoot', 'Стопа')}
                </div>
            </div>
            <div class="arm-buttons" style="margin-top:10px;display:grid;grid-template-columns:1fr;gap:6px;">
                <button class="btn" onclick="window.app.resetAllBones()">🔄 Сбросить руки</button>
                <button class="btn" onclick="window.app.saveAsNaturalPose()">💾 Сохранить как естественную позу</button>
                <button class="btn" onclick="window.app.loadSavedPose()">📂 Загрузить сохранённую позу</button>
                <button class="btn" onclick="window.app.resetSavedPose()">🗑️ Сбросить сохраненную позу</button>
                <button class="btn" onclick="window.app.applyToObs()" style="background: #4CAF50; color: white; border-color: #45a049;">📤 Применить к OBS</button>
            </div>
        `;
        controlsContainer.appendChild(armGroup);
        // --- Обработчик чекбокса паузы ---
        const pauseCheckbox = armGroup.querySelector(`#${pauseAnimId}`);
        this.pauseAnimation = false;
        pauseCheckbox.addEventListener('change', (e) => {
            this.pauseAnimation = pauseCheckbox.checked;
            if (this.pauseAnimation) {
                if (this.movementMixer) this.movementMixer.stopAllAction();
            } else {
                // --- ДОБАВЛЕНО: обновить базу костей после ручного редактирования ---
                this.updateBaseBoneRotationsFromCurrentPose();
                if (this.currentMovement) this.currentMovement.play();
            }
        });
        this.setupLimbControlHandlers();
    }

    setupLimbControlHandlers() {
        // Для всех input[type=number] и кнопок +/-/reset
        const axes = ['X','Y','Z'];
        const bones = [
            // Корпус и голова
            'head','neck','chest','hips','leftShoulder','rightShoulder',
            // Левая рука
            'leftArm','leftForeArm','leftHand',
            // Правая рука
            'rightArm','rightForeArm','rightHand',
            // Левая нога
            'leftLeg','leftLowerLeg','leftFoot',
            // Правая нога
            'rightLeg','rightLowerLeg','rightFoot'
        ];
        // input[type=number]
        bones.forEach(bone => {
            axes.forEach(axis => {
                const input = document.getElementById(`${bone}${axis}`);
                if (input) {
                    input.addEventListener('input', () => this.applyLimbControls());
                }
            });
        });
        // Кнопки +/-
        document.querySelectorAll('.btn-mini[data-action="increment"]').forEach(btn => {
            btn.addEventListener('click', e => {
                const bone = btn.getAttribute('data-bone');
                const axis = btn.getAttribute('data-axis');
                const input = document.getElementById(`${bone}${axis}`);
                if (input) {
                    input.value = (parseFloat(input.value) + 0.05).toFixed(2);
                    input.dispatchEvent(new Event('input'));
                }
            });
        });
        document.querySelectorAll('.btn-mini[data-action="decrement"]').forEach(btn => {
            btn.addEventListener('click', e => {
                const bone = btn.getAttribute('data-bone');
                const axis = btn.getAttribute('data-axis');
                const input = document.getElementById(`${bone}${axis}`);
                if (input) {
                    input.value = (parseFloat(input.value) - 0.05).toFixed(2);
                    input.dispatchEvent(new Event('input'));
                }
            });
        });
        // Кнопки reset
        document.querySelectorAll('.btn-reset').forEach(btn => {
            btn.addEventListener('click', e => {
                const bone = btn.getAttribute('data-bone');
                axes.forEach(axis => {
                    const input = document.getElementById(`${bone}${axis}`);
                    if (input) input.value = 0;
                });
                this.applyLimbControls();
            });
        });
    }

    applyLimbControls() {
        if (!this.vrm || !this.vrm.scene) return;
        // Руки
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const leftForeArm = this.findBoneByName('J_Bip_L_LowerArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        const leftHand = this.findBoneByName('J_Bip_L_Hand');
        const rightHand = this.findBoneByName('J_Bip_R_Hand');
        // Ноги
        const leftLeg = this.findBoneByName('J_Bip_L_UpperLeg');
        const rightLeg = this.findBoneByName('J_Bip_R_UpperLeg');
        const leftLowerLeg = this.findBoneByName('J_Bip_L_LowerLeg');
        const rightLowerLeg = this.findBoneByName('J_Bip_R_LowerLeg');
        const leftFoot = this.findBoneByName('J_Bip_L_Foot');
        const rightFoot = this.findBoneByName('J_Bip_R_Foot');
        // Корпус и голова
        const head = this.findBoneByName('J_Bip_C_Head');
        const neck = this.findBoneByName('J_Bip_C_Neck');
        const chest = this.findBoneByName('J_Bip_C_Chest');
        const hips = this.findBoneByName('J_Bip_C_Hips');
        const leftShoulder = this.findBoneByName('J_Bip_L_Shoulder');
        const rightShoulder = this.findBoneByName('J_Bip_R_Shoulder');

        // Список костей и их id для UI
        const bones = [
            { bone: leftArm, prefix: 'leftArm', defZ: 0.3 },
            { bone: rightArm, prefix: 'rightArm', defZ: -0.3 },
            { bone: leftForeArm, prefix: 'leftForeArm' },
            { bone: rightForeArm, prefix: 'rightForeArm' },
            { bone: leftHand, prefix: 'leftHand' },
            { bone: rightHand, prefix: 'rightHand' },
            { bone: leftLeg, prefix: 'leftLeg' },
            { bone: rightLeg, prefix: 'rightLeg' },
            { bone: leftLowerLeg, prefix: 'leftLowerLeg' },
            { bone: rightLowerLeg, prefix: 'rightLowerLeg' },
            { bone: leftFoot, prefix: 'leftFoot' },
            { bone: rightFoot, prefix: 'rightFoot' },
            { bone: head, prefix: 'head' },
            { bone: neck, prefix: 'neck' },
            { bone: chest, prefix: 'chest' },
            { bone: hips, prefix: 'hips' },
            { bone: leftShoulder, prefix: 'leftShoulder' },
            { bone: rightShoulder, prefix: 'rightShoulder' },
        ];

        bones.forEach(({ bone, prefix, defZ }) => {
            if (!bone) return;
            const x = parseFloat(document.getElementById(prefix + 'X')?.value || 0);
            const y = parseFloat(document.getElementById(prefix + 'Y')?.value || 0);
            let z = parseFloat(document.getElementById(prefix + 'Z')?.value || 0);
            if (typeof defZ !== 'undefined' && isNaN(z)) z = defZ;

            if (this.pauseAnimation) {
                // Абсолютное управление
                bone.rotation.set(x, y, z);
                
                // Убираем автоматическую отправку команд - теперь только по кнопке "Применить к OBS"
            } else {
                // --- Новый фикс: offset всегда к базе анимации ---
                if (!this._animationBaseRot) this._animationBaseRot = {};
                if (!this._lastOffset) this._lastOffset = {};
                if (!this._animationBaseRot[prefix]) {
                    this._animationBaseRot[prefix] = { x: 0, y: 0, z: 0 };
                }
                if (!this._lastOffset[prefix]) {
                    this._lastOffset[prefix] = { x: 0, y: 0, z: 0 };
                }
                // Сохраняем "чистую" позу анимации (без offset)
                this._animationBaseRot[prefix].x = bone.rotation.x - this._lastOffset[prefix].x;
                this._animationBaseRot[prefix].y = bone.rotation.y - this._lastOffset[prefix].y;
                this._animationBaseRot[prefix].z = bone.rotation.z - this._lastOffset[prefix].z;
                // Применяем offset к базе
                bone.rotation.x = this._animationBaseRot[prefix].x + x;
                bone.rotation.y = this._animationBaseRot[prefix].y + y;
                bone.rotation.z = this._animationBaseRot[prefix].z + z;
                // Запоминаем offset для следующего кадра
                this._lastOffset[prefix] = { x, y, z };
            }
        });
    }

    resetArmControls() {
        const armControls = [
            'leftArmX', 'leftArmY', 'leftArmZ', 'leftForeArmX', 'leftHandX',
            'rightArmX', 'rightArmY', 'rightArmZ', 'rightForeArmX', 'rightHandX'
        ];
        
        armControls.forEach(controlId => {
            const control = document.getElementById(controlId);
            if (control) {
                if (controlId === 'leftArmZ') control.value = 0.3;
                else if (controlId === 'rightArmZ') control.value = -0.3;
                else control.value = 0;
            }
        });
        
        this.applyArmControls();
    }

    updateArmControlSliders() {
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const leftForeArm = this.findBoneByName('J_Bip_L_LowerArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        const leftHand = this.findBoneByName('J_Bip_L_Hand');
        const rightHand = this.findBoneByName('J_Bip_R_Hand');
        
        if (leftArm) {
            const leftArmX = document.getElementById('leftArmX');
            const leftArmY = document.getElementById('leftArmY');
            const leftArmZ = document.getElementById('leftArmZ');
            if (leftArmX) leftArmX.value = leftArm.rotation.x;
            if (leftArmY) leftArmY.value = leftArm.rotation.y;
            if (leftArmZ) leftArmZ.value = leftArm.rotation.z;
        }
        
        if (rightArm) {
            const rightArmX = document.getElementById('rightArmX');
            const rightArmY = document.getElementById('rightArmY');
            const rightArmZ = document.getElementById('rightArmZ');
            if (rightArmX) rightArmX.value = rightArm.rotation.x;
            if (rightArmY) rightArmY.value = rightArm.rotation.y;
            if (rightArmZ) rightArmZ.value = rightArm.rotation.z;
        }
        
        if (leftForeArm) {
            const leftForeArmX = document.getElementById('leftForeArmX');
            if (leftForeArmX) leftForeArmX.value = leftForeArm.rotation.z;
        }
        
        if (rightForeArm) {
            const rightForeArmX = document.getElementById('rightForeArmX');
            if (rightForeArmX) rightForeArmX.value = rightForeArm.rotation.z;
        }
        
        if (leftHand) {
            const leftHandX = document.getElementById('leftHandX');
            if (leftHandX) leftHandX.value = leftHand.rotation.x;
        }
        
        if (rightHand) {
            const rightHandX = document.getElementById('rightHandX');
            if (rightHandX) rightHandX.value = rightHand.rotation.x;
        }
    }

    saveAsNaturalPose() {
        console.log('💾 Сохранение текущей позы как естественной...');
        
        const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
        const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
        const leftForeArm = this.findBoneByName('J_Bip_L_LowerArm');
        const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
        const leftHand = this.findBoneByName('J_Bip_L_Hand');
        const rightHand = this.findBoneByName('J_Bip_R_Hand');
        
        if (leftArm && rightArm) {
            this.naturalPose = {
                leftArm: leftArm.rotation.clone(),
                rightArm: rightArm.rotation.clone(),
                leftForeArm: leftForeArm ? leftForeArm.rotation.clone() : new THREE.Euler(),
                rightForeArm: rightForeArm ? rightForeArm.rotation.clone() : new THREE.Euler(),
                leftHand: leftHand ? leftHand.rotation.clone() : new THREE.Euler(),
                rightHand: rightHand ? rightHand.rotation.clone() : new THREE.Euler()
            };
            
            try {
                localStorage.setItem('naturalPose', JSON.stringify(this.naturalPose));
                console.log('✅ Естественная поза сохранена в localStorage');
            } catch (error) {
                console.warn('⚠️ Не удалось сохранить позу в localStorage:', error);
            }
        } else {
            console.log('❌ Кости рук не найдены для сохранения позы');
        }
    }

    resetSavedPose() {
        console.log('🗑️ Сброс сохраненной естественной позы...');
        
        try {
            localStorage.removeItem('naturalPose');
            this.naturalPose = null;
            console.log('✅ Сохраненная поза удалена');
        } catch (error) {
            console.warn('⚠️ Не удалось удалить сохраненную позу:', error);
        }
    }

    loadNaturalPoseFromStorage() {
        try {
            const savedPose = localStorage.getItem('naturalPose');
            if (savedPose) {
                this.naturalPose = JSON.parse(savedPose);
                console.log('✅ Естественная поза загружена из localStorage');
                return true;
            }
        } catch (error) {
            console.warn('⚠️ Не удалось загрузить естественную позу:', error);
        }
        return false;
    }

    applyToObs() {
        console.log('📤 Применение всех настроек к OBS...');
        
        // Отправляем текущую позу всех костей
        const bones = [
            { name: 'J_Bip_L_UpperArm', prefix: 'leftArm' },
            { name: 'J_Bip_R_UpperArm', prefix: 'rightArm' },
            { name: 'J_Bip_L_LowerArm', prefix: 'leftForeArm' },
            { name: 'J_Bip_R_LowerArm', prefix: 'rightForeArm' },
            { name: 'J_Bip_L_Hand', prefix: 'leftHand' },
            { name: 'J_Bip_R_Hand', prefix: 'rightHand' },
            { name: 'J_Bip_L_UpperLeg', prefix: 'leftLeg' },
            { name: 'J_Bip_R_UpperLeg', prefix: 'rightLeg' },
            { name: 'J_Bip_L_LowerLeg', prefix: 'leftLowerLeg' },
            { name: 'J_Bip_R_LowerLeg', prefix: 'rightLowerLeg' },
            { name: 'J_Bip_L_Foot', prefix: 'leftFoot' },
            { name: 'J_Bip_R_Foot', prefix: 'rightFoot' },
            { name: 'J_Bip_C_Head', prefix: 'head' },
            { name: 'J_Bip_C_Neck', prefix: 'neck' },
            { name: 'J_Bip_C_Chest', prefix: 'chest' },
            { name: 'J_Bip_C_Hips', prefix: 'hips' },
            { name: 'J_Bip_L_Shoulder', prefix: 'leftShoulder' },
            { name: 'J_Bip_R_Shoulder', prefix: 'rightShoulder' }
        ];
        
        bones.forEach(({ name, prefix }) => {
            const x = parseFloat(document.getElementById(prefix + 'X')?.value || 0);
            const y = parseFloat(document.getElementById(prefix + 'Y')?.value || 0);
            const z = parseFloat(document.getElementById(prefix + 'Z')?.value || 0);
            
            this.sendPoseControl(name, 'x', x);
            this.sendPoseControl(name, 'y', y);
            this.sendPoseControl(name, 'z', z);
        });
        
        // Отправляем настройки камеры
        if (this.controls.cameraDistance) {
            const distance = parseFloat(this.controls.cameraDistance.value);
            this.sendCameraControl('distance', distance);
        }
        
        // Отправляем настройки освещения
        if (this.controls.lightIntensity) {
            const intensity = parseFloat(this.controls.lightIntensity.value);
            this.sendLightControl('intensity', intensity);
        }
        
        console.log('✅ Все настройки применены к OBS');
    }

    setEmotion(emotionName) {
        console.log('Устанавливаем эмоцию:', emotionName);
        this.applyEmotion(emotionName);
    }

    // Новая функция для обновления липсинка с интерполяцией
    updateLipsync(delta) {
        const speed = this.lipsyncLerp.speed;
        
        // Интерполируем значения для плавности
        Object.keys(this.lipsyncBlendShapes).forEach(key => {
            this.lipsyncLerp.current[key] += (this.lipsyncLerp.target[key] - this.lipsyncLerp.current[key]) * speed;
            this.lipsyncBlendShapes[key] = this.lipsyncLerp.current[key];
        });
        // --- Микродрожание губ ---
        const energy = this.lipsyncBlendShapes.energy;
        if (energy > 0.1) {
            // jitter только если рот открыт
            const jitter = (Math.random() - 0.5) * 0.07 * energy;
            // Добавляем jitter к самой активной гласной
            let maxKey = 'Fcl_MTH_A';
            let maxVal = 0;
            for (const k of ['Fcl_MTH_A','Fcl_MTH_I','Fcl_MTH_U','Fcl_MTH_E','Fcl_MTH_O']) {
                if (this.lipsyncBlendShapes[k] > maxVal) {
                    maxVal = this.lipsyncBlendShapes[k];
                    maxKey = k;
                }
            }
            this.lipsyncBlendShapes[maxKey] += jitter;
            // Ограничиваем диапазон
            this.lipsyncBlendShapes[maxKey] = Math.max(0, Math.min(1, this.lipsyncBlendShapes[maxKey]));
        }
        // --- Быстрое закрытие рта при energy < threshold ---
        if (energy < 0.07) {
            ['Fcl_MTH_A','Fcl_MTH_I','Fcl_MTH_U','Fcl_MTH_E','Fcl_MTH_O'].forEach(k => {
                this.lipsyncBlendShapes[k] *= 0.7;
                if (this.lipsyncBlendShapes[k] < 0.01) this.lipsyncBlendShapes[k] = 0;
            });
        }
        // Применяем blend shapes
        this.applyLipsyncBlendShapes();
    }

    // Новая функция для применения blend shapes липсинка
    applyLipsyncBlendShapes() {
        // Сначала применяем все blend shapes, кроме рта
        this.vrm.scene.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                Object.entries(this.lipsyncBlendShapes).forEach(([key, value]) => {
                    if (key === 'energy') return;
                    // Пропускаем рот — его применим ниже с приоритетом
                    if ([
                        'Fcl_MTH_A','Fcl_MTH_I','Fcl_MTH_U','Fcl_MTH_E','Fcl_MTH_O'
                    ].includes(key)) return;
                    const index = child.morphTargetDictionary[key];
                    if (typeof index !== 'undefined') {
                        child.morphTargetInfluences[index] = Math.max(0, Math.min(1, value));
                    }
                });
            }
        });
        // Теперь lipsync blend shapes (рот) — всегда в приоритете!
        this.vrm.scene.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                ['Fcl_MTH_A','Fcl_MTH_I','Fcl_MTH_U','Fcl_MTH_E','Fcl_MTH_O'].forEach(key => {
                    const index = child.morphTargetDictionary[key];
                    if (typeof index !== 'undefined') {
                        let v = this.lipsyncBlendShapes[key];
                        if (this.lipsyncBlendShapes.energy > 0) {
                            v *= 0.7 + 0.6 * this.lipsyncBlendShapes.energy;
                        }
                        child.morphTargetInfluences[index] = Math.max(0, Math.min(1, v));
                    }
                });
            }
        });
    }

    // Новая функция для установки значений липсинка
    setLipsync(values) {
        // Используем новую систему blend shapes с высоким приоритетом
        if (this.animationIntegration) {
            return this.animationIntegration.setLipsync(values);
        } else {
            // Fallback к старой системе
        // Если все гласные = 0, но есть energy — выставляем A = energy
        const vowels = ['Fcl_MTH_A','Fcl_MTH_I','Fcl_MTH_U','Fcl_MTH_E','Fcl_MTH_O'];
        const allZero = vowels.every(k => !values[k]);
        if (allZero && values.energy > 0) {
            values['Fcl_MTH_A'] = values.energy;
        }
        // Обновляем целевые значения для интерполяции
        Object.keys(this.lipsyncBlendShapes).forEach(key => {
            this.lipsyncLerp.target[key] = values[key] || 0;
        });
        // Если energy не пришёл — вычисляем его как максимум по гласным
        if (typeof values.energy === 'undefined') {
            this.lipsyncLerp.target.energy = Math.max(
                values['Fcl_MTH_A'] || 0,
                values['Fcl_MTH_I'] || 0,
                values['Fcl_MTH_U'] || 0,
                values['Fcl_MTH_E'] || 0,
                values['Fcl_MTH_O'] || 0
            );
            }
        }
    }

    // Новая функция для тестирования липсинка
    testLipsync() {
        console.log('Тестирование липсинка...');
        
        // Последовательность для теста
        const sequence = [
            { vowel: 'A', value: 0.7 },
            { vowel: 'I', value: 0.5 },
            { vowel: 'U', value: 0.6 },
            { vowel: 'E', value: 0.4 },
            { vowel: 'O', value: 0.8 }
        ];

        let index = 0;
        const interval = setInterval(() => {
            if (index >= sequence.length) {
                // Сбрасываем все значения
                this.setLipsync({
                    'Fcl_MTH_A': 0,
                    'Fcl_MTH_I': 0,
                    'Fcl_MTH_U': 0,
                    'Fcl_MTH_E': 0,
                    'Fcl_MTH_O': 0
                });
                clearInterval(interval);
                return;
            }

            const current = sequence[index];
            const values = {
                'Fcl_MTH_A': 0,
                'Fcl_MTH_I': 0,
                'Fcl_MTH_U': 0,
                'Fcl_MTH_E': 0,
                'Fcl_MTH_O': 0
            };
            values[`Fcl_MTH_${current.vowel}`] = current.value;

            console.log(`Тест липсинка: ${current.vowel}`);
            this.setLipsync(values);

            index++;
        }, 1000); // Каждую секунду
    }

    // === ФУНКЦИИ ДЛЯ ТЕСТИРОВАНИЯ НОВОЙ СИСТЕМЫ ===
    
    testOverlappingAnimations() {
        console.log('🎭 Тест наложения анимаций...');
        
        if (this.animationSystem) {
            // Базовая анимация + жест
            this.animationSystem.playAnimation('idle', this.animationSystem.layers.BASE);
            this.animationSystem.playAnimation('greeting', this.animationSystem.layers.GESTURE);
            
            console.log('✅ Наложение: Idle + Greeting');
        } else {
            console.log('❌ Новая система анимаций не инициализирована');
        }
    }
    
    testEmotionPriorities() {
        console.log('🎭 Тест приоритетов эмоций...');
        
        if (this.blendShapeManager) {
            // Базовая эмоция
            this.blendShapeManager.applyEmotion('happy', 0.5, 5);
            
            // Временная эмоция с высоким приоритетом
            this.blendShapeManager.applyEmotion('surprised', 0.8, 8);
            
            // Через 2 секунды возвращаемся к базовой эмоции
            setTimeout(() => {
                this.blendShapeManager.applyEmotion('happy', 0.5, 5);
            }, 2000);
            
            console.log('✅ Приоритеты: Happy (5) → Surprised (8) → Happy (5)');
        } else {
            console.log('❌ Новая система blend shapes не инициализирована');
        }
    }
    
    testStateMachine() {
        console.log('🎭 Тест state machine...');
        
        if (this.stateMachine) {
            // Переходы между состояниями
            this.stateMachine.transitionTo('talking');
            
            // Проверяем разрешенные переходы
            const allowed = this.stateMachine.getAllowedTransitions();
            console.log('Разрешенные переходы:', allowed);
            
            // Возврат к предыдущему состоянию через 3 секунды
            setTimeout(() => {
                this.stateMachine.revertToPrevious();
            }, 3000);
            
            console.log('✅ State Machine: Talking → Previous State');
        } else {
            console.log('❌ State machine не инициализирована');
        }
    }
    
    showDebugInfo() {
        console.log('🎭 Отладочная информация:');
        
        if (this.animationSystem) {
            const activeAnimations = this.animationSystem.getActiveAnimations();
            console.log('Активные анимации:', activeAnimations);
        }
        
        if (this.blendShapeManager) {
            const activeBlendShapes = this.blendShapeManager.getActiveBlendShapes();
            console.log('Активные blend shapes:', activeBlendShapes);
        }
        
        if (this.stateMachine) {
            const currentState = this.stateMachine.getCurrentState();
            const allowedTransitions = this.stateMachine.getAllowedTransitions();
            console.log('Текущее состояние:', currentState);
            console.log('Разрешенные переходы:', allowedTransitions);
        }
        
        console.log('✅ Отладочная информация выведена в консоль');
    }
    
    // Сохранение состояния в localStorage
    saveState() {
        try {
            const state = {
                timestamp: Date.now(),
                currentMovement: this.currentMovement || 'idle',
                currentEmotion: this.currentEmotion || null,
                cameraDistance: this.camera.position.z,
                rotationAngle: THREE.MathUtils.radToDeg(this.rotationGroup?.rotation.y || 0),
                lightIntensity: this.lights?.directional?.intensity || 1.0
            };
            
            localStorage.setItem('vrm_overlay_state', JSON.stringify(state));
            console.log('💾 Состояние сохранено:', state);
        } catch (error) {
            console.error('❌ Ошибка сохранения состояния:', error);
        }
    }
    
    // Восстановление состояния из localStorage
    restoreLastState() {
        try {
            const savedState = localStorage.getItem('vrm_overlay_state');
            if (!savedState) {
                console.log('📋 Сохраненное состояние не найдено');
                return;
            }
            
            const state = JSON.parse(savedState);
            const timeDiff = Date.now() - state.timestamp;
            
            // Восстанавливаем состояние только если оно не старше 5 минут
            if (timeDiff > 5 * 60 * 1000) {
                console.log('⏰ Сохраненное состояние устарело, не восстанавливаем');
                localStorage.removeItem('vrm_overlay_state');
                return;
            }
            
            console.log('🔄 Восстанавливаем состояние:', state);
            
            // Восстанавливаем анимацию
            if (state.currentMovement && this.playMovement) {
                setTimeout(() => {
                    this.playMovement(state.currentMovement);
                }, 1000); // Небольшая задержка для стабилизации
            }
            
            // Восстанавливаем эмоцию
            if (state.currentEmotion && this.applyEmotion) {
                setTimeout(() => {
                    this.applyEmotion(state.currentEmotion);
                }, 1500);
            }
            
            // Восстанавливаем настройки камеры и света
            if (this.camera && state.cameraDistance) {
                this.camera.position.z = state.cameraDistance;
            }
            
            if (this.rotationGroup && state.rotationAngle !== undefined) {
                this.rotationGroup.rotation.y = THREE.MathUtils.degToRad(state.rotationAngle);
            }
            
            if (this.lights && state.lightIntensity) {
                this.lights.ambient.intensity = state.lightIntensity * 0.6;
                this.lights.directional.intensity = state.lightIntensity;
                this.lights.point.intensity = state.lightIntensity * 0.5;
            }
            
            console.log('✅ Состояние восстановлено');
        } catch (error) {
            console.error('❌ Ошибка восстановления состояния:', error);
        }
    }

    // === ДОБАВИТЬ В КЛАСС ===
    updateBaseBoneRotationsFromCurrentPose() {
        // Список костей, как в applyLimbControls
        const bones = [
            { bone: this.findBoneByName('J_Bip_L_UpperArm'), prefix: 'leftArm' },
            { bone: this.findBoneByName('J_Bip_R_UpperArm'), prefix: 'rightArm' },
            { bone: this.findBoneByName('J_Bip_L_LowerArm'), prefix: 'leftForeArm' },
            { bone: this.findBoneByName('J_Bip_R_LowerArm'), prefix: 'rightForeArm' },
            { bone: this.findBoneByName('J_Bip_L_Hand'), prefix: 'leftHand' },
            { bone: this.findBoneByName('J_Bip_R_Hand'), prefix: 'rightHand' },
            { bone: this.findBoneByName('J_Bip_L_UpperLeg'), prefix: 'leftLeg' },
            { bone: this.findBoneByName('J_Bip_R_UpperLeg'), prefix: 'rightLeg' },
            { bone: this.findBoneByName('J_Bip_L_LowerLeg'), prefix: 'leftLowerLeg' },
            { bone: this.findBoneByName('J_Bip_R_LowerLeg'), prefix: 'rightLowerLeg' },
            { bone: this.findBoneByName('J_Bip_L_Foot'), prefix: 'leftFoot' },
            { bone: this.findBoneByName('J_Bip_R_Foot'), prefix: 'rightFoot' },
            { bone: this.findBoneByName('J_Bip_C_Head'), prefix: 'head' },
            { bone: this.findBoneByName('J_Bip_C_Neck'), prefix: 'neck' },
            { bone: this.findBoneByName('J_Bip_C_Chest'), prefix: 'chest' },
            { bone: this.findBoneByName('J_Bip_C_Hips'), prefix: 'hips' },
            { bone: this.findBoneByName('J_Bip_L_Shoulder'), prefix: 'leftShoulder' },
            { bone: this.findBoneByName('J_Bip_R_Shoulder'), prefix: 'rightShoulder' },
        ];
        this.baseBoneRotations = {};
        bones.forEach(({ bone, prefix }) => {
            if (bone) {
                this.baseBoneRotations[prefix] = {
                    x: bone.rotation.x,
                    y: bone.rotation.y,
                    z: bone.rotation.z
                };
            }
        });
    }

    // === ФУНКЦИИ ДЛЯ СИНХРОНИЗАЦИИ С OBS ===
    
    // Отправка команд управления камерой
    sendCameraControl(action, value) {
        if (this.wsClient) {
            this.wsClient.sendMessage({
                type: 'camera_control',
                action: action,
                value: value
            });
        }
    }
    
    // Отправка команд управления позой
    sendPoseControl(bone, axis, value) {
        if (this.wsClient) {
            this.wsClient.sendMessage({
                type: 'pose_control',
                bone: bone,
                axis: axis,
                value: value
            });
        }
    }
    
    // Отправка команд управления освещением
    sendLightControl(action, value) {
        if (this.wsClient) {
            this.wsClient.sendMessage({
                type: 'light_control',
                action: action,
                value: value
            });
        }
    }

    loadSavedPose() {
        console.log('📂 Загрузка сохранённой позы из localStorage...');
        
        const loadedFromStorage = this.loadNaturalPoseFromStorage();
        
        if (this.naturalPose && loadedFromStorage) {
            // Применяем сохранённую позу к модели
            const leftArm = this.findBoneByName('J_Bip_L_UpperArm');
            const rightArm = this.findBoneByName('J_Bip_R_UpperArm');
            const leftForeArm = this.findBoneByName('J_Bip_L_LowerArm');
            const rightForeArm = this.findBoneByName('J_Bip_R_LowerArm');
            const leftHand = this.findBoneByName('J_Bip_L_Hand');
            const rightHand = this.findBoneByName('J_Bip_R_Hand');
            
            if (leftArm) leftArm.rotation.set(this.naturalPose.leftArm.x, this.naturalPose.leftArm.y, this.naturalPose.leftArm.z);
            if (rightArm) rightArm.rotation.set(this.naturalPose.rightArm.x, this.naturalPose.rightArm.y, this.naturalPose.rightArm.z);
            if (leftForeArm) leftForeArm.rotation.set(this.naturalPose.leftForeArm.x, this.naturalPose.leftForeArm.y, this.naturalPose.leftForeArm.z);
            if (rightForeArm) rightForeArm.rotation.set(this.naturalPose.rightForeArm.x, this.naturalPose.rightForeArm.y, this.naturalPose.rightForeArm.z);
            if (leftHand) leftHand.rotation.set(this.naturalPose.leftHand.x, this.naturalPose.leftHand.y, this.naturalPose.leftHand.z);
            if (rightHand) rightHand.rotation.set(this.naturalPose.rightHand.x, this.naturalPose.rightHand.y, this.naturalPose.rightHand.z);
            
            // Обновляем ползунки в интерфейсе
            this.updateArmControlSliders();
            
            console.log('✅ Сохранённая поза загружена и применена');
        } else {
            console.log('❌ Сохранённая поза не найдена в localStorage');
        }
    }
}

// Функция для установки обработчиков кнопок после загрузки приложения
function setupButtonHandlers() {
    console.log('Настройка обработчиков кнопок...');
    
    document.querySelectorAll('[data-action]').forEach(button => {
        const action = button.getAttribute('data-action');
        const emotion = button.getAttribute('data-emotion');
        
        button.addEventListener('click', (e) => {
            if (window.app) {
                try {
                    switch(action) {
                        case 'manualBlink':
                            window.app.manualBlink();
                            break;
                        case 'setEmotion':
                            if (emotion) {
                                window.app.setEmotion(emotion);
                            }
                            break;
                        case 'resetEmotions':
                            window.app.resetEmotions();
                            break;
                        default:
                            console.log(`Неизвестное действие: ${action}`);
                    }
                } catch (error) {
                    console.error('Ошибка при выполнении функции:', error);
                }
            } else {
                console.log('Приложение еще не загружено, попробуйте позже');
            }
        });
    });
    
    console.log('Обработчики кнопок настроены');
}

// Инициализация приложения
const app = new VRMStreamingApp();

// Экспортируем app в глобальную область для доступа из HTML
window.app = app;

// Устанавливаем обработчики после создания приложения
setTimeout(setupButtonHandlers, 100);

// --- ЭКСПОРТ ТОЛЬКО ЧИСТЫХ ФУНКЦИЙ ---
window.app.setEmotion = (...args) => app.__proto__.setEmotion.apply(app, args);
window.app.manualBlink = (...args) => app.__proto__.manualBlink.apply(app, args);
window.app.resetEmotions = (...args) => app.__proto__.resetEmotions.apply(app, args);

// Экспорты функций управления руками
window.app.resetAllBones = (...args) => app.__proto__.resetAllBones.apply(app, args);
window.app.saveAsNaturalPose = (...args) => app.__proto__.saveAsNaturalPose.apply(app, args);
window.app.loadSavedPose = (...args) => app.__proto__.loadSavedPose.apply(app, args);
window.app.resetSavedPose = (...args) => app.__proto__.resetSavedPose.apply(app, args);
window.app.applyToObs = (...args) => app.__proto__.applyToObs.apply(app, args);



// Сохраняем состояние при закрытии страницы
window.addEventListener('beforeunload', () => {
    if (window.app) {
        window.app.saveState();
    }
});

// === ВНЕ КЛАССА ===
function boneControlHtml(prefix, label) {
    return `
        <div style="margin-bottom: 12px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px;">
            <span style="min-width: 60px; font-weight: 500; font-size:15px; margin-bottom:2px;">${label}</span>
            <div style="display: flex; flex-direction: column; gap: 4px;">
                ${['X','Y','Z'].map(axis => `
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span style="font-size:15px; width:15px;">${axis}</span>
                        <button type="button" class="btn-mini" data-bone="${prefix}" data-axis="${axis}" data-action="decrement">−</button>
                        <input type="number" id="${prefix}${axis}" min="-2" max="2" step="0.01" value="0" style="width: 56px; font-size:16px; padding:4px 6px; appearance: textfield; -webkit-appearance: textfield;">
                        <button type="button" class="btn-mini" data-bone="${prefix}" data-axis="${axis}" data-action="increment">+</button>
                    </div>
                `).join('')}
            </div>
            <button type="button" class="btn-mini btn-reset" data-bone="${prefix}" data-action="reset" style="margin-top:6px;">reset</button>
        </div>
    `;
}
