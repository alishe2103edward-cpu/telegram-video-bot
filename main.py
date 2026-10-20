import os
import logging
from telegram.ext import Application

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "Missing TELEGRAM_BOT_TOKEN. Add your bot token in Replit Secrets."
        )

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    application = Application.builder().token(token).build()
    logging.getLogger(__name__).info("Starting Telegram bot with long polling.")
    application.run_polling()


if __name__ == "__main__":
    main()
