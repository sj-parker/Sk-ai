# telegram_bot.py
import logging
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# Настройка логгера
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "7871375085:AAFg2pmXeYBJcCBbeQ3gO7GB9EAheoIuwQo"  # Замени на свой токен

from audio_output import chat_stream_ollama
from memory.user_context import get_user_context, save_user_memory, handle_memory_commands  # ✅ индивидуальная память и роли
from monitor import error_log, last_answers, sanitize_user_input
from overlay_server import send_to_overlay
from config import is_telegram_moderator

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text("Привет! Я Скайнет.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not update.effective_user or not update.message.chat:
        return
    if not update.effective_user or not update.effective_user.id:
        return
    user_id = str(update.effective_user.id)
    chat_type = update.message.chat.type
    user_input = update.message.text
    user_input = sanitize_user_input(user_input)

    bot_me = await context.bot.get_me()
    bot_username = bot_me.username.lower() if bot_me.username else ""

    # ✅ Проверяем: если это НЕ личка и НЕТ упоминания — игнорируем
    if chat_type != "private" and f"@{bot_username}" not in user_input.lower():
        return

    # ✅ Удаляем упоминание бота из текста (если есть)
    user_input = user_input.replace(f"@{bot_username}", "").strip()

    logger.debug(f"[{user_id}] Сообщение обработано: {user_input}")
    
    # --- Получаем контекст пользователя с автоматически подмешанной долгосрочной памятью ---
    memory, role_manager = get_user_context(user_id, 'telegram')

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await send_to_overlay("waiting")

    async def send_typing_action():
        try:
            while True:
                await asyncio.sleep(3)
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        except asyncio.CancelledError:
            pass

    typing_task = asyncio.create_task(send_typing_action())

    try:
        # --- Обрабатываем сообщение через LLM (включая команды памяти и автоматическое подмешивание долгосрочной памяти) ---
        user_name = update.effective_user.first_name or update.effective_user.username or user_id
        response = await chat_stream_ollama(role_manager, memory, user_input, speak=False, user_name=user_name)
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

    await update.message.reply_text(response)
    save_user_memory(user_id)

async def modsay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    user_id = str(update.effective_user.id)
    if not is_telegram_moderator(user_id):
        await update.message.reply_text("⛔️ Только для модераторов.")
        return
    args = getattr(context, 'args', None)
    if not args:
        await update.message.reply_text("Использование: /modsay <текст>")
        return
    text = " ".join(args)
    await update.message.reply_text(f"[MOD] {text}")

async def oldman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    user_id = str(update.effective_user.id)
    if not is_telegram_moderator(user_id):
        await update.message.reply_text("⛔️ Только для модераторов.")
        return
    args = getattr(context, 'args', None)
    if not args or len(args) < 1:
        await update.message.reply_text("Использование: /oldman <текст запроса>")
        return
    prompt = " ".join(args)
    from config import get_role
    from memory.user_context import get_user_context
    from audio_output import chat_stream_ollama
    memory, _ = get_user_context(user_id, 'telegram')
    class TempRoleManager:
        def __init__(self, role):
            self._role = role
        def get_role(self, user_id=None):
            return self._role
    role_text = get_role('oldman')
    if not role_text:
        await update.message.reply_text("Роль 'oldman' не найдена в config.yaml. Добавьте её в секцию ROLES.")
        return
    temp_role_manager = TempRoleManager(role_text)
    await update.message.reply_text("Запрос отправлен. Ожидайте...")
    user_name = update.effective_user.first_name or update.effective_user.username or user_id
    response = await chat_stream_ollama(temp_role_manager, memory, prompt, speak=False, user_name=user_name)
    await update.message.reply_text(response)

def run_telegram_bot():
    logger.info("Запуск Telegram бота в отдельном процессе")
    try:
        logger.debug("[TELEGRAM] Создаём ApplicationBuilder")
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.debug("[TELEGRAM] ApplicationBuilder создан")

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CommandHandler("modsay", modsay))
        app.add_handler(CommandHandler("oldman", oldman))
        logger.debug("[TELEGRAM] Хендлеры добавлены")

        logger.info("Telegram бот запущен и готов принимать сообщения")
        app.run_polling()
        logger.info("[TELEGRAM] run_polling завершён")
    except Exception as e:
        logger.error(f"[TELEGRAM] Ошибка: {e}")
