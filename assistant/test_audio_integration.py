#!/usr/bin/env python3
"""
Тест интеграции аудио стрима с TTS
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_audio_stream():
    """Тестирует отправку аудио в стрим"""
    try:
        from audio_output import speak_text, AUDIO_STREAM_AVAILABLE
        
        print(f"[TEST] AUDIO_STREAM_AVAILABLE: {AUDIO_STREAM_AVAILABLE}")
        
        if AUDIO_STREAM_AVAILABLE:
            print("[TEST] Тестируем отправку аудио в стрим...")
            await speak_text("Привет! Это тест аудио стрима.")
            print("[TEST] Тест завершен")
        else:
            print("[TEST] Аудио стрим недоступен")
            
    except Exception as e:
        print(f"[TEST ERROR]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audio_stream()) 