import re
from memory.short_term import ShortTermMemory
from memory.long_term import load_long_term_memory, save_long_term_memory
from config import (
    is_short_term_enabled, is_long_term_enabled, is_persistent_enabled,
    get_long_term_max_words, get_long_term_max_words_per_entry, is_long_term_auto_include,
    get_long_term_max_entries_to_include, get_long_term_save_phrases, get_long_term_recall_phrases,
    is_long_term_natural_integration
)

class MemoryManager:
    def __init__(self, max_short_length=5, long_term_save_limit=20):
        self.short_term = ShortTermMemory(max_length=max_short_length) if is_short_term_enabled() else None
        self.long_term = load_long_term_memory() if is_long_term_enabled() else []
        self.long_term_save_limit = long_term_save_limit
        self.persistent_memory = [] if is_persistent_enabled() else None

    def add(self, role, content):
        if is_short_term_enabled() and self.short_term:
            # Удаляем триггер-фразу, если есть (только для пользователя)
            if role == "user":
                save_phrases = get_long_term_save_phrases()
                content_lc = content.lower()
                for phrase in save_phrases:
                    if content_lc.startswith(phrase):
                        # Удаляем только в начале строки
                        content = content[len(phrase):].lstrip()
                        break
            self.short_term.add(role, content)

    def load_from_json(self, data):
        if is_long_term_enabled():
            self.long_term = data

    def to_json(self):
        return self.long_term if is_long_term_enabled() else []

    def count_words(self, text):
        """Подсчитывает количество слов в тексте"""
        if not text:
            return 0
        return len(text.split())

    def should_remember(self, message):
        """Проверяет, нужно ли сохранить сообщение в долгосрочную память"""
        if message["role"] != "user":
            return False
        
        content = message["content"].lower()
        save_phrases = get_long_term_save_phrases()
        
        # Проверяем наличие ключевых фраз
        found_phrase = None
        for phrase in save_phrases:
            if phrase in content:
                found_phrase = phrase
                break
        
        if not found_phrase:
            return False
        
        # Удаляем ключевую фразу из подсчета слов
        content_without_phrase = content.replace(found_phrase, "").strip()
        max_words_per_entry = get_long_term_max_words_per_entry()
        word_count = self.count_words(content_without_phrase)
        
        if word_count > max_words_per_entry:
            print(f"[MEMORY] Запись слишком длинная ({word_count} слов), максимум {max_words_per_entry}")
            return False
        
        return True

    def get_short_memory(self):
        if is_short_term_enabled() and self.short_term:
            return self.short_term.get_memory()
        return []

    def get_context_as_system_prompt(self, user_name=None):
        """Возвращает системный промпт с естественной интеграцией долгосрочной памяти"""
        if not is_long_term_enabled() or not is_long_term_auto_include():
            if user_name:
                return {"role": "system", "content": f"Ты Скай, ведущая стрим трансляции. Пользователь: {user_name}."}
            else:
                return {"role": "system", "content": "Ты Скай, ведущая стрим трансляции."}
        
        # Получаем последние записи из долгосрочной памяти
        max_entries = get_long_term_max_entries_to_include()
        recent_memories = self.long_term[-max_entries:] if self.long_term else []
        
        if not recent_memories:
            if user_name:
                return {"role": "system", "content": f"Ты Скай, ведущая стрим трансляции. Пользователь: {user_name}."}
            else:
                return {"role": "system", "content": "Ты Скай, ведущая стрим трансляции."}
        
        # Формируем контекст из долгосрочной памяти
        memory_context = []
        save_phrases = get_long_term_save_phrases()
        for memory in recent_memories:
            if memory.get("role") == "user":
                content = memory.get("content", "").strip()
                if content:
                    clean_content = content
                    for phrase in save_phrases:
                        if phrase in clean_content.lower():
                            clean_content = clean_content.replace(phrase, "").strip()
                            break
                    if clean_content:
                        memory_context.append(clean_content)
        
        if not memory_context:
            if user_name:
                return {"role": "system", "content": f"Ты Скай, ведущая стрим трансляции. Пользователь: {user_name}."}
            else:
                return {"role": "system", "content": "Ты Скай, ведущая стрим трансляции."}
        
        # Проверяем настройку естественной интеграции
        natural_integration = is_long_term_natural_integration()
        
        if natural_integration:
            # Естественная интеграция без явных упоминаний "памяти"
            if user_name:
                context_text = f"Ты Скай, ведущая стрим трансляции. Пользователь: {user_name}. "
            else:
                context_text = "Ты Скай, ведущая стрим трансляции. "
            
            # Добавляем факты о пользователе как естественную часть контекста
            if len(memory_context) == 1:
                context_text += f"Информация о пользователе: {memory_context[0]}"
            else:
                context_text += "Информация о пользователе: " + "; ".join(memory_context)
        else:
            # Старый способ с явным упоминанием памяти
            if user_name:
                context_text = f"Ты Скай, ведущая стрим трансляции. Пользователь: {user_name}. "
            else:
                context_text = "Ты Скай, ведущая стрим трансляции. "
            context_text += (
                "Вот факты о пользователе, которые были сохранены для улучшения взаимодействия. Учитывай их, чтобы делать ответы более персональными и полезными.\n"
                + "\n".join(memory_context)
            )
        
        return {"role": "system", "content": context_text}

    def is_duplicate(self, msg):
        """Проверяет, есть ли уже такая запись в долгосрочной памяти (по роли и содержимому)"""
        for m in self.long_term:
            if m.get("role") == msg.get("role") and m.get("content") == msg.get("content"):
                return True
        return False

    def save_long_term(self):
        """Сохраняет важные сообщения в долгосрочную память с ограничениями и фильтрацией дубликатов"""
        if not is_long_term_enabled():
            return
        if not is_short_term_enabled() or not self.short_term:
            return
        
        short_memory = self.short_term.get_memory()[-self.long_term_save_limit:]
        remembered = []
        i = 0
        
        while i < len(short_memory):
            msg = short_memory[i]
            if self.should_remember(msg):
                # Проверяем общее ограничение по словам
                current_words = sum(self.count_words(m.get("content", "")) for m in self.long_term)
                new_words = self.count_words(msg.get("content", ""))
                max_words = get_long_term_max_words()
                
                if current_words + new_words > max_words:
                    print(f"[MEMORY] Достигнут лимит слов в долгосрочной памяти ({current_words}/{max_words})")
                    # Удаляем самые старые записи, чтобы освободить место
                    while self.long_term and current_words + new_words > max_words:
                        oldest = self.long_term.pop(0)
                        current_words -= self.count_words(oldest.get("content", ""))
                
                # --- Фильтрация дубликатов ---
                if not self.is_duplicate(msg):
                    remembered.append(msg)
                if i + 1 < len(short_memory) and short_memory[i + 1]["role"] == "assistant":
                    if not self.is_duplicate(short_memory[i + 1]):
                        remembered.append(short_memory[i + 1])
                    i += 1
            i += 1
        
        if remembered:
            self.long_term.extend(remembered)
            save_long_term_memory(self.long_term)
            print(f"[MEMORY] Сохранено {len(remembered)} записей в долгосрочную память")

    def search_memory(self, query, persistent=False, max_results=3):
        """
        Ищет релевантные сообщения по ключевым словам в long_term или persistent памяти.
        Возвращает список сообщений (dict).
        """
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        if persistent:
            if not is_persistent_enabled() or self.persistent_memory is None:
                return []
            memory_source = self.persistent_memory
        else:
            if not is_long_term_enabled():
                return []
            memory_source = self.long_term
        
        results = []
        for msg in reversed(memory_source):
            if pattern.search(msg.get("content", "")):
                results.append(msg)
                if len(results) >= max_results:
                    break
        return list(reversed(results))

    def get_long_term_summary(self):
        """Возвращает краткое описание долгосрочной памяти"""
        if not is_long_term_enabled() or not self.long_term:
            return "Я пока ничего не знаю о тебе."
        
        memories = []
        save_phrases = get_long_term_save_phrases()
        
        for memory in self.long_term:
            if memory.get("role") == "user":
                content = memory.get("content", "").strip()
                if content:
                    # Удаляем ключевые слова из отображения
                    clean_content = content
                    for phrase in save_phrases:
                        if phrase in clean_content.lower():
                            clean_content = clean_content.replace(phrase, "").strip()
                            break
                    
                    if clean_content:
                        memories.append(clean_content)
        
        if not memories:
            return "Я пока ничего не знаю о тебе."
        
        # Более естественный ответ без явного упоминания "памяти"
        if len(memories) == 1:
            return f"Я знаю, что ты: {memories[0]}"
        else:
            return "Вот что я знаю о тебе:\n" + "\n".join([f"- {memory}" for memory in memories])

    def handle_memory_commands(self, text):
        """Обрабатывает команды для работы с памятью"""
        text_lower = text.lower()
        recall_phrases = get_long_term_recall_phrases()
        
        # Команды для получения долгосрочной памяти
        if any(phrase in text_lower for phrase in recall_phrases):
            return self.get_long_term_summary()
        
        return None

    def load_persistent_memory(self, data):
        if is_persistent_enabled():
            self.persistent_memory = data

    def clear_persistent_memory(self):
        if is_persistent_enabled():
            self.persistent_memory = []

    def get_memory_stats(self):
        """Возвращает статистику памяти"""
        stats = {
            'short_term_count': len(self.short_term.get_memory()) if self.short_term else 0,
            'long_term_count': len(self.long_term),
            'long_term_words': sum(self.count_words(m.get("content", "")) for m in self.long_term),
            'persistent_count': len(self.persistent_memory) if self.persistent_memory else 0
        }
        return stats
