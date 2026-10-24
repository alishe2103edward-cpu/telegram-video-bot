from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from database import get_or_create_user, set_user_language, get_user_credits

router = Router()

# Til tanlash klaviaturasi
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton(text="🇰🇿 Қазақcha", callback_data="lang_kk"),
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tg")
        ]
    ])

# Asosiy menyu klaviaturasi
def get_main_menu(lang: str = 'uz'):
    # Hozircha oddiy matnli tugmalar bilan boshlaymiz
    if lang == 'ru':
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Создать видео (AI)", callback_data="create_video")],
            [InlineKeyboardButton(text="💳 Мой баланс / Пополнить", callback_data="balance"), InlineKeyboardButton(text="🌐 Язык", callback_data="settings_lang")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Video yaratish (AI)", callback_data="create_video")],
            [InlineKeyboardButton(text="💳 Balansim / To'ldirish", callback_data="balance"), InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="settings_lang")]
        ])

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Foydalanuvchi /start bosganda ishga tushadi"""
    user = await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        f"🤖 Men sun'iy intellekt asosida ishlaydigan professional Video & UGC Marketolog botiman.\n"
        f"Sizga bitta rasm va qisqa g‘oya orqali millionlab ko‘rish olib keluvchi marketing videolarini yasab beraman.\n\n"
        f"🎁 Sizga sovg‘a sifatida {user['credits']} ta bepul kredit taqdim etildi!\n\n"
        f"Marhamat, o'zingizga qulay tilni tanlang:"
    )
    
    await message.answer(welcome_text, reply_markup=get_language_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    """Til tanlanganda ishlaydi"""
    lang = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang)
    
    texts = {
        'uz': "✅ Til muvaffaqiyatli o'zgartirildi: O'zbekcha\n\nKerakli bo'limni tanlang:",
        'ru': "✅ Язык успешно изменен: Русский\n\nВыберите нужный раздел:",
        'kk': "✅ Til сәтті өзгертілді: Қазақша\n\nҚажетті бөлімді таңдаңыз:",
        'tg': "✅ Zabong bo'yicha муваффақиятгузошт шуд: Тоҷикӣ\n\nҚисми лозимиро интихоб кунед:"
    }
    
    await callback.message.edit_text(
        texts.get(lang, texts['uz']),
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    """Foydalanuvchi balansini ko'rsatish"""
    credits = await get_user_credits(callback.from_user.id)
    balance_text = (
        f"💳 Sizning balansingiz:\n\n"
        f"⚡️ Qolgan kreditlar: {credits} ta\n\n"
        f"Videolarni davom ettirish va ko'proq yaratish uchun tarifni tanlang yoki balansingizni to'ldiring:"
    )
    # Bu yerga keyingi bosqichda to'lov tariflarini ulaymiz ($5.50, $27, $49)
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(balance_text, reply_markup=back_kb, parse_mode="Markdown")
    await callback.answer()
[10/25/2026 12:32 AM] Alisher: @router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 Asosiy menyu:\nKerakli bo'limni tanlang:",
        reply_markup=get_main_menu('uz'),
        parse_mode="Markdown"
    )
    await callback.answer()
