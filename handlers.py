import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import PRICING_TIERS, ADMIN_IDS
from database import (
    get_or_create_user, set_user_language, get_user_credits, 
    update_user_credits, create_payment_record
)
from ai_services import (
    moderate_and_generate_script, generate_voiceover, 
    generate_ai_video, verify_payment_receipt
)

router = Router()

# Muloqot bosqichlari (FSM States)
class BotStates(StatesGroup):
    waiting_for_product = State()
    waiting_for_receipt = State()

# Til tanlash klaviaturasi
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kk"),
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tg")
        ]
    ])

# Asosiy menyu klaviaturasi
def get_main_menu(lang: str = 'uz'):
    if lang == 'ru':
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Создать видео (AI)", callback_data="create_video")],
            [InlineKeyboardButton(text="💳 Мой баланс / Тарифы", callback_data="balance"), InlineKeyboardButton(text="🌐 Язык", callback_data="settings_lang")]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Video yaratish (AI)", callback_data="create_video")],
        [InlineKeyboardButton(text="💳 Balansim / Tariflar", callback_data="balance"), InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="settings_lang")]
    ])


# ==========================================
# /START VA TIL SOZLAMALARI
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "user",
        full_name=message.from_user.full_name
    )
    
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        f"🤖 Men sun'iy intellekt asosida ishlaydigan professional Video & UGC Marketolog botiman.\n"
        f"Sizga bitta rasm va qisqa g‘oya orqali yuqori sifatli marketing videolarini yasab beraman.\n\n"
        f"⚠️ Muhim qoida: Bot orqali alkogol, tamaki, dori vositalari (farmatsevtika) hamda axloq me'yorlariga zid mahsulotlar uchun video yaratish qat'iyan man etiladi!\n\n"
        f"🎁 Sizning boshlang‘ich balansingiz: {user['credits']} ta kredit.\n\n"
        f"Marhamat, o'zingizga qulay tilni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_language_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "settings_lang")
async def change_lang_menu(callback: CallbackQuery):
    await callback.message.edit_text("🌐 Tilni tanlang / Выберите язык:", reply_markup=get_language_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang)
    
    await callback.message.edit_text(
        "✅ Til saqlandi! Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown"
    )
    await callback.answer()
@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🤖 Asosiy menyu:\nKerakli bo'limni tanlang:",
        reply_markup=get_main_menu('uz'),
        parse_mode="Markdown"
    )
    await callback.answer()


# ==========================================
# VIDEO YARATISH VA ETIK FILTR JARAYONI
# ==========================================
@router.callback_query(F.data == "create_video")
async def start_video_creation(callback: CallbackQuery, state: FSMContext):
    credits = await get_user_credits(callback.from_user.id)
    if credits < 5:
        await callback.answer("⚠️ Balansingizda yetarli kredit yo'q! Iltimos, hisobingizni to'ldiring.", show_alert=True)
        return await show_balance(callback)
    
    await state.set_state(BotStates.waiting_for_product)
    text = (
        "🎬 AI Video Yaratish Studiyasi\n\n"
        "Menga mahsulotingiz rasmini (bitta rasm ustiga izoh yozib) yoki shunchaki mahsulot haqida qisqacha ma'lumot yuboring.\n\n"
        "🚫 *Eslatma: Alkogol, tamaki, sigaret, narko/tibbiy dorilar va uyatsiz mahsulotlar avtomatik bloklanadi!*\n"
        "💎 *Narxi: 5 kredit*"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="back_to_main")]])
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="Markdown")
    await callback.answer()


@router.message(BotStates.waiting_for_product)
async def handle_product_input(message: Message, state: FSMContext, bot: Bot):
    user_text = message.caption or message.text
    if not user_text:
        return await message.answer("⚠️ Iltimos, rasm bilan birga mahsulot haqida qisqa izoh (yoki matnning o'zini) ham yozib yuboring!")

    image_url = None
    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

    status_msg = await message.answer("🔍 1/3: Mahsulot xavfsizlik qoidalariga tekshirilmoqda va marketing ssenariysi tuzilmoqda...", parse_mode="Markdown")

    try:
        # 1. Etik filtr va Ssenariy (GPT-4o)
        ai_data = await moderate_and_generate_script(user_text=user_text, image_url=image_url, lang="uz")
        
        if not ai_data.get("is_safe", False):
            await state.clear()
            reason = ai_data.get("violation_reason", "Taqiqlangan mahsulot aniqlandi.")
            return await status_msg.edit_text(f"🚫 Generatsiya rad etildi!\n\n{reason}\n\n*(Balansingizdan kredit yechilmadi)*", parse_mode="Markdown")

        voiceover_text = ai_data["voiceover_text"]
        visual_prompt = ai_data["visual_prompt"]

        # 2. Diktor ovozini yaratish (ElevenLabs)
        await status_msg.edit_text(f"🎙 2/3: Ssenariy tayyor! Jonli diktor ovozi yozilmoqda...\n\n📝 *Matn:* _{voiceover_text}_", parse_mode="Markdown")
        audio_path = f"voice_{message.from_user.id}.mp3"
        await generate_voiceover(voiceover_text, output_path=audio_path)

        # 3. Video generatsiya qilish (Fal.ai - Kling)
        await status_msg.edit_text("🎥 3/3: AI Video kadrlar va 3D vizual effektlar generatsiya qilinmoqda (bu 1-2 daqiqa vaqt olishi mumkin, iltimos kuting)...", parse_mode="Markdown")
        video_url = await generate_ai_video(visual_prompt=visual_prompt, image_url=image_url)

        # Kreditni yechish (-5 kredit)
        await update_user_credits(message.from_user.id, -5)
        remaining = await get_user_credits(message.from_user.id)

        # Natijalarni yuborish
        await status_msg.delete()
        await message.answer_video(
            video=video_url,
caption=f"✅ Videongiz tayyor!\n\n📝 Ssenariy:\n{voiceover_text}\n\n⚡️ Qolgan balans: {remaining} kredit",
            parse_mode="Markdown"
        )
        
        # Diktor audio faylini alohida yuborish
        audio_file = FSInputFile(audio_path)
        await message.answer_audio(audio=audio_file, caption="🎙 Studiyaviy diktor ovozi (MP3) — videoga montajda ulash yoki Reels uchun tayyor!")
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        await state.clear()

    except Exception as e:
        await state.clear()
        await status_msg.edit_text(f"⚠️ Texnik xatolik yuz berdi: {str(e)}\n*(Kreditlaringiz saqlanib qoldi)*")


# ==========================================
# BALANS, TARIFLAR VA TO'LOV TIZIMI
# ==========================================
@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    credits = await get_user_credits(callback.from_user.id)
    text = (
        f"💳 Sizning balansingiz: {credits} kredit\n\n"
        f"⚠️ *Diqqat: Kredit xarid qilishdan avval eslatib o'tamiz — alkogol, tamaki, dori vositalari va axloqsiz mahsulotlar uchun bot ishlamaydi!*\n\n"
        f"📦 Tariflardan birini tanlang:"
    )
    
    buttons = []
    for plan_id, info in PRICING_TIERS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{info['name']} — ${info['price_usd']} ({info['credits']} kredit)",
                callback_data=f"buy_{plan_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def select_plan(callback: CallbackQuery, state: FSMContext):
    plan_id = callback.data.split("_")[1]
    plan = PRICING_TIERS.get(plan_id)
    if not plan:
        return await callback.answer("Xato tarif!")

    # CBU kursi bo'yicha so'mdagi narxni hisoblash
    local_price_str = await get_local_price(plan["price_usd"], "uz")
    
    await state.update_data(plan_id=plan_id, amount_usd=plan["price_usd"], amount_local=local_price_str, credits=plan["credits"])
    await state.set_state(BotStates.waiting_for_receipt)

    text = (
        f"💎 Tanlangan tarif: {plan['name']} ({plan['credits']} kredit)\n"
        f"💵 Narxi: ${plan['price_usd']} (~ {local_price_str})\n\n"
        f"💳 To'lov uchun rekvizitlar:\n"
        f"• Uzcard: {UZCARD_NUMBER}\n"
        f"• Humo: {HUMO_NUMBER}\n"
        f"• Qabul qiluvchi: {CARD_HOLDER_NAME}\n\n"
        f"📸 Yuqoridagi kartalardan biriga {local_price_str} o'tkazing va to'lov cheki (skrinshot) rasmini shu yerga yuboring!"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="balance")]])
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="Markdown")
    await callback.answer()


@router.message(BotStates.waiting_for_receipt, F.photo)
async def handle_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo = message.photo[-1]
    
    wait_msg = await message.answer("⏳ Chek AI skaneri orqali tekshirilmoqda...")
    
    file_info = await bot.get_file(photo.file_id)
    image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

    # GPT-4o Vision orqali chekni o'qish
    scan_result = await verify_payment_receipt(image_url, data["amount_local"])
    
    payment_id = await create_payment_record(
        user_id=message.from_user.id,
        plan_id=data["plan_id"],
        amount_usd=data["amount_usd"],
        amount_local=data["amount_local"],
        receipt_file_id=photo.file_id
    )
# Adminlarga xabar va tasdiqlash tugmasini yuborish
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}_{data['credits']}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
        ]
    ])
    
    admin_caption = (
        f"🔔 Yangi To'lov Cheki (#{payment_id})\n\n"
        f"👤 Mijoz: {message.from_user.full_name} ({message.from_user.id})\n"
        f"📦 Tarif: {data['plan_id'].upper()} ({data['credits']} kredit)\n"
        f"💰 Kutilgan summa: {data['amount_local']}\n\n"
        f"🤖 AI Skaner Xulosasi:\n"
        f"• Haqiqiy chekmi: {'Ha' if scan_result.get('is_valid_receipt') else 'Shubhali'}\n"
        f"• Chekdagi summa: {scan_result.get('extracted_amount')}\n"
        f"• Xulosa: _{scan_result.get('summary')}_"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=photo.file_id, caption=admin_caption, reply_markup=admin_kb, parse_mode="Markdown")
        except Exception:
            pass

    await state.clear()
    await wait_msg.edit_text("✅ To'lov chekingiz qabul qilindi!\nAI tekshiruvidan o'tdi. Admin tasdiqlashi bilan balansingizga kreditlar avtomatik qo'shiladi.", parse_mode="Markdown")


# ==========================================
# ADMIN TASDIQLASH PANELI
# ==========================================
@router.callback_query(F.data.startswith("approve_"))
async def admin_approve_payment(callback: CallbackQuery, bot: Bot):
    _, user_id_str, credits_str = callback.data.split("_")
    user_id, credits = int(user_id_str), int(credits_str)
    
    await update_user_credits(user_id, credits)
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ TASDIQLANDI!", parse_mode="Markdown")
    
    try:
        await bot.send_message(user_id, f"🎉 To'lovingiz tasdiqlandi!\nHisobingizga {credits} ta kredit qo'shildi. Marhamat, videolar yaratishingiz mumkin!", parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("To'lov tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_"))
async def admin_reject_payment(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ RAD ETILDI!", parse_mode="Markdown")
    
    try:
        await bot.send_message(user_id, "❌ Kechirasiz, yuborgan to'lov chekingiz tasdiqlanmadi. Iltimos, qaytadan tekshirib yuboring.", parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("To'lov rad etildi!")
