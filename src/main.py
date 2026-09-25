"""
Telegram bot for parsing posts and reposting them to VK group +
answer to advertisement requests.

Main module, launches infinite polling and passes settings from
config.py to telegram_bot.py
"""

from config import settings
from logging_config import setup_logging
from telegram_bot import create_bot

def main() -> None:
    """
    Initialize logging, set up Telegram bot, remove existing webhooks,
    start polling.
    """
    setup_logging()

    bot = create_bot(settings)
    bot.delete_webhook()

    bot.infinity_polling(
        allowed_updates=['message', 'channel_post'],
    )

if __name__ == '__main__':
    main()