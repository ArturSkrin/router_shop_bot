import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from database import init_db, add_router_db, remove_router_db, list_routers_db

# Загрузка .env переменных
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Inline клавиатура
def get_menu():
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить роутер", callback_data="add_router")],
        [InlineKeyboardButton(text="Удалить роутер", callback_data="remove_router")],
        [InlineKeyboardButton(text="Список роутеров", callback_data="list_routers")],
    ])
    return menu

# FSM состояния
class Form(StatesGroup):
    adding_phone = State()
    adding_name = State()
    adding_mac = State()
    adding_router_name = State()
    removing = State()

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# /start
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Выбери действие:", reply_markup=get_menu())

# Добавление роутера: старт
@dp.callback_query(F.data == "add_router")
async def add_router_phone(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.adding_phone)
    await callback.message.answer("Введи номер телефона:")
    await callback.answer()

# Добавление роутера: телефон
@dp.message(Form.adding_phone)
async def add_router_name(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Form.adding_name)
    await message.answer("Введи имя:")

# Добавление роутера: имя
@dp.message(Form.adding_name)
async def add_router_mac(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.adding_mac)
    await message.answer("Введи MAC адрес роутера:")

# Добавление роутера: MAC и имя роутера
@dp.message(Form.adding_mac)
async def add_router_router_name(message: Message, state: FSMContext):
    await state.update_data(mac=message.text)
    await state.set_state(Form.adding_router_name)
    await message.answer("Введи название роутера:")

# Добавление роутера: финал
@dp.message(Form.adding_router_name)
async def add_router_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    success, msg = add_router_db(
        message.from_user.id,
        data["phone"],
        data["name"],
        data["mac"],
        message.text
    )
    await message.answer(msg, reply_markup=get_menu())
    await state.clear()

# Удаление роутера: старт
@dp.callback_query(F.data == "remove_router")
async def remove_router_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.removing)
    await callback.message.answer("Введи MAC адрес роутера для удаления:")
    await callback.answer()

# Удаление роутера: MAC
@dp.message(Form.removing)
async def remove_router(message: Message, state: FSMContext):
    success, msg = remove_router_db(message.from_user.id, message.text)
    await message.answer(msg, reply_markup=get_menu())
    await state.clear()

# Список роутеров
@dp.callback_query(F.data == "list_routers")
async def list_routers(callback: types.CallbackQuery):
    routers = list_routers_db(callback.from_user.id)
    if routers:
        router_list = "\n".join([f"MAC: {router['mac']}, Название: {router['name']}" for router in routers])
        await callback.message.answer(f"Ваши роутеры:\n{router_list}", reply_markup=get_menu())
    else:
        await callback.message.answer("Список роутеров пуст!", reply_markup=get_menu())
    await callback.answer()

# Точка входа
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())