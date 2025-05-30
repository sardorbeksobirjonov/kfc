import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === BOT TOKEN ===
TOKEN = "7712398717:AAGafUU_PZ57OWoNFvdI3kFOECw5PKuYSKo"  # O'z tokeningizni yozing

# === ADMIN MA'LUMOTLARI ===
ADMINS = [7700441769]
ADMIN_CONTACTS = [
    "@junior_developmentt",
    "@itssasilbee",
    "+998 97 609 41 02"
]

# === GLOBAL FOYDALANUVCHILAR RO'YXATI ===
users = set()

# === FSM HOLATLARI ===
class OrderStates(StatesGroup):
    waiting_for_order = State()
    waiting_for_phone = State()

# === BOT VA DISPATCHER ===
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === MENYU MATNI ===
menu_text = (
    "🍗 <b>YFC\nYangiyol Fried Chicken</b> 🍗\n\n"
    "🔥 <b>Qanot</b>\n1 kg • 75.000\n0,5 kg • 40.000\n1 portsa • 25.000\n\n"
    "🥩 <b>Laxim</b>\n1 kg • 80.000\n0,5 kg • 40.000\n1 portsa • 28.000"
)

# === BOSHLANG'ICH KOMANDA ===
@dp.message(CommandStart())
async def start_handler(msg: Message):
    users.add(msg.from_user.id)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Menyu"), KeyboardButton(text="🛒 Buyurtma berish")]
        ],
        resize_keyboard=True,
        row_width=2
    )

    await msg.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "🍟 Bu bot orqali YFC menyusini ko'rishingiz yoki buyurtma berishingiz mumkin.\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=keyboard
    )

# === MENYU KO'RSATISH ===
@dp.message(F.text == "📋 Menyu")
async def menu_handler(msg: Message):
    await msg.answer(menu_text, parse_mode="HTML")

# === BUYURTMA BOSQICHLARI ===

# 1. Buyurtma nomini so'rash
@dp.message(F.text == "🛒 Buyurtma berish")
async def order_request_handler(msg: Message, state: FSMContext):
    await msg.answer("📝 <b>Buyurtma nomini yozing (masalan: Qanot 1 kg):</b>", parse_mode="HTML")
    await state.set_state(OrderStates.waiting_for_order)

# 2. Buyurtma nomini qabul qilish va telefon raqamini so'rash
@dp.message(OrderStates.waiting_for_order)
async def process_order(msg: Message, state: FSMContext):
    order_text = msg.text.strip()
    await state.update_data(order=order_text)

    await msg.answer("📞 <b>Iltimos, telefon raqamingizni kiriting:</b>", parse_mode="HTML")
    await state.set_state(OrderStates.waiting_for_phone)

# 3. Telefon raqamini qabul qilish va adminlarga yuborish
@dp.message(OrderStates.waiting_for_phone)
async def process_phone(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    user_id = msg.from_user.id
    username = msg.from_user.username
    display_name = f"@{username}" if username else msg.from_user.full_name

    data = await state.get_data()
    order_text = data.get("order")

    users.add(user_id)

    # Adminlarga buyurtma va telefon raqamini yuborish
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📥 <b>Yangi buyurtma</b>\n\n"
                    f"👤 Foydalanuvchi: <a href='tg://user?id={user_id}'>{display_name}</a>\n"
                    f"🆔 ID: <a href='tg://user?id={user_id}'>{user_id}</a>\n"
                    f"📦 Buyurtma: <code>{order_text}</code>\n"
                    f"📞 Telefon raqami: <code>{phone}</code>"
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xatolik: {e}")

    # Foydalanuvchiga javob
    await msg.answer(
        "✅ <b>Buyurtmangiz qabul qilindi!\n"
        "Biz tez orada siz bilan bog'lanamiz.</b>\n\n"
        "📞 Admin bilan bog'lanish:\n"
        f"👤 {ADMIN_CONTACTS[0]}\n"
        f"👤 {ADMIN_CONTACTS[1]}\n"
        f"Rasmiy Yangiyol Chicken 🐔\n"
        f"📱 {ADMIN_CONTACTS[2]}",
        parse_mode="HTML"
    )
    await state.clear()

# === ADMIN: FOYDALANUVCHILARNI KO'RISH ===
@dp.message(F.text == "/users")
async def users_list_handler(msg: Message):
    if msg.from_user.id in ADMINS:
        if not users:
            await msg.answer("📛 Hozircha foydalanuvchi yo'q.")
            return

        user_text = "📊 <b>Bot foydalanuvchilari:</b>\n\n"
        for uid in users:
            user_text += f"🔹 <a href='tg://user?id={uid}'>Foydalanuvchi</a> — <code>{uid}</code>\n"
        await msg.answer(user_text, parse_mode="HTML")
    else:
        await msg.answer("❌ Sizda bu komandani ishlatish huquqi yo'q.")

# === ADMIN: REKLAMA TARQATISH ===
@dp.message(F.text.startswith("/reklama "))
async def reklama_handler(msg: Message):
    if msg.from_user.id in ADMINS:
        reklama_matni = msg.text[len("/reklama "):].strip()
        count = 0
        for uid in users:
            try:
                await bot.send_message(uid, f"📢 <b>Yangi xabar:</b>\n\n{reklama_matni}", parse_mode="HTML")
                count += 1
            except Exception:
                continue
        await msg.answer(f"✅ Reklama {count} foydalanuvchiga yuborildi.")
    else:
        await msg.answer("❌ Sizda bu komandani ishlatish huquqi yo'q.")

# === NOANIQ XABARLAR UCHUN (faqat matn bo‘lmaganlar uchun) ===
@dp.message(F.text.not_in({"📋 Menyu", "🛒 Buyurtma berish"}) & ~F.text.startswith("/") & ~F.text)
async def unknown_handler(msg: Message):
    await msg.answer(
        "❗ So‘rovingiz bo‘yicha ma’lumot topilmadi.\n"
        "Iltimos, admin bilan bog‘laning:\n"
        f"👤 {ADMIN_CONTACTS[0]}\n"
        f"👤 {ADMIN_CONTACTS[1]}\n"
        f"Rasmiy Yangiyol Chicken 🐔\n"
        f"📱 {ADMIN_CONTACTS[2]}"
    )

# === ASOSIY FUNKSIYA ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
