from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import asyncio
import logging

from alert_bot import load_config
from . import AlertHandler, Record


logger = logging.getLogger(__name__)


class TelegramHandler(AlertHandler):
    def __init__(self, token: str, chat_id: int):
        self.token = token
        self.chat_id = chat_id

    async def send_message(self, text: str):
        bot = Bot(token=self.token)
        await bot.send_message(chat_id=self.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

    def handle(self, message: Record):
        text = (
            f"message from {message.timestamp.isoformat()}:\n"
            f"*subject*: {message.subject}\n"
            f"*body*:\n"
            "```\n"
            f"{message.body}\n"
            "```"
        )
        logger.debug(f"send message to telegram: {text}")
        asyncio.run(self.send_message(text))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    echo chat_id back to the user
    """
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat_id is: {chat_id}")
    logger.info(f"Captured chat_id: {chat_id}")


def main():
    """
    poll for messages and echo back chat_id on /start command
    """
    config = load_config()
    config.setup_logging()
    if "telegram" not in config.handlers:
        logger.error("no configuration found for telegram handler")
        return

    app = Application.builder().token(
        config.handlers["telegram"].config["token"]
    ).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
