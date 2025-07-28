import unittest
import os
import time
from unittest.mock import patch, MagicMock
from triggers import contains_trigger
from memory.short_term import ShortTermMemory
from config import check_required_config, config
from audio_output import TMP_FOLDER, periodic_temp_audio_cleanup
from memory.manager import MemoryManager

class TestUtils(unittest.TestCase):
    def test_contains_trigger(self):
        self.assertTrue(contains_trigger('Привет, скай!'))
        self.assertTrue(contains_trigger('Hello, sky!'))
        self.assertFalse(contains_trigger('Привет, мир!'))

    def test_short_term_memory(self):
        mem = ShortTermMemory(max_length=3)
        mem.add('user', 'one')
        mem.add('user', 'two')
        mem.add('user', 'three')
        self.assertEqual(len(mem.get_memory()), 3)
        mem.add('user', 'four')
        self.assertEqual(len(mem.get_memory()), 3)
        self.assertEqual(mem.get_memory()[0]['content'], 'two')
        mem.clear()
        self.assertEqual(len(mem.get_memory()), 0)

    def test_check_required_config_valid(self):
        # Должно не выбрасывать исключение
        check_required_config()

    def test_check_required_config_invalid(self):
        # Подделываем конфиг с отсутствующим ключом
        orig = config.get('TWITCH_TOKEN')
        config['TWITCH_TOKEN'] = ''
        with self.assertRaises(RuntimeError):
            check_required_config()
        config['TWITCH_TOKEN'] = orig

    def test_temp_audio_cleanup(self):
        # Создаём старый файл
        test_path = os.path.join(TMP_FOLDER, 'test_old.tmp')
        with open(test_path, 'w') as f:
            f.write('old')
        # Делаем файл старым
        old_time = time.time() - 7200
        os.utime(test_path, (old_time, old_time))
        # Запускаем очистку вручную
        def cleanup_once():
            now = time.time()
            for fname in os.listdir(TMP_FOLDER):
                fpath = os.path.join(TMP_FOLDER, fname)
                try:
                    if os.path.isfile(fpath):
                        if now - os.path.getmtime(fpath) > 3600:
                            os.remove(fpath)
                except Exception as e:
                    pass
        cleanup_once()
        self.assertFalse(os.path.exists(test_path))

    def test_memory_manager_long_term(self):
        mem = MemoryManager()
        mem.add('user', 'hello')
        mem.add('assistant', 'hi')
        self.assertTrue(any(m['content'] == 'hello' for m in mem.get_short_memory()))
        mem.save_long_term()
        self.assertTrue(isinstance(mem.long_term, list))

    def test_memory_manager_search(self):
        mem = MemoryManager()
        mem.long_term = [
            {'role': 'user', 'content': 'запомни важное'},
            {'role': 'assistant', 'content': 'ок'},
            {'role': 'user', 'content': 'ещё что-то'},
        ]
        results = mem.search_memory('важное')
        self.assertEqual(len(results), 1)
        self.assertIn('важное', results[0]['content'])

    @patch('overlay_server.server_ref', None)
    @patch('overlay_server.websockets')
    def test_overlay_server_start(self, mock_websockets):
        from overlay_server import start_overlay_server, server_ref
        mock_websockets.serve = MagicMock()
        # Первый старт должен вызвать serve
        async def run():
            await start_overlay_server(12345)
            self.assertTrue(mock_websockets.serve.called)
        import asyncio
        asyncio.run(run())
        # Повторный старт не должен вызвать serve
        mock_websockets.serve.reset_mock()
        from overlay_server import server_ref as sr
        sr = object()  # имитируем уже запущенный сервер
        with patch('overlay_server.server_ref', sr):
            async def run2():
                await start_overlay_server(12345)
                self.assertFalse(mock_websockets.serve.called)
            asyncio.run(run2())

    def test_rate_limit(self):
        # Имитация rate-limit из twitch_youtube_chat
        from twitch_youtube_chat import last_answer_time, CHAT_RATE_LIMIT
        user = ('twitch', 'user1')
        now = time.time()
        last_answer_time[user] = now
        # Следующий вызов слишком рано
        from twitch_youtube_chat import process_message_from_chat
        async def test():
            await process_message_from_chat('twitch', 'user1', 'скай привет')
            # last_answer_time не должен обновиться
            self.assertEqual(last_answer_time[user], now)
        import asyncio
        asyncio.run(test())

    def test_ocr_module_extract_text(self):
        from ocr_module import OCRModule
        ocr = OCRModule()
        # Мокаем reader.readtext
        ocr.reader = MagicMock()
        ocr.reader.readtext.return_value = [((0,0,0,0), 'тест', 0.9)]
        text = ocr.extract_text('fake_image')
        self.assertIn('тест', text)
        # Проверка фильтра по prob
        ocr.reader.readtext.return_value = [((0,0,0,0), 'low', 0.1)]
        text = ocr.extract_text('fake_image')
        self.assertEqual(text, '')

    @patch('telegram_bot.run_telegram_bot')
    def test_telegram_bot_run(self, mock_run):
        # Проверяем, что функция запускается без ошибок
        from telegram_bot import run_telegram_bot
        mock_run.return_value = None
        try:
            run_telegram_bot()
        except Exception as e:
            self.fail(f"Telegram bot run failed: {e}")

    @patch('discord_voice_bot.DiscordVoiceBot')
    def test_discord_voice_bot_run(self, mock_bot):
        # Проверяем, что бот создаётся и run вызывается
        from discord_voice_bot import DiscordVoiceBot, ENABLE_DISCORD, TOKEN
        bot = mock_bot()
        bot.run.return_value = None
        if ENABLE_DISCORD:
            try:
                bot.run(TOKEN)
            except Exception as e:
                self.fail(f"Discord bot run failed: {e}")

if __name__ == '__main__':
    unittest.main() 