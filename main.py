import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# Loggingni sozlash
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(name)

# Har xil tillardagi matnlar bazasi (Localization)
TRANSLATIONS = {
    "uz": {
        "welcome": "Assalomu alaykum! AI Reklama va Video Maker botiga xush kelibsiz. 🚀\nIltimos, o'zingizga qulay tilni tanlang:",
        "choose_mode": "Kerakli rejimni tanlang:",
        "btn_business": "🏢 Biznes uchun reklama",
        "btn_reels": "🎬 Reels & TikTok yaratish",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в AI Telegram Video Maker. 🚀\nПожалуйста, выберите язык:",
        "choose_mode": "Выберите режим работы:",
        "btn_business": "🏢 Реклама для бизнеса",
        "btn_reels": "🎬 Создать Reels & TikTok",
    },
    "kk": {
        "welcome": "Сәлем! AI Video Maker ботына қош келдіңіз. 🚀\nӨзіңізге ыңғайlı тілді таңдаңыз:",
        "choose_mode": "Жұмыс режимін таңдаңыз:",
        "btn_business": "🏢 Бизнеске арналған жарнама",
        "btn_reels": "🎬 Reels & TikTok жасау",
    },
    "ky": {
        "welcome": "Саламатсызбы! AI Video Maker ботуна кош келиңиз. 🚀\nӨзүңүзгө ыңгайлуу тилди тандаңыз:",
        "choose_mode": "Керектүү режимди тандаңыз:",
        "btn_business": "🏢 Бизнес үчүн жарнама",
        "btn_reels": "🎬 Reels & TikTok жасоо",
    },
    "tg": {
        "welcome": "Салом! Хуш омадед ба боти AI Video Maker. 🚀\nЗабони худро интихоб кунед:",
        "choose_mode": "Режими лозимиро интихоб кунед:",
        "btn_business": "🏢 Реклама барои бизнес",
        "btn_reels": "🎬 Сохтани Reels & TikTok",
    },
}

# /start komandasi - Til tanlash menyusini chiqarish
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        ],
        [
            InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk"),
            InlineKeyboardButton("🇰🇬 Кыргызча", callback_data="lang_ky"),
        ],
        [
            InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data="lang_tg"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Agar xabar orqali kelsa
    if update.message:
        await update.message.reply_text(
            "Assalomu alaykum! Добро пожаловать! Tilni tanlang / Выберите язык:",
            reply_markup=reply_markup
        )

# Tugmalarni bosganda ishlaydigan funksiya
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        context.user_data["language"] = lang # Tilni saqlab qo'yamiz
        
        # Tanlangan tildagi xush kelibsiz xabari va rejimlar menyusi
        t = TRANSLATIONS.get(lang, TRANSLATIONS["uz"])
        
        keyboard = [
            [InlineKeyboardButton(t["btn_business"], callback_data="mode_business")],
            [InlineKeyboardButton(t["btn_reels"], callback_data="mode_reels")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"{t['welcome']}\n\n{t['choose_mode']}",
            reply_markup=reply_markup
        )
        
    elif data == "mode_business":
        lang = context.user_data.get("language", "uz")
        # Keyingi bosqich: Biznes sohalarini chiqarishga o'tamiz
        await query.edit_message_text(
[10/21/2026 8:13 PM] Alisher: text="🏢 Kichik biznes turlarini tanlash bo'limi ochilmoqda...\n(Tez orada sohalar ro'yxati qo'shiladi)"
        )
        
    elif data == "mode_reels":
        lang = context.user_data.get("language", "uz")
        await query.edit_message_text(
            text="🎬 Reels & TikTok video yaratish bo'limi ochilmoqda...\n(Tez orada prompt yuborish imkoniyati qo'shiladi)"
        )

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Add your bot token in Environment Variables.")

    application = Application.builder().token(token).build()

    # Handlerlarni ulash
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Starting Telegram bot with long polling.")
    application.run_polling()

if name == "main":
    main()
