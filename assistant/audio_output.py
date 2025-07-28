import re
import json
import asyncio
import uuid
import os
import edge_tts
import requests
import subprocess
from overlay_server import send_to_overlay, send_text_to_overlay, send_emotion_to_vrm, send_animation_to_vrm, send_status_to_vrm, send_speech_to_vrm, send_text_to_vrm, send_to_vrm
from monitor import error_log, last_answers
import time
import inspect
from collections import OrderedDict
from config import get, get_tts_engine
from typing import Optional
import threading
from vrm_websocket import init_vrm_server, send_mouth_open
import monitor

# Импорт аудио стрим сервера
try:
    from audio_stream_server import audio_server
    AUDIO_STREAM_AVAILABLE = True
    print("[AUDIO STREAM] Модуль аудио стрима доступен")
except ImportError as e:
    AUDIO_STREAM_AVAILABLE = False
    print(f"[AUDIO STREAM] Модуль аудио стрима недоступен: {e}")

# --- Silero TTS ---
import torch
import soundfile as sf
import numpy as np

VOICE = "ru-RU-SvetlanaNeural"
TMP_FOLDER = "temp_audio"
os.makedirs(TMP_FOLDER, exist_ok=True)

# Паттерн для деления текста на произносимые куски
punctuation_pattern = re.compile(r'[.!?…\n]+')

# --- Глобальный LLM-кэш ---
class LLMCache(OrderedDict):
    def __init__(self, maxsize=1000):
        super().__init__()
        self.maxsize = maxsize
    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value
    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]
llm_cache = LLMCache(maxsize=1000)

def silero_tts(text, filename, speaker='baya', sample_rate=48000):
    model, _ = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language='ru',
        speaker='v3_1_ru'
    )
    audio = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
    sf.write(filename, audio, sample_rate)

async def stream_lipsync_from_wav(filename, duration=None, frame_ms=40):
    """
    Анализирует wav/mp3-файл, отправляет energy lipsync в VRM overlay.
    frame_ms — длина окна анализа в миллисекундах (обычно 30-50мс)
    duration — длительность аудио (сек), если известна
    """
    try:
        # Открываем аудиофайл (mp3/wav)
        data, samplerate = sf.read(filename)
        if len(data.shape) > 1:
            data = data.mean(axis=1)  # моно
        frame_len = int(samplerate * frame_ms / 1000)
        total_frames = len(data) // frame_len
        for i in range(total_frames):
            frame = data[i*frame_len:(i+1)*frame_len]
            if len(frame) == 0:
                continue
            rms = np.sqrt(np.mean(frame**2))
            # Масштабируем energy в диапазон 0..1 (эмпирически)
            energy = min(1.0, float(rms) * 5)
            await send_to_vrm({"type": "lipsync", "energy": energy})
            await asyncio.sleep(frame_ms / 1000)
        # В конце — рот закрыть
        await send_to_vrm({"type": "lipsync", "energy": 0.0})
    except Exception as e:
        print(f"[LIPSYNC ERROR]: {e}")

async def speak_text(text: str):
    tts_engine = get_tts_engine()
    ext = '.wav'  # Всегда сохраняем в wav для корректного анализа
    filename = os.path.join(TMP_FOLDER, f"{uuid.uuid4().hex}{ext}")
    try:
        await init_vrm_server()
        if tts_engine == 'silero':
            silero_tts(text, filename)
            lipsync_task = asyncio.create_task(stream_lipsync_from_wav(filename))
        else:
            # EdgeTTS: пробуем сохранить напрямую в wav
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(filename)
            # Проверяем, действительно ли файл wav (иногда EdgeTTS сохраняет mp3 с расширением wav)
            try:
                _ = sf.info(filename)
                wav_for_lipsync = filename
            except Exception:
                # Если не удалось прочитать как wav — конвертируем mp3 в wav
                mp3_filename = filename.replace('.wav', '.mp3')
                os.rename(filename, mp3_filename)
                wav_for_lipsync = filename
                subprocess.run(['ffmpeg', '-y', '-i', mp3_filename, wav_for_lipsync], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            lipsync_task = asyncio.create_task(stream_lipsync_from_wav(wav_for_lipsync))
        
        await send_mouth_open(0.7)
        
        # Отправляем аудио в стрим (если сервер запущен)
        if AUDIO_STREAM_AVAILABLE:
            try:
                # Читаем аудио файл и отправляем в стрим
                with open(filename, 'rb') as f:
                    audio_data = f.read()
                await audio_server.broadcast_audio(audio_data)
                print(f"[AUDIO STREAM] Аудио отправлено в стрим ({len(audio_data)} байт)")
            except Exception as e:
                print(f"[AUDIO STREAM] Ошибка отправки аудио: {e}")
        else:
            print("[AUDIO STREAM] Аудио стрим недоступен")
        
        # Проигрываем аудио локально (ffplay)
        proc = subprocess.Popen(
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Ждём завершения проигрывания и lipsync
        await asyncio.to_thread(proc.wait)
        await lipsync_task
        await send_mouth_open(0.0)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        # Удаляем временный mp3, если был
        mp3_filename = filename.replace('.wav', '.mp3')
        if os.path.exists(mp3_filename):
            os.remove(mp3_filename)

# --- Вынести emoji_map на уровень модуля ---
emoji_map = {
    '😊': 'happy',
    '😄': 'happy',
    '😢': 'sad',
    '😭': 'sad',
    '😡': 'angry',
    '😱': 'surprised',
    '😉': 'happy',
    '😃': 'happy',
    '😆': 'happy',
    '😂': 'happy',
    '😐': 'neutral',
    '😔': 'sad',
    '😞': 'sad',
    '😅': 'happy',
    '😏': 'happy',
    '😜': 'happy',
    '😋': 'happy',
    '😤': 'angry',
    '😬': 'surprised',
    '😳': 'surprised',
    '😇': 'happy',
    '😎': 'happy',
    '🥲': 'sad',
    '🥹': 'sad',
    '🥰': 'happy',
    '😍': 'happy',
    '😘': 'happy',
    '😚': 'happy',
    '😙': 'happy',
    '😗': 'happy',
    '😚': 'happy',
    '😽': 'happy',
    '😺': 'happy',
    '😸': 'happy',
    '😹': 'happy',
    '😻': 'happy',
    '😼': 'happy',
    '😽': 'happy',
    '😾': 'angry',
    '😿': 'sad',
    '🙀': 'surprised',
}

def extract_emotion(text):
    for emoji, emotion in emoji_map.items():
        if emoji in text:
            return emotion
    return None

# --- ДОБАВЛЕНО: emoji -> animation ---
emoji_to_animation = {
    '😱': 'surprise_move',
    '😳': 'surprise_move',
    '🙀': 'surprise_move',
    '🤯': 'surprise_move',
    '🫢': 'surprise_move',
    '🥶': 'surprise_move',
    '🥴': 'surprise_move',
    '🫨': 'surprise_move',
    '😮': 'surprise_move',
    '😲': 'surprise_move',
    '😯': 'surprise_move',
    '😵': 'surprise_move',
    '😵\u200d💫': 'surprise_move',  # 😵‍💫
    '🥱': 'surprise_move',
    '🤭': 'surprise_move',
    '🤔': 'surprise_move',
    '😡': 'activeTalking_move',
    '😤': 'activeTalking_move',
    '😊': 'greeting_move',
    '😄': 'greeting_move',
    '🥰': 'greeting_move',
    '😢': 'thinking_move',
    '😭': 'thinking_move',
    # Можно расширять по желанию
    # --- Волнение (excitement) ---
    '🤩': 'excitement_move',
    '🤗': 'excitement_move',
    '🥳': 'excitement_move',
    '🤪': 'excitement_move',
    '🤠': 'excitement_move',
    '🤓': 'excitement_move',
    '🤘': 'excitement_move',
    '✨': 'excitement_move',
    '💃': 'excitement_move',
    '🕺': 'excitement_move',
    '🥂': 'excitement_move',
    '🎉': 'excitement_move',
    '🎊': 'excitement_move',
    # --- Приветствие (greeting) ---
    '👋': 'greeting_move',
    '🖐️': 'greeting_move',
    '✋': 'greeting_move',
    '🤚': 'greeting_move',
    '🫱': 'greeting_move',
    '🫲': 'greeting_move',
    '🫳': 'greeting_move',
    '🫴': 'greeting_move',
    '🤝': 'greeting_move',
    '🙏': 'greeting_move',
    '🙌': 'greeting_move',
    '👏': 'greeting_move',
}

def clean_text_for_tts(text):
    filters = get('TTS_FILTERS', {})
    # Удалить всё, что между *звёздочками*
    if filters.get('remove_star_text', True):
        text = re.sub(r'\*.*?\*', '', text)
    # Удалить emoji
    if filters.get('remove_emoji', True):
        # Удаляем все emoji (unicode диапазоны)
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
    # Оставить только разрешённые символы
    allowed = filters.get('allowed_chars', 'a-zA-Zа-яА-ЯёЁ0-9 ')
    text = re.sub(f'[^{allowed}]', '', text)
    return text

# --- ДОБАВИТЬ: универсальный парсер для эмоций и движений ---
def extract_emotion_and_animation(text):
    found_emotion = None
    found_animation = None
    for char in text:
        if not found_emotion and char in emoji_map:
            found_emotion = emoji_map[char]
        if not found_animation and char in emoji_to_animation:
            found_animation = emoji_to_animation[char]
        if found_emotion and found_animation:
            break
    return found_emotion, found_animation

# --- Глобальные переменные для отслеживания эмоций и движений ---
last_emotion = None
last_animation = None
emotion_reset_time = 0
animation_reset_time = 0

# model phi3:mini or gemma3:4b or gemma:2b or gemma3n:e2b
async def chat_stream_ollama(role_manager, memory, prompt, model_name="gemma3n:e2b", speak=True, user_name=None):
    steps = []
    step_start = time.time()
    cache_key = (role_manager.get_role(), prompt)
    if cache_key in llm_cache:
        full_response = llm_cache[cache_key]
        print("[LLM CACHE] Ответ из кэша.")
        await send_text_to_overlay(full_response.strip())
        last_answers.append({'source': 'local', 'user': 'user', 'text': full_response.strip(), 'timestamp': time.strftime('%H:%M:%S')})
        return full_response.strip()

    memory.add("user", prompt)
    steps.append({"name": "add_to_short_term", "duration": time.time() - step_start}); step_start = time.time()

    # --- Обработка команд памяти ---
    memory_response = memory.handle_memory_commands(prompt)
    steps.append({"name": "memory_commands", "duration": time.time() - step_start}); step_start = time.time()
    if memory_response:
        print(f"[MEMORY] {memory_response}")
        await send_text_to_overlay(memory_response)
        last_answers.append({'source': 'local', 'user': 'user', 'text': memory_response, 'timestamp': time.strftime('%H:%M:%S')})
        monitor.timing_history.append({"steps": steps, "total": sum(s["duration"] for s in steps)})
        if len(monitor.timing_history) > 5:
            monitor.timing_history.pop(0)
        return memory_response

    # --- Получаем контекст с автоматически подмешанной долгосрочной памятью ---
    context_prompt = memory.get_context_as_system_prompt(user_name)
    steps.append({"name": "get_context_as_system_prompt", "duration": time.time() - step_start}); step_start = time.time()
    context_messages = [context_prompt] if context_prompt else []

    # --- Поиск по ключевым словам (только если не найдено в автоматическом контексте) ---
    recall_keywords = ["вспомни", "помнишь"]
    recall_hits = []
    if any(kw in prompt.lower() for kw in recall_keywords):
        # Поиск в long_term
        recall_hits.extend(memory.search_memory(prompt, persistent=False, max_results=3))
        # Поиск в persistent (если есть)
        recall_hits.extend(memory.search_memory(prompt, persistent=True, max_results=2))
    steps.append({"name": "search_memory", "duration": time.time() - step_start}); step_start = time.time()

    # 💡 Вставляем роль + контекст с долгосрочной памятью + релевантную память + краткосрочную
    messages = (
        [{"role": "system", "content": role_manager.get_role()}]
        + context_messages
        + recall_hits
        + memory.get_short_memory()
    )
    try:
        import monitor
        monitor.last_llm_prompt = messages
    except Exception:
        pass
    steps.append({"name": "form_messages", "duration": time.time() - step_start}); step_start = time.time()

    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "messages": messages,
        "stream": True
    }

    buffer = ""
    full_response = ""
    last_text_update = ""

    try:
        # Отправляем статус "thinking" в VRM
        await send_status_to_vrm("thinking")
        steps.append({"name": "overlay_thinking", "duration": time.time() - step_start}); step_start = time.time()
        
        with requests.post(url, json=data, headers=headers, stream=True) as response:
            steps.append({"name": "llm_request_start", "duration": time.time() - step_start}); step_start = time.time()
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8').strip()
                if line.startswith("data:"):
                    line = line[5:].strip()

                try:
                    json_data = json.loads(line)
                    content = json_data.get("message", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        buffer += content
                        full_response += content

                        # --- Эмоции через overlay и VRM ---
                        now = time.time()
                        emotion, animation = extract_emotion_and_animation(content)
                        print(f"[DEBUG] extract_emotion_and_animation: emotion={emotion}, animation={animation}, content={content!r}")
                        global last_emotion, last_animation, emotion_reset_time, animation_reset_time
                        # Эмоция
                        if emotion:
                            print(f"[DEBUG] Триггер эмоции: {emotion}")
                            if emotion != last_emotion or now > emotion_reset_time:
                                await send_to_overlay(f"emotion:{emotion}")
                                await send_emotion_to_vrm(emotion, 1.0, 2000)
                                last_emotion = emotion
                                emotion_reset_time = now + 2  # 2 секунды (или сколько длится эмоция)
                        # Движение
                        if animation:
                            print(f"[DEBUG] Триггер движения: {animation}")
                            if animation != last_animation or now > animation_reset_time:
                                await send_animation_to_vrm(animation, 2000)
                                last_animation = animation
                                animation_reset_time = now + 2  # 2 секунды (или сколько длится движение)
                        # --- конец ---

                        # --- Промежуточное обновление текстового overlay ---
                        # Обновляем текст только когда накопилось достаточно контента
                        # или когда встретили знак препинания
                        text_overlay_config = get('TEXT_OVERLAY', {})
                        min_chars = text_overlay_config.get('update_min_chars', 50)
                        update_on_punct = text_overlay_config.get('update_on_punctuation', True)
                        
                        should_update = len(full_response) - len(last_text_update) > min_chars
                        if update_on_punct:
                            should_update = should_update or any(p in content for p in '.!?')
                        
                        if should_update:
                            await send_text_to_overlay(full_response.strip())
                            # Отправляем текст в VRM
                            await send_text_to_vrm(full_response.strip(), 5000)
                            last_text_update = full_response
                        # --- конец ---

                        while True:
                            match = punctuation_pattern.search(buffer)
                            if not match:
                                break
                            chunk = buffer[:match.end()].strip()
                            buffer = buffer[match.end():]
                            if chunk and speak:
                                # Отправляем статус "talking" в VRM
                                await send_status_to_vrm("talking")
                                await send_speech_to_vrm(True, chunk)
                                
                                await send_to_overlay("start")
                                clean_chunk = clean_text_for_tts(chunk)
                                if clean_chunk.strip():
                                    await speak_text(clean_chunk)
                                await send_to_overlay("stop")
                                
                                # Отправляем статус "idle" в VRM
                                await send_status_to_vrm("idle")
                                await send_speech_to_vrm(False)

                    if json_data.get("done", False):
                        if buffer.strip() and speak:
                            # Отправляем статус "talking" в VRM для последнего куска
                            await send_status_to_vrm("talking")
                            await send_speech_to_vrm(True, buffer.strip())
                            
                            clean_buffer = clean_text_for_tts(buffer.strip())
                            if clean_buffer:
                                await speak_text(clean_buffer)
                            
                            # Отправляем статус "idle" в VRM
                            await send_status_to_vrm("idle")
                            await send_speech_to_vrm(False)

                        # Добавляем ответ в память
                        memory.add("assistant", full_response.strip())
                        # ⏳ Сохраняем долгосрочную память (если есть что сохранять)
                        memory.save_long_term()
                        steps.append({"name": "llm_response", "duration": time.time() - step_start}); step_start = time.time()
                        break

                except Exception as e:
                    print(f"\n[Ошибка парсинга]: {e}")
                    error_log.append({'error': f'[LLM Parse Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})

    except requests.RequestException as e:
        print(f"[Ошибка подключения к Ollama]: {e}")
        error_log.append({'error': f'[Ollama Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})
        # Отправляем статус "idle" в VRM при ошибке
        await send_status_to_vrm("idle")

    await send_text_to_overlay(full_response.strip())
    steps.append({"name": "overlay_final_text", "duration": time.time() - step_start}); step_start = time.time()
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        caller = frame.f_back.f_code.co_name
        if caller not in ['process_message_from_chat']:
            last_answers.append({'source': 'local', 'user': 'user', 'text': full_response.strip(), 'timestamp': time.strftime('%H:%M:%S')})

    llm_cache[cache_key] = full_response.strip()
    steps.append({"name": "cache_and_finish", "duration": time.time() - step_start}); step_start = time.time()
    monitor.timing_history.append({"steps": steps, "total": sum(s["duration"] for s in steps)})
    if len(monitor.timing_history) > 5:
        monitor.timing_history.pop(0)
    return full_response.strip()

async def chat_stream_llamacpp(role_manager, memory, prompt, model_path="E:\\Skai\\llm\\gemma-3n-E4B-it-Q6_K.gguf", speak=True):
    """
    Альтернативная функция для работы с llama.cpp напрямую
    Использует только текст пользователя как prompt (без ролей и контекста)
    """
    steps = []
    step_start = time.time()
    cache_key = (role_manager.get_role(), prompt)
    if cache_key in llm_cache:
        full_response = llm_cache[cache_key]
        print("[LLM CACHE] Ответ из кэша.")
        await send_text_to_overlay(full_response.strip())
        last_answers.append({'source': 'local', 'user': 'user', 'text': full_response.strip(), 'timestamp': time.strftime('%H:%M:%S')})
        return full_response.strip()

    memory.add("user", prompt)
    steps.append({"name": "add_to_short_term", "duration": time.time() - step_start}); step_start = time.time()

    # --- Обработка команд памяти ---
    memory_response = memory.handle_memory_commands(prompt)
    steps.append({"name": "memory_commands", "duration": time.time() - step_start}); step_start = time.time()
    if memory_response:
        print(f"[MEMORY] {memory_response}")
        await send_text_to_overlay(memory_response)
        last_answers.append({'source': 'local', 'user': 'user', 'text': memory_response, 'timestamp': time.strftime('%H:%M:%S')})
        monitor.timing_history.append({"steps": steps, "total": sum(s["duration"] for s in steps)})
        if len(monitor.timing_history) > 5:
            monitor.timing_history.pop(0)
        return memory_response

    # --- llama.cpp: prompt только текст пользователя ---
    full_prompt = prompt

    buffer = ""
    full_response = ""
    last_text_update = ""

    try:
        # Отправляем статус "thinking" в VRM
        await send_status_to_vrm("thinking")
        steps.append({"name": "overlay_thinking", "duration": time.time() - step_start}); step_start = time.time()
        
        # Запускаем llama.cpp как подпроцесс
        import subprocess
        import json
        
        # Путь к llama-cli.exe
        llama_path = "E:\\Skai\\llama_vulkan\\build\\bin\\Release\\llama-cli.exe"
        
        # Параметры запуска
        cmd = [
            llama_path,
            "-m", model_path,
            "-p", full_prompt,
            "-n", "200",  # максимальное количество токенов
            "-t", "8",    # количество потоков
            "--no-warmup"  # пропускаем разогрев
        ]
        
        print(f"[LLAMACPP] Запуск: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        steps.append({"name": "llm_request_start", "duration": time.time() - step_start}); step_start = time.time()
        
        # Читаем весь вывод сразу (llama.cpp может не поддерживать потоковый вывод)
        stdout, stderr = process.communicate()
        
        if stderr:
            print(f"[LLAMACPP STDERR]: {stderr}")
        
        if stdout:
            # Обрабатываем вывод как единый блок
            output = stdout.strip()
            print(output, end="", flush=True)
            full_response = output
            # Обрабатываем весь ответ сразу
            if full_response.strip() and speak:
                await send_status_to_vrm("talking")
                await send_speech_to_vrm(True, full_response.strip())
                
                clean_response = clean_text_for_tts(full_response.strip())
                if clean_response:
                    await speak_text(clean_response)
                
                await send_status_to_vrm("idle")
                await send_speech_to_vrm(False)

        # Добавляем ответ в память
        memory.add("assistant", full_response.strip())
        memory.save_long_term()
        steps.append({"name": "llm_response", "duration": time.time() - step_start}); step_start = time.time()

    except Exception as e:
        print(f"[Ошибка llama.cpp]: {e}")
        error_log.append({'error': f'[LLAMACPP Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})
        await send_status_to_vrm("idle")

    await send_text_to_overlay(full_response.strip())
    steps.append({"name": "overlay_final_text", "duration": time.time() - step_start}); step_start = time.time()
    
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        caller = frame.f_back.f_code.co_name
        if caller not in ['process_message_from_chat']:
            last_answers.append({'source': 'local', 'user': 'user', 'text': full_response.strip(), 'timestamp': time.strftime('%H:%M:%S')})

    llm_cache[cache_key] = full_response.strip()
    steps.append({"name": "cache_and_finish", "duration": time.time() - step_start}); step_start = time.time()
    monitor.timing_history.append({"steps": steps, "total": sum(s["duration"] for s in steps)})
    if len(monitor.timing_history) > 5:
        monitor.timing_history.pop(0)
    return full_response.strip()

async def tts_to_file(text: str, filename: Optional[str] = None) -> str:
    """
    Сохраняет озвучку текста в mp3- или wav-файл и возвращает путь к файлу.
    Если filename не указан — создаёт уникальный файл в TMP_FOLDER.
    Файл не удаляется автоматически!
    """
    tts_engine = get_tts_engine()
    ext = '.wav' if tts_engine == 'silero' else '.mp3'
    if not filename:
        filename = os.path.join(TMP_FOLDER, f"{uuid.uuid4().hex}{ext}")
    if filename is None:
        raise ValueError("filename не может быть None")
    if tts_engine == 'silero':
        silero_tts(text, filename)
    else:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(filename)
    return filename

def periodic_temp_audio_cleanup(folder=TMP_FOLDER, max_age_sec=3600, interval_sec=1800):
    """
    Периодически удаляет файлы старше max_age_sec из папки folder.
    """
    def cleanup():
        while True:
            now = time.time()
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                try:
                    if os.path.isfile(fpath):
                        if now - os.path.getmtime(fpath) > max_age_sec:
                            os.remove(fpath)
                except Exception as e:
                    print(f"[TEMP_AUDIO CLEANUP ERROR]: {e}")
            time.sleep(interval_sec)
    t = threading.Thread(target=cleanup, daemon=True)
    t.start()

# Запуск очистки при импорте модуля
periodic_temp_audio_cleanup()