import os
import json
import httpx
import fal_client
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, ELEVENLABS_API_KEY, FAL_KEY

# Fal.ai kalitini tizimga tanitamiz
os.environ["FAL_KEY"] = FAL_KEY

# OpenAI mijozini ishga tushiramiz
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ==========================================
# 1. ETIK FILTR VA SSENARIY GENERATORI (GPT-4o)
# ==========================================
async def moderate_and_generate_script(user_text: str, image_url: str = None, lang: str = "uz") -> dict:
    """
    1. Mahsulotni etik va qonuniy filtrdan o'tkazadi (Alkogol, tamaki, dorilar, 18+ qat'iyan taqiqlanadi).
    2. Ruxsat berilsa, sotuvbop UGC marketing ssenariysi va vizual prompt tuzadi.
    """
    system_prompt = f"""
    Sen qat'iy etik nazoratchi va professional UGC Marketing Rejissyorisan.
    
    1-QADAM: XAVFSIZLIK VA ETIK TEKSHIRUV (QAT'IY!)
    Foydalanuvchi yuborgan matn va rasmni tekshir. Agar mahsulot yoki g'oya quyidagilarga aloqador bo'lsa, DARHOL RAD ET:
    - Alkogol va spirtli ichimliklar (pivo, vino, aroq va h.k.)
    - Tamaki, sigaret, veyp, kalyan, nosvoy
    - Narkotik moddalar va psixotrop vositalar
    - Har qanday tibbiy dorilar, tabletkalar, farmatsevtika mahsulotlari, БАДlar
    - Axloqsiz, uyatsiz (18+), qimor (betting/kazino) yoki noqonuniy narsalar.

    2-QADAM: SSENARIY VA VIZUAL REJA
    Agar mahsulot toza va ruxsat etilgan bo'lsa (masalan: oziq-ovqat, kiyim, agro, xizmatlar, texnika, ta'lim va h.k.), '{lang}' tilida 30-45 soniyalik kuchli marketing ssenariysi yoz.
    Vizual prompt (visual_prompt) ichida HECH QACHON alkogol, shisha idishdagi spirtli ichimlik yoki sigaret tasvirini qo'shma!

    Javobni FAQAT quyidagi JSON formatida qaytar:
    {{
        "is_safe": true yoki false,
        "violation_reason": "Agar is_safe false bo'lsa, foydalanuvchiga '{lang}' tilida xushmuomalalik bilan rad etish sababi (masalan: Kechirasiz, bizning botimiz orqali alkogol, tamaki, dori vositalari va axloqqa zid mahsulotlar uchun video tayyorlash qat'iyan man etiladi.)",
        "voiceover_text": "Diktor o'qib beradigan to'liq, emotsional va sotuvbop matn ('{lang}' tilida)",
        "visual_prompt": "Fal.ai video generatori uchun ingliz tilida yuqori sifatli kinematik prompt (masalan: 'Cinematic 3D commercial of..., photorealistic, 8k, smooth camera motion, no alcohol, family friendly')"
    }}
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    user_content = [{"type": "text", "text": f"Mahsulot tavsifi: {user_text}"}]
    if image_url:
        user_content.append({"type": "image_url", "image_url": {"url": image_url}})
        
    messages.append({"role": "user", "content": user_content})

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=messages,
        temperature=0.7
    )

    return json.loads(response.choices[0].message.content)


# ==========================================
# 2. JONLI DIKTOR OVOZI (ElevenLabs API)
# ==========================================
async def generate_voiceover(text: str, output_path: str = "voiceover.mp3") -> str:
    """Matnni tabiiy va emotsional diktor ovoziga aylantiradi."""
    # Adam (universal, chuqur va ishonchli erkak diktor ovozi)
    voice_id = "pNInz6obpgDQGcFmaJgB"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
            
    return output_path
[10/25/2026 12:34 AM] Alisher: # ==========================================
# 3. AI VIDEO VA VIZUAL GENERATOR (Fal.ai - Kling / Flux)
# ==========================================
async def generate_ai_video(visual_prompt: str, image_url: str = None) -> str:
    """
    Rasm va prompt asosida Fal.ai orqali kinematik video yaratadi.
    """
    if image_url:
        # Rasmni jonlantirish (Image-to-Video)
        handler = await fal_client.submit_async(
            "fal-ai/kling-video/v1/standard/image-to-video",
            arguments={
                "prompt": visual_prompt,
                "image_url": image_url,
                "duration": "5",
                "aspect_ratio": "9:16"
            }
        )
    else:
        # Matndan to'g'ridan-to'g'ri video yaratish (Text-to-Video)
        handler = await fal_client.submit_async(
            "fal-ai/kling-video/v1/standard/text-to-video",
            arguments={
                "prompt": visual_prompt,
                "duration": "5",
                "aspect_ratio": "9:16"
            }
        )
        
    result = await handler.get()
    return result["video"]["url"]


# ==========================================
# 4. TO'LOV CHEKINI SKANERLASH (GPT-4o Vision)
# ==========================================
async def verify_payment_receipt(image_url: str, expected_amount_str: str) -> dict:
    """
    Mijoz yuborgan bank cheki (Uzcard/Humo/Kaspi va h.k.) skrinshotini o'qiydi va tekshiradi.
    """
    prompt = f"""
    Ushbu to'lov cheki (kvitansiya) rasmiga qara.
    Kutilayotgan to'lov miqdori: {expected_amount_str}.
    
    Quyidagilarni aniqla va FAQAT JSON formatida javob qaytar:
    {{
        "is_valid_receipt": true yoki false (haqiqiy bank o'tkazmasi chekimi?),
        "extracted_amount": "Chekda yozilgan summa va valyuta",
        "status_success": true yoki false (To'lov muvaffaqiyatli/bajarildi deb yozilganmi?),
        "summary": "Admin uchun qisqa xulosa (O'zbek tilida)"
    }}
    """
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    )
    
    return json.loads(response.choices[0].message.content)
