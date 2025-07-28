# Assist — Голосовой ассистент для стримов и чатов

## Возможности
- Интеграция с Twitch, YouTube, Telegram, локальным чатом
- Озвучка ответов LLM (через Ollama + локальный gemma3)
- Overlay для эмоций и текста (web-интерфейс для OBS/стрима)
- Долгосрочная и persistent память (RAG)
- Фильтрация спама, rate-limit, антифлуд
- Гибкая система ролей (разные промпты для разных источников)
- Мониторинг состояния (web-интерфейс)
- Централизованный конфиг (config.yaml)
- Отказоустойчивость: автоматический рестарт слушателей, логирование ошибок

## Структура проекта
```
assist/
  audio_output.py         # Озвучка, генерация ответа LLM, overlay
  main.py                 # Точка входа, запуск всех модулей
  recognize_from_microphone.py # Распознавание речи (Whisper)
  overlay_server.py       # WebSocket overlay для эмоций/текста
  telegram_bot.py         # Telegram-бот
  twitch_youtube_chat.py  # Слушатели Twitch/YouTube
  monitor.py              # Web-мониторинг
  config.py, config.yaml  # Конфиг и доступ к нему
  memory/                 # Модули памяти (short/long/persistent)
  roles/                  # Роли и шаблоны промптов
  web_overlay/            # HTML/JS для overlay и мониторинга
```

## Быстрый старт
1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Настройте config.yaml:**
   - Впишите свои токены Twitch, YouTube, Telegram (если нужно)
   - Проверьте лимиты, роли, пути
3. **Запустите ассистента:**
   ```bash
   python main.py
   ```
4. **Откройте overlay и мониторинг:**
   - Overlay: http://localhost:31991 (эмоции/статус), http://localhost:31991/text (текст)
   - Мониторинг: http://localhost:31994

## FAQ
- **Как добавить новые эмоции?**
  - Положите gif в web_overlay/static, добавьте в index.html и emotionGifs.
- **Как сменить роль?**
  - Измените config.yaml или добавьте команду в чат (см. расширение).
- **Как отключить модуль?**
  - В config.yaml поставьте ENABLE_TWITCH/ENABLE_YOUTUBE/ENABLE_OVERLAY в false.
- **Как добавить новую платформу?**
  - Реализуйте слушатель по аналогии с twitch_youtube_chat.py и добавьте в main.py.
- **Как обновить лимиты/роли?**
  - Измените config.yaml и перезапустите ассистента.

## Советы
- Для продакшена используйте отдельный сервер для Ollama/LLM.
- Для ускорения Whisper используйте quantized режим (int8) и уменьшайте silence_duration.
- Для кастомизации overlay редактируйте web_overlay/templates/*.html.

---

**Проект активно развивается!**
Если есть вопросы или предложения — создавайте issue или пишите напрямую. 

 Диагностика
Откройте эти тестовые страницы:
http://192.168.1.4:31991/force-reload - проверит загрузку изображений
http://192.168.1.4:31991/test-websocket - проверит WebSocket соединение
http://192.168.1.4:31991/test-simple - простой тест изображений