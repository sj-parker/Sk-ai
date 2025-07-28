import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, make_response, request, jsonify, redirect
from config import get

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    overlay_gifs = get('OVERLAY_GIFS', {})
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    return render_template('index.html', overlay_gifs=overlay_gifs, ws_port=ws_port, ws_host=ws_host)

@app.route('/vrm')
def vrm_overlay():
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    vrm_config = get('VRM_OVERLAY', {})
    emotion_duration_ms = get('OVERLAY_GIFS', {}).get('emotion_duration_ms', 2000)
    
    return render_template('vrm_overlay.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         vrm_model_path=vrm_config.get('model_path', '/static/character.vrm'),
                         emotion_duration_ms=emotion_duration_ms)

@app.route('/vrm-advanced')
def vrm_advanced_overlay():
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    vrm_config = get('VRM_OVERLAY', {})
    emotion_duration_ms = get('OVERLAY_GIFS', {}).get('emotion_duration_ms', 2000)
    
    return render_template('vrm_overlay_advanced.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         vrm_model_path=vrm_config.get('model_path', '/static/character.vrm'),
                         emotion_duration_ms=emotion_duration_ms)

@app.route('/test-vrm')
def test_vrm():
    return app.send_static_file('test_vrm.html')

@app.route('/vrm-simple')
def vrm_simple_overlay():
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    vrm_config = get('VRM_OVERLAY', {})
    emotion_duration_ms = get('OVERLAY_GIFS', {}).get('emotion_duration_ms', 2000)
    
    return render_template('vrm_overlay_simple.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         vrm_model_path=vrm_config.get('model_path', '/static/models/character.vrm'),
                         emotion_duration_ms=emotion_duration_ms)

@app.route('/vrm-debug')
def vrm_debug_overlay():
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    vrm_config = get('VRM_OVERLAY', {})
    emotion_duration_ms = get('OVERLAY_GIFS', {}).get('emotion_duration_ms', 2000)
    
    return render_template('vrm_overlay_debug.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         vrm_model_path=vrm_config.get('model_path', '/static/models/character.vrm'),
                         emotion_duration_ms=emotion_duration_ms)

@app.route('/vrm-fallback')
def vrm_fallback_overlay():
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    vrm_config = get('VRM_OVERLAY', {})
    emotion_duration_ms = get('OVERLAY_GIFS', {}).get('emotion_duration_ms', 2000)
    
    return render_template('vrm_overlay_fallback.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         vrm_model_path=vrm_config.get('model_path', '/static/models/character.vrm'),
                         emotion_duration_ms=emotion_duration_ms)

@app.route('/vrm-local')
def vrm_local_overlay():
    ws_port = app.config.get('OVERLAY_WS_PORT', 31992)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    vrm_config = get('VRM_OVERLAY', {})
    emotion_duration_ms = get('OVERLAY_GIFS', {}).get('emotion_duration_ms', 2000)
    
    return render_template('vrm_overlay_local.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         vrm_model_path=vrm_config.get('model_path', '/static/models/character.vrm'),
                         emotion_duration_ms=emotion_duration_ms)

@app.route('/favicon.ico')
def favicon():
    # Возвращаем пустой favicon для предотвращения 404 ошибок
    response = make_response('', 200)
    response.headers['Content-Type'] = 'image/x-icon'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/static/favicon.ico')
def static_favicon():
    # Возвращаем пустой favicon для предотвращения 404 ошибок
    response = make_response('', 200)
    response.headers['Content-Type'] = 'image/x-icon'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/static/<path:filename>')
def static_files(filename):
    # Специальная обработка для favicon.ico
    if filename == 'favicon.ico':
        response = make_response('', 200)
        response.headers['Content-Type'] = 'image/x-icon'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    response = app.send_static_file(filename)
    # Кэшируем статические файлы на 1 час
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@app.route('/text')
def text_overlay():
    ws_port = app.config.get('TEXT_OVERLAY_WS_PORT', 31993)
    ws_host = app.config.get('OVERLAY_CLIENT_HOST', '192.168.1.4')
    text_overlay_config = get('TEXT_OVERLAY', {})
    return render_template('text_overlay.html', 
                         ws_port=ws_port, 
                         ws_host=ws_host, 
                         text_overlay_config=text_overlay_config)

@app.route('/test')
def test_overlay():
    return app.send_static_file('test_overlay.html')

@app.route('/test-simple')
def test_simple():
    return app.send_static_file('test_simple.html')

@app.route('/test-websocket')
def test_websocket():
    return app.send_static_file('test_websocket.html')

@app.route('/api/test-websocket', methods=['POST'])
def api_test_websocket():
    data = request.get_json()
    message = data.get('message', 'test')
    # Здесь можно добавить отправку сообщения в WebSocket
    return jsonify({'status': 'ok', 'message': f'Received: {message}'})

@app.route('/force-reload')
def force_reload():
    return app.send_static_file('force_reload.html')

@app.route('/test-text-overlay')
def test_text_overlay():
    return app.send_static_file('test_text_overlay.html')

@app.route('/audio-receiver')
def audio_receiver():
    return app.send_static_file('audio_receiver.html')

@app.route('/<path:filename>')
def catch_all(filename):
    # Обработка всех возможных путей к favicon
    if filename in ['favicon.ico', 'static/favicon.ico', 'images/favicon.ico']:
        response = make_response('', 200)
        response.headers['Content-Type'] = 'image/x-icon'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # Для остальных файлов возвращаем 404
    return "File not found", 404

if __name__ == "__main__":
    # Получаем порт из конфига или используем 31991 по умолчанию
    port = get('WEB_SERVER_PORT', 31991)
    app.run(host="0.0.0.0", port=port, debug=True)