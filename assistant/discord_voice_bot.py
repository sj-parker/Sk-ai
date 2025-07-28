import discord
import asyncio
import os
from config import get
from audio_output import tts_to_file, chat_stream_ollama
from roles.role_manager import RoleManager
from discord.ext import commands
from recognize_from_microphone import recognize_from_audio_file
import tempfile
import soundfile as sf
import numpy as np
from discord_record import AudioSink

# Импортируй свой ASR (Whisper) сюда
# from recognize_from_microphone import recognize_from_audio_file

TOKEN = get('DISCORD_TOKEN')
GUILD = get('DISCORD_GUILD')
VOICE_CHANNEL = get('DISCORD_VOICE_CHANNEL')
WAKE_WORD = get('DISCORD_WAKE_WORD', 'скай')
ASR_CHUNK_SEC = get('DISCORD_ASR_CHUNK_SEC', 5)
TTS_PATH = get('DISCORD_TTS_PATH', 'temp_audio/discord_tts.mp3')
ENABLE_DISCORD = get('ENABLE_DISCORD', True)

intents = discord.Intents.default()
intents.message_content = False
intents.voice_states = True
intents.guilds = True

class DiscordVoiceBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix="!", intents=intents, **kwargs)
        self.voice_client = None

    async def setup_hook(self):
        pass  # audiorec больше не нужен

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        guild = discord.utils.get(self.guilds, id=int(GUILD)) if GUILD.isdigit() else discord.utils.get(self.guilds, name=GUILD)
        if not guild:
            print(f"Guild {GUILD} not found!")
            return
        channel = discord.utils.get(guild.voice_channels, id=int(VOICE_CHANNEL)) if VOICE_CHANNEL.isdigit() else discord.utils.get(guild.voice_channels, name=VOICE_CHANNEL)
        if not channel:
            print(f"Voice channel {VOICE_CHANNEL} not found!")
            return
        self.voice_client = await channel.connect()
        print(f"Connected to voice channel: {channel}")
        print("Заглушка: аудио из Discord не обрабатывается. Используй команду !test для проверки пайплайна.")

    async def on_audio_receive(self, sink, user, audio):
        # audio.file - путь к WAV-файлу
        text = recognize_from_audio_file(audio.file)
        print(f"[Whisper] {user}: {text}")
        if WAKE_WORD.lower() in text.lower():
            await self.process_discord_message(text)

    async def process_discord_message(self, text):
        # Получаем роль для Discord
        role_manager = RoleManager(source='discord')
        # Генерируем ответ ассистента (LLM)
        response = await chat_stream_ollama(role_manager, None, text, speak=False, user_name="Discord User")
        # Озвучиваем ответ в файл
        tts_file = await tts_to_file(response)
        # Воспроизводим файл в Discord-канале
        await self.play_audio(tts_file)
        os.remove(tts_file)

    async def play_audio(self, file_path):
        if self.voice_client and self.voice_client.is_connected():
            audio_source = discord.FFmpegPCMAudio(file_path)
            self.voice_client.play(audio_source)
            while self.voice_client.is_playing():
                await asyncio.sleep(0.5)

    @commands.command()
    async def test(self, ctx):
        """
        Тестовая команда для проверки пайплайна Whisper → LLM → TTS → воспроизведение.
        Использует файл test.wav в корне проекта.
        """
        test_wav = 'test.wav'
        if not os.path.exists(test_wav):
            await ctx.send('Файл test.wav не найден!')
            return
        text = recognize_from_audio_file(test_wav)
        await ctx.send(f"[Whisper] {text}")
        if WAKE_WORD.lower() in text.lower():
            await self.process_discord_message(text)
        else:
            await ctx.send('Wake word не найдено в тексте.')

# --- Запуск ---
if __name__ == "__main__" and ENABLE_DISCORD:
    bot = DiscordVoiceBot()
    bot.add_command(bot.test)
    bot.run(TOKEN) 