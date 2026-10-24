import os
import time
import httpx
from dotenv import load_dotenv

# .env faylidagi yashirin o'zgaruvchilarni yuklash
load_dotenv()

# =====================================================================
# 1. XAVFSIZ API KALITLAR (Railway Variables yoki .env ichidan o'qiladi)
# =====================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Admin Telegram ID (Cheklarni tasdiqlash va tizimni boshqarish uchun)
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()
]

# =====================================================================
# 2. TO'LOV KARTALARI VA XALQARO HAVOLALAR (KRIPTOVALYUTASIZ!)
# =====================================================================
PAYMENT_CARDS = {
    "uzcard_number": os.getenv("UZCARD_NUMBER", "8600 **  **"),
    "humo_number": os.getenv("HUMO_NUMBER", "9860 **  **"),
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
        "title": "⚡ STANDART (40-45 soniya)",
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
PRICING_PLANS = {
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

# =====================================================================
# 5. JONLI VALYUTA KURSI KONVERTORI ($ -> UZS, KZT, TJS, KGS)
# =====================================================================
# Internet uzilganda ishlatiladigan zaxira (Fallback) kurslar
FALLBACK_RATES = {
    "UZS": float(os.getenv("DEFAULT_USD_UZS", "12850.0")),
    "KZT": 485.0,
    "TJS": 10.9,
    "KGS": 86.5,
    "RUB": 96.0,
}

# Kursni har safar so'ramaslik uchun 1 soatlik kesh (Cache)
_RATE_CACHE = {"timestamp": 0, "rates": FALLBACK_RATES.copy()}
BANK_SPREAD_BUFFER = 1.01  # +1% bank konvertatsiya zaxirasi


async def get_live_exchange_rates() -> dict:
    """
    O'zbekiston Markaziy Banki (cbu.uz) va Xalqaro API orqali
    1$ ning bugungi kursini avtomatik oladi (1 soat kesh bilan).
    """
    now = time.time()
    if now - _RATE_CACHE["timestamp"] < 3600:
        return _RATE_CACHE["rates"]

    rates = FALLBACK_RATES.copy()
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1) O'zbekiston Markaziy Bankidan aniq UZS kursini olish
        try:
            resp = await client.get("https://cbu.uz/oz/arkhiv-kursov-valyut/json/USD/")
            if resp.status_code == 200:
                data = resp.json()
                if data and "Rate" in data[0]:
                    rates["UZS"] = float(data[0]["Rate"]) * BANK_SPREAD_BUFFER
        except Exception:
            pass

        # 2) Qo'shni davlatlar (KZT, TJS, KGS) kursini olish
        try:
            resp2 = await client.get("https://open.er-api.com/v6/latest/USD")
            if resp2.status_code == 200:
                er_data = resp2.json().get("rates", {})
                for code in ("KZT", "TJS", "KGS", "RUB"):
                    if code in er_data:
                        rates[code] = float(er_data[code]) * BANK_SPREAD_BUFFER
        except Exception:
            pass

    _RATE_CACHE["timestamp"] = now
    _RATE_CACHE["rates"] = rates
    return rates


async def calculate_local_payment(price_usd: float) -> dict:
    """
    Mijoz tanlagan $ dagi tarifni bugungi kurs bo'yicha
    So'm (UZS) va qo'shni valyutalarda chiroyli yaxlitlab hisoblab beradi.
    """
    rates = await get_live_exchange_rates()
    raw_uzs = price_usd * rates["UZS"]

    # Oxirgi 3 ta raqamni minglikka chiroyli yaxlitlash (masalan: 346 950 -> 347 000 so'm)
    rounded_uzs = int(round(raw_uzs / 1000.0) * 1000)

    return {
        "price_usd": price_usd,
        "usd_to_uzs_rate": int(rates["UZS"]),
        "amount_uzs": rounded_uzs,
        "amount_uzs_formatted": f"{rounded_uzs:,}".replace(",", " "),
        "approx_tjs": int(round(price_usd * rates["TJS"])),   # Tojikistonliklar uchun ma'lumot
        "approx_kzt": int(round(price_usd * rates["KZT"], -2)), # Qozog'istonliklar uchun ma'lumot
        "approx_kgs": int(round(price_usd * rates["KGS"], -1)), # Qirg'izistonliklar uchun ma'lumot
    }
