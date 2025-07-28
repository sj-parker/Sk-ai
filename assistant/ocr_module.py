# ocr_module.py
import cv2
import easyocr
import numpy as np
import time
import threading
from PIL import ImageGrab
import os
from config import get
from monitor import error_log, module_status
from memory.user_context import get_user_context, save_user_memory

class OCRModule:
    def __init__(self):
        self.reader = None
        self.is_running = False
        self.last_text = ""
        self.text_history = []
        self.max_history = 10
        self.languages = ['ru', 'en']  # русский и английский
        self.initialize_reader()
        
    def initialize_reader(self):
        """Инициализация EasyOCR"""
        try:
            print("[OCR] Инициализация EasyOCR...")
            self.reader = easyocr.Reader(self.languages, gpu=False)
            print("[OCR] EasyOCR инициализирован успешно")
            module_status['ocr'] = True
        except Exception as e:
            print(f"[OCR] Ошибка инициализации: {e}")
            error_log.append({'error': f'[OCR Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})
            module_status['ocr'] = False
    
    def capture_screen(self):
        """Захват экрана"""
        try:
            # Захватываем весь экран
            screenshot = ImageGrab.grab()
            # Конвертируем в numpy array для OpenCV
            frame = np.array(screenshot)
            # Конвертируем из RGB в BGR (OpenCV формат)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"[OCR] Ошибка захвата экрана: {e}")
            return None
    
    def capture_camera(self):
        """Захват с камеры (если доступна)"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[OCR] Камера недоступна")
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return frame
            else:
                return None
        except Exception as e:
            print(f"[OCR] Ошибка захвата с камеры: {e}")
            return None
    
    def extract_text(self, image):
        """Извлечение текста из изображения"""
        if self.reader is None:
            return ""
        
        try:
            # Распознаём текст
            results = self.reader.readtext(image)
            
            # Извлекаем текст из результатов
            text_parts = []
            for (bbox, text, prob) in results:
                if prob > 0.5:  # Фильтруем по уверенности
                    text_parts.append(text.strip())
            
            return " ".join(text_parts)
        except Exception as e:
            print(f"[OCR] Ошибка распознавания текста: {e}")
            return ""
    
    def process_text(self, text):
        """Обработка распознанного текста"""
        if not text or text == self.last_text:
            return
        
        # Очищаем текст от лишних символов
        clean_text = text.strip()
        if len(clean_text) < 3:  # Игнорируем слишком короткий текст
            return
        
        self.last_text = clean_text
        
        # Добавляем в историю
        self.text_history.append({
            'text': clean_text,
            'timestamp': time.strftime('%H:%M:%S')
        })
        
        # Ограничиваем размер истории
        if len(self.text_history) > self.max_history:
            self.text_history.pop(0)
        
        # Логируем распознанный текст
        print(f"[OCR] Распознан текст: {clean_text}")
        
        # Сохраняем в память ассистента
        try:
            memory, role_manager = get_user_context("ocr_user", 'ocr')
            memory.add("user", f"Я вижу на экране текст: {clean_text}")
            save_user_memory("ocr_user")
        except Exception as e:
            print(f"[OCR] Ошибка сохранения в память: {e}")
    
    def start_monitoring(self, source='screen', interval=5):
        """Запуск мониторинга"""
        if self.is_running:
            return
        
        self.is_running = True
        print(f"[OCR] Запуск мониторинга ({source}) с интервалом {interval} сек")
        
        def monitor_loop():
            while self.is_running:
                try:
                    # Захватываем изображение
                    if source == 'screen':
                        image = self.capture_screen()
                    elif source == 'camera':
                        image = self.capture_camera()
                    else:
                        continue
                    
                    if image is not None:
                        # Извлекаем текст
                        text = self.extract_text(image)
                        if text:
                            self.process_text(text)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"[OCR] Ошибка в цикле мониторинга: {e}")
                    time.sleep(interval)
        
        # Запускаем в отдельном потоке
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_running = False
        print("[OCR] Мониторинг остановлен")
    
    def get_text_history(self):
        """Получение истории распознанного текста"""
        return self.text_history.copy()
    
    def clear_history(self):
        """Очистка истории"""
        self.text_history.clear()
        self.last_text = ""

# Глобальный экземпляр OCR модуля
ocr_module = None

def init_ocr_module():
    """Инициализация OCR модуля"""
    global ocr_module
    if ocr_module is None:
        ocr_module = OCRModule()
    return ocr_module

def start_ocr_monitoring(source='screen', interval=5):
    """Запуск OCR мониторинга"""
    global ocr_module
    if ocr_module is None:
        ocr_module = init_ocr_module()
    
    ocr_module.start_monitoring(source, interval)

def stop_ocr_monitoring():
    """Остановка OCR мониторинга"""
    global ocr_module
    if ocr_module:
        ocr_module.stop_monitoring()

def get_ocr_text_history():
    """Получение истории OCR"""
    global ocr_module
    if ocr_module:
        return ocr_module.get_text_history()
    return [] 