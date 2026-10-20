import logging
import os


from telegram_bot.bot import build_application


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
    application = build_application(token)
    logging.getLogger(__name__).info("Starting Telegram bot with long polling.")
    application.run_polling()


if __name__ == "__main__":
    main()
