"""
Telegram-бот: приветствие и проверка подписки на канал.
Перед запуском создайте файл .env и заполните переменные.
"""

import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")  # опционально: https://t.me/your_channel

SUBSCRIBED_STATUSES = (
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
    ChatMemberStatus.RESTRICTED,
)

BTN_INFO = "ℹ️ Информация"
BTN_CHECK = "✅ Проверить подписку"

MAIN_MENU_KB = ReplyKeyboardMarkup(
    [[BTN_INFO], [BTN_CHECK]],
    resize_keyboard=True,
)


def _channel_configured() -> bool:
    return bool(CHANNEL_ID and CHANNEL_ID.strip())

def _join_text() -> str:
    base = "Чтобы пользоваться ботом, подпишись на канал и нажми «Проверить подписку»."
    if CHANNEL_LINK and CHANNEL_LINK.strip():
        return f"{base}\n\nСсылка на канал: {CHANNEL_LINK.strip()}"
    return base


async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    if not _channel_configured():
        return False
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID.strip(), user_id)
    except Exception as e:
        logger.warning("get_chat_member failed: %s", e)
        return False
    return member.status in SUBSCRIBED_STATUSES


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user = update.effective_user
    name = user.first_name or "друг"
    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "Это бот с проверкой подписки. Ниже главное меню.",
        reply_markup=MAIN_MENU_KB,
    )
    await _post_start_state(update, context)


async def _post_start_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    if not _channel_configured():
        await update.message.reply_text(
            "Админ ещё не настроил CHANNEL_ID в переменных окружения.",
            reply_markup=MAIN_MENU_KB,
        )
        return

    ok = await is_user_subscribed(context, update.effective_user.id)
    if ok:
        await update.message.reply_text("✅ Подписка найдена. Жми «Информация».", reply_markup=MAIN_MENU_KB)
    else:
        await update.message.reply_text(f"❌ Подписка не найдена.\n\n{_join_text()}", reply_markup=MAIN_MENU_KB)


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    if not _channel_configured():
        await update.message.reply_text(
            "CHANNEL_ID не задан в .env. Укажи id или @username канала."
        )
        return
    user_id = update.effective_user.id
    ok = await is_user_subscribed(context, user_id)
    if ok:
        await update.message.reply_text("✅ Ты подписан на канал.")
    else:
        await update.message.reply_text(f"❌ Подписка не найдена.\n\n{_join_text()}")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    if not _channel_configured():
        await update.message.reply_text("Админ ещё не настроил CHANNEL_ID.", reply_markup=MAIN_MENU_KB)
        return
    user_id = update.effective_user.id
    if not await is_user_subscribed(context, user_id):
        await update.message.reply_text(f"🔒 Сначала подпишись.\n\n{_join_text()}", reply_markup=MAIN_MENU_KB)
        return

    await update.message.reply_text(
        "ℹ️ Информация:\n"
        "- Этот бот проверяет подписку на канал.\n"
        "- Если ты подписан, ты видишь этот экран.\n\n"
        "Команды:\n"
        "/start — главное меню\n"
        "/check — проверить подписку",
        reply_markup=MAIN_MENU_KB,
    )


async def on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text == BTN_INFO:
        await info(update, context)
    elif text == BTN_CHECK:
        await check(update, context)
    else:
        await update.message.reply_text("Выбери пункт меню кнопками ниже.", reply_markup=MAIN_MENU_KB)


class _HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        pass

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok")


def _start_http_on_port_if_set() -> None:
    """Render и др. PaaS задают PORT — отвечаем 200, чтобы не уходить в сон (health check)."""
    raw = os.getenv("PORT")
    if not raw:
        return
    try:
        port = int(raw)
    except ValueError:
        return
    if port <= 0:
        return

    def serve() -> None:
        server = HTTPServer(("0.0.0.0", port), _HealthHandler)
        logger.info("HTTP health на порту %s", port)
        server.serve_forever()

    threading.Thread(target=serve, daemon=True).start()


def main() -> None:
    if not BOT_TOKEN:
        logger.error("Задай BOT_TOKEN в файле .env (см. .env.example)")
        sys.exit(1)

    _start_http_on_port_if_set()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_menu_text))

    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
