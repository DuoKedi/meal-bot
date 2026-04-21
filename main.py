import asyncio
import logging
import json
import time
from os import getenv
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import AsyncOpenAI

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sysprompt import prompt


load_dotenv()


BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set!")

bot = Bot(token=BOT_TOKEN)

access = json.loads(getenv("access", "[]"))
MODEL = getenv("MODEL")
API = getenv("API")

client = AsyncOpenAI(
    api_key=API,
    base_url="https://api.groq.com/openai/v1"
)

dp = Dispatcher()
def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍳 Створити рецепт")],
            [KeyboardButton(text="ℹ️ Допомога")]
        ],
        resize_keyboard=True
    )
    return kb

@dp.message(lambda message: message.text == "ℹ️ Допомога")
async def help_handler(message: Message):
    await message.answer_photo(
        photo="https://glavcom.ua/img/article/8157/64_main-v1642618338.jpg",
        caption=
        "👨‍🍳 Я кулінарний бот!\n\n"
        "Що я вмію:\n"
        "• Генерувати рецепти з твоїх інгредієнтів\n"
        "• Рахувати КБЖУ\n"
        "• Давати прості інструкції\n\n"
        "Як користуватись:\n"
        "1. Натисни «🍳 Створити рецепт»\n"
        "2. Введи інгредієнти (наприклад: буряк, капуста, картопля, морква, цибуля, м’ясо)\n"
        "3. Отримай рецепт 😎"
    )
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(
        "Привіт! Я кулінарний бот 👨\nОбери дію:",
        reply_markup=main_menu()
    )
@dp.message(lambda message: message.text == "🍳 Створити рецепт")
async def create_recipe(message: Message, state: FSMContext):
    await message.answer("Введи інгредієнти:")
    await state.set_state(States.wait_promt)
    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LOG")

class States(StatesGroup):
    wait_promt = State()

def validator(user_id: int) -> bool:
    return False #user_id not in access

def log(message: Message):
    logger.info(f"[{message.from_user.id}] {message.text}")

@dp.message(Command("verify"))
async def command_start_handler(message: Message):
    user_id = message.from_user.id
    text = f"@{message.from_user.username} [{user_id}] tried to use bot!"
    if user_id in access:
        await message.answer("[✅] Access confirmed!")
    else:
        await message.answer("[❌] Access denied!")

        await bot.send_message(chat_id=access[0], text=text)
    log(message)

@dp.message(Command("gentext"))
async def cmd_start(message: Message, state: FSMContext):
    text = f"@{message.from_user.username} [{message.from_user.id}] tried to use bot!"
    if validator(message.from_user.id):
        await bot.send_message(chat_id=access[0], text=text)
        return
    await message.answer("prompt:")
    await state.set_state(States.wait_promt)

@dp.message(States.wait_promt)
async def process_text(message: Message, state: FSMContext):
    status_msg = await message.answer("Generating response...")
    user_text = message.text
    done = False
    
    while not done:
        try:
            full_response = ""
            chunk_count = 0
            
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": prompt(user_text)}
                ],
                stream=True
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    chunk_count += 1

                    if chunk_count % 5 == 0:
                        try:
                            await status_msg.edit_text(full_response + " ▌")
                        except: 
                            pass

            await status_msg.edit_text(full_response)
            done = True
            
        except Exception as e:
            logging.error(f"Error: {e}")
            await status_msg.edit_text("Groq is busy or limit reached. Waiting...")
            await asyncio.sleep(15)

    log(message)
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())