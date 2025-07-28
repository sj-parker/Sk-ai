import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

def get(key, default=None):
    return config.get(key, default)

def get_role(source):
    return config.get('ROLES', {}).get(source, config.get('ROLES', {}).get('local', ''))

# --- Новые функции для управления памятью ---
def is_short_term_enabled():
    return config.get('MEMORY', {}).get('ENABLE_SHORT_TERM', True)

def is_long_term_enabled():
    return config.get('MEMORY', {}).get('ENABLE_LONG_TERM', True)

def is_persistent_enabled():
    return config.get('MEMORY', {}).get('ENABLE_PERSISTENT', True)

# --- Новые функции для настроек долгосрочной памяти ---
def get_long_term_config():
    """Возвращает настройки долгосрочной памяти"""
    return config.get('MEMORY', {}).get('LONG_TERM', {})

def get_long_term_max_words():
    """Максимальное количество слов в долгосрочной памяти"""
    return get_long_term_config().get('MAX_WORDS', 300)

def get_long_term_max_words_per_entry():
    """Максимальное количество слов в одной записи"""
    return get_long_term_config().get('MAX_WORDS_PER_ENTRY', 4)

def is_long_term_auto_include():
    """Автоматически подмешивать долгосрочную память в контекст"""
    return get_long_term_config().get('AUTO_INCLUDE', True)

def get_long_term_max_entries_to_include():
    """Максимальное количество записей для подмешивания"""
    return get_long_term_config().get('MAX_ENTRIES_TO_INCLUDE', 10)

def get_long_term_save_phrases():
    """Ключевые фразы для сохранения в долгосрочную память"""
    return get_long_term_config().get('SAVE_PHRASES', ["запомни", "не забудь", "это важно", "обязательно запомни"])

def get_long_term_recall_phrases():
    """Ключевые фразы для поиска в памяти"""
    return get_long_term_config().get('RECALL_PHRASES', ["вспомни", "помнишь", "что ты помнишь"])

def is_long_term_natural_integration():
    """Естественная интеграция памяти (без явных упоминаний "памяти")"""
    return get_long_term_config().get('NATURAL_INTEGRATION', True)

def check_required_config():
    required_keys = [
        'TWITCH_TOKEN',
        'TWITCH_CHANNEL',
        'YOUTUBE_VIDEO_ID',
        'OVERLAY_HOST',
        'OVERLAY_PORT',
        'DISCORD_TOKEN',
        'DISCORD_GUILD',
        'DISCORD_VOICE_CHANNEL',
        'USER_DATA_DIR',
        'PERSISTENT_DIR',
    ]
    missing = []
    for key in required_keys:
        if not config.get(key):
            missing.append(key)
    if missing:
        msg = f"[CONFIG ERROR] Missing required config keys: {', '.join(missing)}"
        print(msg)
        raise RuntimeError(msg)

def is_telegram_moderator(user_id):
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return str(user_id) in [str(uid) for uid in config.get("MODERATORS", {}).get("telegram", [])]

def get_tts_engine():
    return config.get('TTS_ENGINE', 'edge')

# --- Функции для автоматической активности ---
def is_auto_activity_enabled():
    """Включена ли автоматическая активность"""
    return config.get('AUTO_ACTIVITY', {}).get('ENABLED', False)

def get_auto_activity_config():
    """Возвращает настройки автоматической активности"""
    return config.get('AUTO_ACTIVITY', {})

def get_inactivity_timeout():
    """Время ожидания без сообщений перед активацией (в секундах)"""
    return get_auto_activity_config().get('INACTIVITY_TIMEOUT', 300)

def get_activity_check_interval():
    """Интервал проверки активности (в секундах)"""
    return get_auto_activity_config().get('CHECK_INTERVAL', 60)

def get_max_context_messages():
    """Максимальное количество последних сообщений для контекста"""
    return get_auto_activity_config().get('MAX_CONTEXT_MESSAGES', 10)

def get_activity_types():
    """Типы активности"""
    return get_auto_activity_config().get('ACTIVITY_TYPES', ['fact', 'joke', 'comment'])

def get_activity_weights():
    """Вероятности каждого типа активности"""
    return get_auto_activity_config().get('ACTIVITY_WEIGHTS', {'fact': 30, 'joke': 40, 'comment': 30})

def get_fact_config():
    """Настройки для фактов"""
    return get_auto_activity_config().get('FACT', {})

def get_joke_config():
    """Настройки для шуток"""
    return get_auto_activity_config().get('JOKE', {})

def get_comment_config():
    """Настройки для комментариев"""
    return get_auto_activity_config().get('COMMENT', {})

def is_auto_activity_cache_disabled():
    """Отключен ли кэш для автоматической активности"""
    return get_auto_activity_config().get('DISABLE_CACHE', False) 