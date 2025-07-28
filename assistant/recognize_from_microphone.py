import queue
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import asyncio

samplerate = 16000
blocksize = 8000
silence_threshold = 50
silence_duration = 1.0

audio_queue = queue.Queue()
model = WhisperModel("base", compute_type="int8_float32")

def audio_callback(indata, frames, time_info, status):
    if status:
        print("⚠️", status)
    audio_queue.put(indata.copy())

def recognize_sync():
    print("🎤 Ожидание речи...")
    buffer = []
    silent_chunks = 0
    max_silent_chunks = int(silence_duration * samplerate / blocksize)

    with sd.InputStream(samplerate=samplerate, blocksize=blocksize, channels=1, dtype='float32', callback=audio_callback):
        while True:
            data = audio_queue.get()
            volume_norm = np.linalg.norm(data) * 10
            if volume_norm > silence_threshold:
                buffer.append(data)
                silent_chunks = 0
                print("🎙 Идёт запись...", end="\r")
            else:
                if buffer:
                    silent_chunks += 1
                    print(f"🔇 Тишина {silent_chunks}/{max_silent_chunks}", end="\r")
                    if silent_chunks >= max_silent_chunks:
                        break

    print("\n⏱ Распознаём...")
    audio = np.concatenate(buffer, axis=0).flatten()
    segments, _ = model.transcribe(audio, language="ru")
    final_text = ""
    for segment in segments:
        final_text += segment.text + " "
    print(f"\n Распознано: {final_text.strip()}")
    return final_text.strip()

async def recognize_from_microphone_async():
    # Запускаем синхронный код в отдельном потоке
    text = await asyncio.to_thread(recognize_sync)
    return text
