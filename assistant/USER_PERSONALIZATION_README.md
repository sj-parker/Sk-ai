# Персонализация ответов ассистента

## Обзор

Добавлена возможность персонализации ответов ассистента путем передачи имени пользователя в системный промпт. Это позволяет ассистенту обращаться к пользователям по имени и делать ответы более персональными.

## Изменения

### 1. Модификация `memory/manager.py`

Метод `get_context_as_system_prompt()` теперь принимает параметр `user_name`:

```python
def get_context_as_system_prompt(self, user_name=None):
```

**Логика работы:**
- Если `user_name` передан, он добавляется в системный промпт: `"Ты Скай, ведущая стрим трансляции. Пользователь: {user_name}."`
- Если `user_name` не передан, используется стандартный промпт: `"Ты Скай, ведущая стрим трансляции."`

### 2. Модификация `audio_output.py`

Функция `chat_stream_ollama()` теперь принимает параметр `user_name`:

```python
async def chat_stream_ollama(role_manager, memory, prompt, model_name="gemma3n:e2b", speak=True, user_name=None):
```

### 3. Обновление вызовов в различных модулях

#### `twitch_youtube_chat.py`
```python
response = await chat_stream_ollama(role_manager, memory, text, speak=True, user_name=user)
```

#### `telegram_bot.py`
```python
user_name = update.effective_user.first_name or update.effective_user.username or user_id
response = await chat_stream_ollama(role_manager, memory, user_input, speak=False, user_name=user_name)
```

#### `main.py` (локальный голосовой чат)
```python
await chat_stream_ollama(role_manager, memory, user_text, model_name=ollama_config.get('model', 'gemma3n:e2b'), speak=True, user_name="Буу")
```

#### `auto_activity.py`
```python
response = await chat_stream_ollama(role_manager, memory, prompt, speak=True, user_name="Скай")
```

#### `discord_voice_bot.py`
```python
response = await chat_stream_ollama(role_manager, None, text, speak=False, user_name="Discord User")
```

## Примеры использования

### С персонализацией
```
Системный промпт: "Ты Скай, ведущая стрим трансляции. Пользователь: Виктор."
Пользователь: "Привет! Как дела?"
Ассистент: "Привет, Виктор! 😊 Как дела у тебя? Надеюсь, всё отлично!"
```

### Без персонализации
```
Системный промпт: "Ты Скай, ведущая стрим трансляции."
Пользователь: "Привет! Как дела?"
Ассистент: "Привет! 😊 Как дела? Надеюсь, всё отлично!"
```

## Преимущества

1. **Персонализация**: Ассистент может обращаться к пользователям по имени
2. **Контекст**: Имя пользователя становится частью контекста для LLM
3. **Обратная совместимость**: Все существующие вызовы продолжают работать
4. **Гибкость**: Можно включать/отключать персонализацию по необходимости

## Тестирование

Для тестирования персонализации создан файл `test_user_personalization.py`:

```bash
cd assistant
python test_user_personalization.py
```

Этот тест сравнивает ответы с персонализацией и без неё для разных пользователей.

## Конфигурация

Персонализация работает автоматически для всех источников:
- **Twitch**: использует имя пользователя из чата
- **YouTube**: использует имя автора сообщения
- **Telegram**: использует first_name или username пользователя
- **Локальный голосовой чат**: использует имя "Буу" (создатель)
- **Автоматическая активность**: использует имя "Скай" (сама ассистент)
- **Discord**: использует общее имя "Discord User"

## Обратная совместимость

Все изменения обратно совместимы:
- Если `user_name` не передан, используется стандартное поведение
- Существующие конфигурации не требуют изменений
- Все модули продолжают работать как раньше 