from flask import Flask, render_template, jsonify
import threading
import time
from config import get, check_required_config
import re
import os
import json
from memory.user_context import USER_DATA_DIR, PERSISTENT_DIR
import socket

app = Flask(
    __name__,
    template_folder=os.path.join('web_overlay', 'templates')
)

# Глобальные очереди и логи (заполняются из других модулей)
message_queue = []  # [{'source':..., 'user':..., 'text':..., 'timestamp':...}]
last_answers = []   # [{'source':..., 'user':..., 'text':..., 'timestamp':...}]
error_log = []      # [{'error':..., 'timestamp':...}]
module_status = {
    'twitch': False,
    'youtube': False,
    'overlay': False,
    'text_overlay': False,
    'ocr': False,
}

# --- История времени этапов (максимум 5 последних запросов) ---
timing_history = []  # [{'steps': [...], 'total': ...}, ...]

# --- Последний промпт, отправленный в LLM ---
last_llm_prompt = None

@app.route('/')
def index():
    return render_template('monitor.html')

@app.route('/api/state')
def api_state():
    return jsonify({
        'queue': message_queue[-20:],
        'last_answers': last_answers[-10:],
        'errors': error_log[-10:],
        'modules': module_status,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
    })

@app.route('/api/ocr_history')
def get_ocr_history():
    from ocr_module import get_ocr_text_history
    return jsonify(get_ocr_text_history())

@app.route('/api/health')
def api_health():
    # Проверка записи в temp_audio
    temp_audio_status = True
    try:
        test_path = os.path.join('temp_audio', 'healthcheck.tmp')
        with open(test_path, 'w') as f:
            f.write('ok')
        os.remove(test_path)
    except Exception as e:
        temp_audio_status = False

    # Проверка чтения/записи в user_data_dir
    user_data_status = True
    try:
        user_dir = get('USER_DATA_DIR', 'memory/users')
        test_path = os.path.join(user_dir, 'healthcheck.tmp')
        with open(test_path, 'w') as f:
            f.write('ok')
        os.remove(test_path)
    except Exception as e:
        user_data_status = False

    # Проверка обязательных параметров конфига
    config_status = True
    try:
        check_required_config()
    except Exception as e:
        config_status = False

    # Проверка overlay websocket (только локально)
    overlay_ws_status = True
    ws_port = get('OVERLAY_WS_PORT', 31992)
    ws_host = get('OVERLAY_WS_HOST', '127.0.0.1')
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((ws_host, ws_port))
        sock.close()
    except Exception as e:
        overlay_ws_status = False

    # TODO: Можно добавить проверки внешних API (Discord, Twitch, Telegram) через ping или requests

    return jsonify({
        'status': 'ok',
        'modules': module_status,
        'temp_audio': temp_audio_status,
        'user_data_dir': user_data_status,
        'config': config_status,
        'overlay_ws': overlay_ws_status,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
    })

@app.route('/api/timing')
def api_timing():
    return jsonify(timing_history)

@app.route('/api/llm_prompt')
def api_llm_prompt():
    from flask import Response
    import json
    if last_llm_prompt is None:
        return Response('Нет данных', mimetype='text/plain')
    return Response(json.dumps(last_llm_prompt, ensure_ascii=False, indent=2), mimetype='application/json')

def sanitize_user_input(text):
    # Удаляем управляющие символы (кроме \n и \t)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    # Удаляем zero-width символы и BOM
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    # Ограничиваем количество подряд одинаковых символов (не более 4)
    text = re.sub(r'(.)\1{4,}', r'\1\1\1\1', text)
    return text

def run_monitor():
    port = get('MONITOR_PORT', 31994)
    app.run(host="0.0.0.0", port=port, debug=False)

# Для запуска в отдельном потоке:
def start_monitor_thread():
    t = threading.Thread(target=run_monitor, daemon=True)
    t.start()

def log_memory_stats():
    print("[MEMORY STATS]")
    # Статистика по long_term
    for fname in os.listdir(USER_DATA_DIR):
        if fname.endswith('.json'):
            path = os.path.join(USER_DATA_DIR, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"User {fname.replace('.json','')}: long_term = {len(data)} записей")
            except Exception as e:
                print(f"Ошибка чтения {fname}: {e}")
    # Статистика по persistent
    persistent_files = [f for f in os.listdir(PERSISTENT_DIR) if f.endswith('.json')]
    print(f"Всего persistent файлов: {len(persistent_files)}")

# Вызов статистики при старте
log_memory_stats() 