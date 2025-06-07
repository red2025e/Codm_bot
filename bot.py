import logging
from aiogram import Bot, Dispatcher, types, executor
import os
import json

# Load token from environment variable
API_TOKEN = os.getenv("API_TOKEN")

# Load config from JSON file
with open("cp_bot_config.json", "r") as f:
    config = json.load(f)

ADMIN_USERNAME = config["admin_username"]
SOLANA_WALLET = config["solana_wallet"]
CP_PACKAGES = config["packages"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    for cp, price in CP_PACKAGES.items():
        keyboard.add(types.InlineKeyboardButton(f"{cp} ({price})", callback_data=cp))
    await message.answer("🎮 Welcome!\n\nSelect a CP package:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data in CP_PACKAGES)
async def handle_package_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    selected = callback_query.data
    user_data[user_id] = {"cp": selected}
    await bot.send_message(user_id, f"You selected *{selected}*. Please enter your UID:", parse_mode="Markdown")
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(lambda message: message.chat.id in user_data and "uid" not in user_data[message.chat.id])
async def get_uid(message: types.Message):
    user_id = message.chat.id
    user_data[user_id]["uid"] = message.text

    await message.answer("💸 Send a screenshot of your payment to the wallet below:\n\nSolana Address:")
    await message.answer(SOLANA_WALLET)

    cp = user_data[user_id]["cp"]
    uid = user_data[user_id]["uid"]
    username = message.from_user.username or "No username"

    admin_message = (
        f"🆕 New CP Order\n\n"
        f"👤 Username: @{username}\n"
        f"📦 Package: {cp}\n"
        f"🆔 UID: {uid}\n"
        f"💰 Amount: {CP_PACKAGES[cp]}"
    )
    await bot.send_message(chat_id=ADMIN_USERNAME, text=admin_message)

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    await message.reply("✅ Screenshot received! Your order is being processed.")
    await bot.send_photo(chat_id=ADMIN_USERNAME, photo=message.photo[-1].file_id, caption="🖼️ Payment screenshot")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
