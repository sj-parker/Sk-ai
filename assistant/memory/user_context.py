import os
import json
from memory.manager import MemoryManager
from roles.role_manager import RoleManager
import datetime
import time
from typing import Optional

# Папка для хранения памяти пользователей
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "users")
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Глобальные кэши
user_memories = {}
user_roles = {}

PERSISTENT_DIR = os.path.join(os.path.dirname(__file__), "persistent")
os.makedirs(PERSISTENT_DIR, exist_ok=True)

MAX_USER_CACHE = 100

def get_user_context(user_id: str, source: str = ''):
    # Приводим user_id к строке
    user_id = str(user_id)
    source_str = str(source) if source is not None else ""

    # --- Лимит кэша пользователей ---
    if len(user_memories) >= MAX_USER_CACHE and user_id not in user_memories:
        oldest_user = next(iter(user_memories))
        user_memories.pop(oldest_user, None)
        user_roles.pop(oldest_user, None)

    if user_id not in user_memories:
        # Загружаем долгосрочную память из файла
        filepath = os.path.join(USER_DATA_DIR, f"{user_id}.json")
        memory = MemoryManager()
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    memory.long_term = json.load(f)
            except Exception as e:
                print(f"[Ошибка загрузки памяти {user_id}]: {e}")
        user_memories[user_id] = memory

    if user_id not in user_roles:
        user_roles[user_id] = RoleManager(user_id=user_id, source=source_str)

    return user_memories[user_id], user_roles[user_id]

def save_user_memory(user_id: str):
    user_id = str(user_id)
    if user_id in user_memories:
        filepath = os.path.join(USER_DATA_DIR, f"{user_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(user_memories[user_id].long_term, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Ошибка сохранения памяти {user_id}]: {e}")

def cleanup_old_persistent_memory(days=30):
    now = time.time()
    for fname in os.listdir(PERSISTENT_DIR):
        if fname.endswith('.json'):
            path = os.path.join(PERSISTENT_DIR, fname)
            mtime = os.path.getmtime(path)
            if now - mtime > days * 86400:
                try:
                    os.remove(path)
                    print(f"[Persistent] Удалён устаревший файл: {fname}")
                except Exception as e:
                    print(f"[Persistent] Ошибка удаления {fname}: {e}")

def save_persistent_memory(user_id: Optional[str], messages: list, date_str: str = None):
    """
    Сохраняет persistent память пользователя за день в отдельный файл.
    date_str: 'YYYYMMDD' (по умолчанию сегодня)
    """
    cleanup_old_persistent_memory(days=30)
    user_id_str: str = str(user_id) if user_id is not None else "local"
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(PERSISTENT_DIR, f"{user_id_str}_{date_str}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения persistent памяти {user_id_str}]: {e}")

def load_persistent_memory(user_id: Optional[str], date_str: str = None):
    """
    Загружает persistent память пользователя за день.
    date_str: 'YYYYMMDD' (по умолчанию сегодня)
    """
    user_id_str: str = str(user_id) if user_id is not None else "local"
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(PERSISTENT_DIR, f"{user_id_str}_{date_str}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Ошибка загрузки persistent памяти {user_id_str}]: {e}")
    return []

def handle_memory_commands(text, memory_manager, user_id):
    text_lower = text.lower()
    
    # 1. Обрабатываем команды через новый MemoryManager
    memory_response = memory_manager.handle_memory_commands(text)
    if memory_response:
        return memory_response
    
    # 2. Показываем persistent память за сегодня/вчера/дату
    if "что было важно" in text_lower:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        if "вчера" in text_lower:
            date_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        from memory.user_context import load_persistent_memory
        persistent = load_persistent_memory(user_id, date_str)
        if not persistent:
            return "В этот день ничего важного не было сохранено."
        return "Вот что было важно:\n" + "\n".join([f"- {msg['content']}" for msg in persistent])
    
    # 3. Показываем статистику памяти
    if "статистика памяти" in text_lower or "память статистика" in text_lower:
        stats = memory_manager.get_memory_stats()
        return f"Статистика памяти:\n- Краткосрочная: {stats['short_term_count']} сообщений\n- Долгосрочная: {stats['long_term_count']} записей ({stats['long_term_words']} слов)\n- Persistent: {stats['persistent_count']} записей"

    return None
