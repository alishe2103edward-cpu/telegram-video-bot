import os
import time
import httpx
from dotenv import load_dotenv

# .env faylidagi yashirin o'zgaruvchilarni yuklash
load_dotenv()

# =====================================================================
# 1. XAVFSIZ API KALITLAR (Railway Variables yoki .env ichidan o'qiladi)
# =====================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip('"').strip("'")
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY") or "").strip().strip('"').strip("'")
FAL_KEY = (os.getenv("FAL_KEY") or os.getenv("FAL_API_KEY") or "").strip().strip('"').strip("'")
ELEVENLABS_API_KEY = (os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_KEY") or "").strip().strip('"').strip("'")

# Railway Variables ichida qanday kalitlar borligini tekshirish uchun:
print("RAILWAY MAVJUD KALITLAR:", [k for k in os.environ.keys() if "KEY" in k or "TOKEN" in k or "OPENAI" in k or "FAL" in k])

# Admin Telegram ID (Cheklarni tasdiqlash va tizimni boshqarish uchun)
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()
]

# =====================================================================
# 2. TO'LOV KARTALARI VA XALQARO HAVOLALAR (KRIPTOVALYUTASIZ!)
# =====================================================================
PAYMENT_CARDS = {
    "uzcard_number": os.getenv("UZCARD_NUMBER", "8600   "),
    "humo_number": os.getenv("HUMO_NUMBER", "9860   "),
    "card_holder": os.getenv("CARD_HOLDER_NAME", "SADRIDDIN K."),
    # Visa / Mastercard (Lemon Squeezy yoki Paddle to'lov havolalari)
    "intl_link_start": os.getenv("INTL_LINK_START", "https://yourstore.lemonsqueezy.com/buy/start"),
    "intl_link_biz": os.getenv("INTL_LINK_BIZ", "https://yourstore.lemonsqueezy.com/buy/biznes"),
    "intl_link_vip": os.getenv("INTL_LINK_VIP", "https://yourstore.lemonsqueezy.com/buy/vip"),
}

# =====================================================================
# 3. VIDEO DAVOMIYLIGI VA KREDIT SARFI (3 POG'ONALI TIZIM)
# =====================================================================
VIDEO_DURATION_TIERS = {
    "standart_40s": {
        "title": "⚡️ STANDART (40-45 soniya)",
        "seconds": 40,
        "scenes_count": 4,       # 4 ta kadr (har biri ~10s)
        "credits_cost": 10,      # 10 kredit
        "bonus_stories": False,
        "bonus_poster": False,
    },
    "optimal_75s": {
        "title": "🔥 OPTIMAL (60-75 soniya + AI Aktyor)",
        "seconds": 75,
        "scenes_count": 7,       # 7 ta kadr (Mahsulot + UGC Aktyor + Detallar)
        "credits_cost": 20,      # 20 kredit
        "bonus_stories": True,    # +15s Stories qirqimi bepul
        "bonus_poster": False,
    },
    "vip_120s": {
        "title": "👑 VIP MINI-FILM (90-120 soniya + Sotuv Voronkasi)",
        "seconds": 120,
        "scenes_count": 10,      # 10 ta kadr (To'liq hikoya va obzor)
        "credits_cost": 30,      # 30 kredit
        "bonus_stories": True,    # +15s Stories qirqimi bepul
        "bonus_poster": True,     # +4K Sotuvchi Poster bepul
    },
}

# =====================================================================
# 4. TARIF REJALARI (VITRINADA DOLLARDA KO'RINADI)
# =====================================================================
PRICING_TIERS = {
    "start": {
        "id": "start",
        "name": "🚀 START",
        "credits": 10,           # 1 ta 40s Standart video
        "price_usd": 5.50,       # ~69 000 so'm
        "watermark": False,
        "multi_brand": 1,
    },
    "biznes": {
        "id": "biznes",
        "name": "🔥 BIZNES",
        "credits": 60,           # 6 ta 40s yoki 3 ta 75s Optimal video
        "price_usd": 27.00,      # ~349 000 so'm
        "watermark": False,
        "multi_brand": 3,
    },
    "vip": {
        "id": "vip",
        "name": "👑 VIP AGENTLIK",
        "credits": 200,          # 20 ta 40s yoki 6-7 ta 120s VIP Film
        "price_usd": 49.00,      # ~649 000 so'm (Super tejamkor langar narx!)
        "watermark": False,
        "multi_brand": 10,       # SMMchilar uchun 10 ta brend profili
    },
}
