# 🎭 Интеграция VRM с Ассистентом

Этот документ описывает интеграцию 3D аватара VRM с голосовым ассистентом для создания интерактивного виртуального персонажа.

## 🚀 Быстрый старт

### 1. Запуск ассистента
```bash
cd assistant
python main.py
```

### 2. Запуск VRM приложения
```bash
cd VRMoverlay
npm install
npm run dev
```

### 3. Проверка интеграции
```bash
python test_vrm_integration.py
```

## 📡 Архитектура интеграции

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Ассистент     │ ←──────────────→ │   VRM Overlay   │
│                 │                 │                 │
│ • TTS           │                 │ • 3D Аватар     │
│ • LLM           │                 │ • Анимации      │
│ • Память        │                 │ • Эмоции        │
│ • Чат-интеграция│                 │ • Текст overlay │
└─────────────────┘                 └─────────────────┘
```

## 🔧 Настройка

### Конфигурация WebSocket
В файле `assistant/config.yaml`:
```yaml
OVERLAY_WS_HOST: "192.168.1.4"  # Ваш IP адрес
OVERLAY_WS_PORT: 31992          # Порт WebSocket
```

В файле `VRMoverlay/src/vrm-websocket.js`:
```javascript
this.wsHost = '192.168.1.4'; // Измените на ваш IP
this.wsPort = 31992;         // Порт WebSocket ассистента
```

### Настройка VRM модели
1. Поместите вашу VRM модель в папку `VRMoverlay/public/`
2. Обновите путь в `VRMoverlay/index.html`:
```html
<option value="your-model.vrm">Your Model</option>
```

## 📨 Протокол WebSocket

### Команды от ассистента к VRM:

#### Статус
```json
{
  "type": "status",
  "status": "idle|talking|thinking|waiting"
}
```

#### Эмоция
```json
{
  "type": "emotion",
  "emotion": "happy|sad|angry|surprised|neutral",
  "intensity": 1.0,
  "duration": 2000
}
```

#### Анимация
```json
{
  "type": "animation",
  "animation": "idle|talking|thinking|greeting|breathing|stretching|surprise|excitement|listening",
  "duration": 5000
}
```

#### Текст
```json
{
  "type": "text",
  "text": "Текст для отображения",
  "duration": 5000
}
```

#### Речь
```json
{
  "type": "speech",
  "isSpeaking": true|false,
  "text": "Текст речи"
}
```

### Идентификация VRM клиента:
```json
{
  "type": "vrm_client",
  "client": "vrm_overlay",
  "version": "1.0"
}
```

## 🎮 Возможности

### Автоматическая синхронизация:
- ✅ **Эмоции** - автоматически извлекаются из текста ассистента
- ✅ **Анимации речи** - активируются при TTS
- ✅ **Статусы** - thinking, talking, idle
- ✅ **Текстовый overlay** - отображение речи в VRM

### Ручное управление:
- ✅ **Эмоции** - кнопки в интерфейсе VRM
- ✅ **Анимации** - выпадающий список движений
- ✅ **Поза** - управление руками и телом
- ✅ **Камера** - настройка ракурса

## 🔍 Отладка

### Проверка подключения:
1. Откройте консоль браузера в VRM приложении
2. Убедитесь, что WebSocket подключен:
```
✅ WebSocket подключен к ассистенту
```

### Тестирование команд:
```bash
python test_vrm_integration.py
```

### Логи ассистента:
```
🎭 VRM клиент подключен. Всего VRM клиентов: 1
```

## 🛠️ Расширение функциональности

### Добавление новых эмоций:
1. В `assistant/audio_output.py` добавьте эмодзи в `emoji_map`
2. В `VRMoverlay/src/main.js` добавьте обработку в `applyEmotion()`

### Добавление новых анимаций:
1. В `VRMoverlay/src/main.js` создайте новую анимацию
2. В `assistant/overlay_server.py` добавьте функцию отправки

### Кастомизация текстового overlay:
В `VRMoverlay/src/vrm-websocket.js` измените `showTextOverlay()`.

## 📋 Требования

### Для ассистента:
- Python 3.8+
- Зависимости из `assistant/requirements.txt`
- Ollama с моделью (gemma3:4b, phi3:mini, etc.)

### Для VRM:
- Node.js 16+
- Современный браузер с WebGL
- VRM модель (.vrm файл)

## 🚨 Устранение неполадок

### VRM не подключается:
1. Проверьте IP адрес в настройках
2. Убедитесь, что ассистент запущен
3. Проверьте файрвол

### Анимации не работают:
1. Проверьте, что VRM модель загружена
2. Убедитесь, что кости найдены в модели
3. Проверьте консоль на ошибки

### Эмоции не применяются:
1. Проверьте blend shapes в VRM модели
2. Убедитесь, что эмоции определены в коде
3. Проверьте логи в консоли

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в консоли браузера
2. Проверьте логи ассистента
3. Запустите тестовый скрипт
4. Создайте issue с описанием проблемы

---

**Удачной интеграции! 🎉** 