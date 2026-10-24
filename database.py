import aiosqlite

DB_FILE = "bot_database.db"

async def init_db():
    """
    Bot uchun ma'lumotlar bazasini yaratadi:
    1. Foydalanuvchilar jadvali (Balans, Til, Ro'yxatdan o'tgan sana)
    2. To'lovlar tarixi jadvali (Cheklar va kutilayotgan tranzaksiyalar)
    """
    async with aiosqlite.connect(DB_FILE) as db:
        # Foydalanuvchilar bazasi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                credits INTEGER DEFAULT 5, -- Bepul boshlang'ich 5 ta kredit
                language TEXT DEFAULT 'uz',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # To'lovlar va cheklar tarixi bazasi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_id TEXT,
                amount_usd REAL,
                amount_local TEXT,
                receipt_file_id TEXT,
                status TEXT DEFAULT 'pending', -- pending, approved, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_or_create_user(user_id: int, username: str, full_name: str) -> dict:
    """
    Foydalanuvchi botga birinchi marta kirganda bazaga qo'shadi,
    oldin kirgan bo'lsa uning ma'lumotlarini qaytaradi.
    """
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id, credits, language FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
            if row:
                return {"user_id": row[0], "credits": row[1], "language": row[2], "is_new": False}
            else:
                await db.execute(
                    "INSERT INTO users (user_id, username, full_name, credits) VALUES (?, ?, ?, ?)",
                    (user_id, username, full_name, 5)
                )
                await db.commit()
                return {"user_id": user_id, "credits": 5, "language": "uz", "is_new": True}


async def get_user_credits(user_id: int) -> int:
    """Foydalanuvchining joriy kredit balansini qaytaradi."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def update_user_credits(user_id: int, amount: int):
    """Foydalanuvchi balansiga kredit qo'shadi yoki ayiradi."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


async def set_user_language(user_id: int, lang: str):
    """Foydalanuvchining tanlagan tilini yangilaydi (uz, ru, kk, ky, tg)."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
        await db.commit()


async def create_payment_record(user_id: int, plan_id: str, amount_usd: float, amount_local: str, receipt_file_id: str) -> int:
    """Yangi to'lov cheki tashlanganda bazaga 'pending' holatida yozib qo'yadi."""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "INSERT INTO payments (user_id, plan_id, amount_usd, amount_local, receipt_file_id, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, plan_id, amount_usd, amount_local, receipt_file_id, 'pending')
        )
        await db.commit()
        return cursor.lastrowid
