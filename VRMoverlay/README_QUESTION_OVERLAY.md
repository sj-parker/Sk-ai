# Question Overlay - Инструкция по использованию

## 📝 Описание

`question_overlay.html` - это отдельный оверлей для OBS, который отображает вопросы пользователя. Он визуально отличается от оверлея с ответами ассистента, чтобы зритель мог легко различать вопрос и ответ.

## 🎨 Визуальные отличия

### Question Overlay (Вопросы)
- **Позиция**: Верх экрана (15vh от верха)
- **Цвет фона**: Градиент фиолетовый (от #667eea до #764ba2)
- **Иконка**: 💭 (облако мыслей)
- **Время отображения**: 8 секунд
- **WebSocket порт**: **31994**

### Text Overlay (Ответы)
- **Позиция**: Низ экрана (10vh от низа)
- **Цвет фона**: Полупрозрачный черный
- **Время отображения**: 12 секунд
- **WebSocket порт**: **31993**

## 🔧 Настройка в OBS

### 1. Добавление Question Overlay

1. Откройте OBS Studio
2. В разделе **Sources** нажмите `+` → **Browser**
3. Назовите источник: `User Questions`
4. Настройки:
   - **URL**: `http://localhost:5173/question_overlay.html` (или путь к файлу)
   - **Width**: 1920
   - **Height**: 1080
   - **FPS**: 30
   - ✅ **Shutdown source when not visible**
   - ✅ **Refresh browser when scene becomes active**

5. Нажмите **OK**

### 2. Добавление Text Overlay (если ещё не добавлен)

Повторите те же шаги, но используйте:
- **Название**: `Assistant Answers`
- **URL**: `http://localhost:5173/text_overlay.html`

## 🌐 WebSocket порты

Ваш бэкенд должен отправлять сообщения на разные порты:

| Тип данных | Порт | Файл |
|------------|------|------|
| VRM команды | 31992 | vrm-only.html |
| Ответы ассистента | 31993 | text_overlay.html |
| **Вопросы пользователя** | **31994** | **question_overlay.html** |

## 💻 Пример кода для бэкенда

### Python (asyncio)

```python
import asyncio
import websockets

# Хранение подключенных клиентов
question_clients = set()
answer_clients = set()

async def question_handler(websocket, path):
    """Обработчик для вопросов пользователя (порт 31994)"""
    question_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        question_clients.remove(websocket)

async def answer_handler(websocket, path):
    """Обработчик для ответов ассистента (порт 31993)"""
    answer_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        answer_clients.remove(websocket)

async def send_question(text):
    """Отправить вопрос пользователя на оверлей"""
    if question_clients:
        await asyncio.gather(
            *[client.send(text) for client in question_clients],
            return_exceptions=True
        )

async def send_answer(text):
    """Отправить ответ ассистента на оверлей"""
    if answer_clients:
        await asyncio.gather(
            *[client.send(text) for client in answer_clients],
            return_exceptions=True
        )

# Запуск серверов
async def main():
    # Сервер для вопросов
    question_server = await websockets.serve(
        question_handler, 
        "192.168.1.4", 
        31994
    )
    
    # Сервер для ответов
    answer_server = await websockets.serve(
        answer_handler, 
        "192.168.1.4", 
        31993
    )
    
    print("✅ WebSocket серверы запущены:")
    print("   📝 Вопросы: ws://192.168.1.4:31994")
    print("   💬 Ответы: ws://192.168.1.4:31993")
    
    await asyncio.Future()  # Работаем вечно

if __name__ == "__main__":
    asyncio.run(main())
```

### Использование в вашем ассистенте

```python
# Когда пользователь задаёт вопрос
user_question = "Как дела?"
await send_question(user_question)

# Когда ассистент отвечает
assistant_answer = "У меня всё отлично, спасибо!"
await send_answer(assistant_answer)
```

## 🎯 Тестирование

### Локальное тестирование

1. Откройте `question_overlay.html` в браузере
2. Откройте консоль разработчика (F12)
3. Проверьте, что WebSocket подключён к `ws://192.168.1.4:31994`

### Отправка тестового сообщения

```python
import asyncio
import websockets

async def test_question():
    uri = "ws://192.168.1.4:31994"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Это тестовый вопрос!")
        print("✅ Вопрос отправлен")

asyncio.run(test_question())
```

## 🎨 Кастомизация

### Изменение позиции

Отредактируйте CSS переменные в файле `question_overlay.html`:

```css
:root {
    --question-overlay-top: 15vh;    /* Расстояние от верха */
    --question-overlay-font-size: 1.8em;  /* Размер текста */
    --question-overlay-max-width: 85vw;   /* Максимальная ширина */
}
```

### Изменение времени отображения

```javascript
const DISPLAY_DURATION = 8000; // Время в миллисекундах
```

### Изменение цвета фона

```css
background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.85) 0%,  /* Начальный цвет */
    rgba(118, 75, 162, 0.85) 100%  /* Конечный цвет */
);
```

## 🔍 Отладка

Для включения индикатора подключения раскомментируйте строку в HTML:

```html
<!-- Раскомментируйте эту строку -->
<div id="connection-status" class="disconnected">Отключено</div>
```

Индикатор покажет:
- 🟢 **Зелёный** = Подключено
- 🔴 **Красный** = Отключено

## 📊 Схема работы

```
Пользователь → Бэкенд → ws://192.168.1.4:31994 → question_overlay.html (OBS)
                     ↓
                     → ws://192.168.1.4:31993 → text_overlay.html (OBS)
                     ↓
                     → ws://192.168.1.4:31992 → vrm-only.html (OBS)
```

## ✅ Готово!

Теперь у вас есть два отдельных оверлея:
- **Question Overlay** - для вопросов пользователя (вверху, фиолетовый)
- **Text Overlay** - для ответов ассистента (внизу, черный)

Зрители на стриме будут чётко видеть, что является вопросом, а что - ответом! 🎉
