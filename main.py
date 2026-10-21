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
        "choose_business_cat": "🏢 Biznes sohangizni tanlang:",
        "btn_cafe": "🍽️ Restoran & Kafe",
        "btn_shop": "👗 Kiyim-kechak & Butik",
        "btn_salon": "💅 Go‘zallik saloni",
        "btn_other": "🛒 Boshqa xizmatlar",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в AI Telegram Video Maker. 🚀\nПожалуйста, выберите язык:",
        "choose_mode": "Выберите режим работы:",
        "btn_business": "🏢 Реклама для бизнеса",
        "btn_reels": "🎬 Создать Reels & TikTok",
        "choose_business_cat": "🏢 Выберите сферу вашего бизнеса:",
        "btn_cafe": "🍽️ Ресторан & Кафе",
        "btn_shop": "👗 Одежда & Бутик",
        "btn_salon": "💅 Салон красоты",
        "btn_other": "🛒 Другие услуги",
    },
    "kk": {
        "welcome": "Сәлем! AI Video Maker ботына қош келдіңіз. 🚀\nӨзіңізге ыңғайлы тілді таңдаңыз:",
        "choose_mode": "Жұмыс режимін таңдаңыз:",
        "btn_business": "🏢 Бизнеске арналған жарнама",
        "btn_reels": "🎬 Reels & TikTok жасау",
        "choose_business_cat": "🏢 Бизнес саласын таңдаңыз:",
        "btn_cafe": "🍽️ Ресторан & Кафе",
        "btn_shop": "👗 Киім & Бутик",
        "btn_salon": "💅 Сұлулық салоны",
        "btn_other": "🛒 Басқа қызметтер",
    },
    "ky": {
        "welcome": "Саламатсызбы! AI Video Maker ботуна кош келиңиз. 🚀\nӨзүңүзгө ыңгайлуу тилди тандаңыз:",
        "choose_mode": "Керектүү режимди тандаңыз:",
        "btn_business": "🏢 Бизнес үчүн жарнама",
        "btn_reels": "🎬 Reels & TikTok жасоо",
        "choose_business_cat": "🏢 Бизнес багытын тандаңыз:",
        "btn_cafe": "🍽️ Ресторан & Кафе",
        "btn_shop": "👗 Киim & Бутик",
        "btn_salon": "💅 Сулуулук салону",
        "btn_other": "🛒 Башка кызматтар",
    },
    "tg": {
        "welcome": "Салом! Хуш омадед ба боти AI Video Maker. 🚀\nЗабони худро интихоб кунед:",
        "choose_mode": "Режими лозимиро интихоб кунед:",
        "btn_business": "🏢 Реклама барои бизнес",
        "btn_reels": "🎬 Сохтани Reels & TikTok",
        "choose_business_cat": "🏢 Соҳаи бизнеси худро интихоб кунед:",
        "btn_cafe": "🍽️ Ресторан & Кафе",
        "btn_shop": "👗 Либос & Бутик",
        "btn_salon": "💅 Салони зебоӣ",
        "btn_other": "🛒 Дигар хизматрасониҳо",
    },
}

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
    reply_markup = InlineKeyboardMarkup(
