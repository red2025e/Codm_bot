import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import os

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_USERNAME = "@REDDOT016"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderForm(StatesGroup):
    uid = State()
    payment = State()

cp_packages = [
    {"label": "3000 CP", "naira_price": "₦40,000"},
    {"label": "5000 CP", "naira_price": "₦58,000"},
    {"label": "10000 CP", "naira_price": "₦75,000"},
    {"label": "10800 CP", "naira_price": "₦80,000"},
    {"label": "15000 CP", "naira_price": "₦120,000"},
    {"label": "20000 CP", "naira_price": "₦140,000"},
]

user_orders = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for pkg in cp_packages:
        label = f"{pkg['label']} ({pkg['naira_price']})"
        kb.add(InlineKeyboardButton(text=label, callback_data=pkg['label']))
    await message.answer("👾 Welcome!\nSelect a CP package below:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.endswith("CP"))
async def package_selected(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(package=callback_query.data)
    user_orders[callback_query.from_user.id] = {"package": callback_query.data}
    await bot.send_message(callback_query.from_user.id, f"💎 You selected {callback_query.data}\n\nNow enter your UID:")
    await OrderForm.uid.set()

@dp.message_handler(state=OrderForm.uid)
async def uid_received(message: types.Message, state: FSMContext):
    await state.update_data(uid=message.text)
    data = await state.get_data()
    user_orders[message.from_user.id]['uid'] = message.text

    await message.answer(
        f"📸 Send a screenshot of your payment to the wallet below:\n\n"
        f"Solana Address:\n`2BW8GnRa36iy5V9ihJZrssPYYfx37G16z8JSFdVfUrsg`",
        parse_mode="Markdown"
    )
    await OrderForm.payment.set()

@dp.message_handler(state=OrderForm.payment, content_types=types.ContentTypes.PHOTO)
async def screenshot_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get('uid')
    package = data.get('package')
    photo_id = message.photo[-1].file_id

    await message.reply("✅ Thanks! We've received your payment. Your order is being processed.")

    caption = (
        "🧾 *New CP Order!*\n\n"
        f"💠 *Package:* {package}\n"
        f"🆔 *UID:* `{uid}`\n"
        f"👤 *From:* @{message.from_user.username if message.from_user.username else message.from_user.full_name}"
    )

    await bot.send_photo(chat_id=ADMIN_USERNAME, photo=photo_id, caption=caption, parse_mode="Markdown")
    await state.finish()

@dp.message_handler(lambda message: "sent" in message.text.lower(), state=OrderForm.payment)
async def sent_text_handler(message: types.Message):
    await message.reply("✅ Thanks! Please make sure to upload the screenshot as well so we can verify your payment.")

