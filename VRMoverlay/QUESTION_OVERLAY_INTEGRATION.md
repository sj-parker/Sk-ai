# Тестирование Question Overlay

## ✅ Что было сделано:

### 1. Изменения в `overlay_server.py`
- ✅ Добавлен `question_overlay_clients` набор клиентов
- ✅ Добавлен `question_server_ref` для сервера
- ✅ Создан `question_handler()` - обработчик подключений
- ✅ Создан `broadcast_question()` - функция для отправки вопросов
- ✅ Создан `send_question_to_overlay()` - публичная функция для отправки
- ✅ Обновлен `start_overlay_server()` для запуска сервера на порту 31994
- ✅ Обновлен `stop_overlay_server()` для корректного завершения

### 2. Изменения в `main.py`
- ✅ Добавлен параметр `question_port=overlay_ws_port + 2` (31994) в `start_overlay_server()`

### 3. Изменения в `twitch_youtube_chat.py`
- ✅ Добавлен импорт `send_question_to_overlay`
- ✅ Добавлен вызов `await send_question_to_overlay(f"{user}: {text}")` перед обработкой

### 4. Изменения в `telegram_bot.py`
- ✅ Добавлен импорт `send_question_to_overlay`
- ✅ Добавлен вызов `await send_question_to_overlay(f"{user_name}: {user_input}")` перед обработкой

### 5. Файлы оверлеев
- ✅ `question_overlay.html` - оверлей для вопросов (порт 31994)
- ✅ `text_overlay.html` - оверлей для ответов (порт 31993)
- ✅ `vrm-only.html` - оверлей для VRM модели (порт 31992)

## 🎯 Архитектура WebSocket серверов:

```
Порт 31992 (VRM)     → vrm-only.html         → VRM команды (анимации, эмоции, липсинк)
Порт 31993 (Answers) → text_overlay.html     → Ответы ассистента (внизу экрана)
Порт 31994 (Questions) → question_overlay.html → Вопросы пользователя (вверху экрана)
```

## 🚀 Запуск

### Автоматически запустится при старте ассистента:
```bash
python main.py
```

Или запустите универсальный скрипт:
```bash
python start_universal_with_indextts.py
```

### В консоли вы увидите:
```
🚀 Запуск WebSocket серверов...
📡 Основной сервер: ws://192.168.1.4:31992
📝 Текстовый сервер: ws://192.168.1.4:31993
💭 Вопросный сервер: ws://192.168.1.4:31994
✅ WebSocket серверы запущены успешно!
```

## 🎨 Настройка в OBS

### 1. VRM Overlay
- URL: `http://localhost:5173/vrm-only.html`
- Размер: 1920x1080

### 2. Text Overlay (Ответы)
- URL: `http://localhost:5173/text_overlay.html`
- Размер: 1920x1080

### 3. **Question Overlay (Вопросы)** ⭐
- URL: `http://localhost:5173/question_overlay.html`
- Размер: 1920x1080

## 📝 Пример работы

1. Пользователь пишет в Twitch: "Скай, привет!"
2. **Вопрос отображается вверху** (фиолетовый фон): "Username: Скай, привет!"
3. Ассистент генерирует ответ
4. **Ответ отображается внизу** (черный фон): "@Username, Привет! Как дела?"
5. VRM модель говорит и показывает эмоции

## 🔧 Проверка работы

### Откройте в браузере для тестирования:
1. http://localhost:5173/question_overlay.html - вопросы
2. http://localhost:5173/text_overlay.html - ответы
3. http://localhost:5173/vrm-only.html - VRM модель

### Проверьте консоль:
- Должны увидеть подключение к WebSocket
- При получении сообщения появится текст на экране

## ✨ Итог

Теперь у вас полноценная система с тремя отдельными оверлеями:
- ✅ VRM модель с анимациями
- ✅ Вопросы пользователей (вверху, фиолетовый)
- ✅ Ответы ассистента (внизу, черный)

Всё работает автоматически при запуске ассистента! 🎉
