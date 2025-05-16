import asyncio
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from database import init_db, add_router_db, remove_router_db, list_routers_db, add_new_user_db, validate_router, check_user_exist_db, list_user_info_db

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Inline клавиатура основного меню
def get_menu():
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить роутер", callback_data="add_router"),
        InlineKeyboardButton(text="📄 Моя Информация", callback_data="print_user_information")],
        [InlineKeyboardButton(text="📶 Мои роутеры", callback_data="list_routers"),
        InlineKeyboardButton(text="📊 Статус", callback_data="status_button")],
    ])
    return menu

# Inline клавиатура для согласия
def get_consent_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Даю згоду", callback_data="give_consent")]
    ])

# Клавиатура для запроса телефона
def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Поделиться телефоном", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# FSM состояния
class Form(StatesGroup):
    adding_phone = State()
    adding_name = State()
    adding_consent = State()
    adding_mac = State()
    adding_router_name = State()
    removing = State()

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Проверка MAC-адреса
def is_valid_mac(mac: str) -> bool:
    pattern = r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))

# /start
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if check_user_exist_db(message.from_user.id):
        await message.answer("Привет! Выбери действие:", reply_markup=get_menu())
    else:
        await state.set_state(Form.adding_phone)
        await message.answer("📲 Нажмите кнопку: Поделиться телефоном", reply_markup=get_phone_keyboard())

# Регистрация: телефон
@dp.message(Form.adding_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(Form.adding_name)
    await message.answer("Введи имя:", reply_markup=types.ReplyKeyboardRemove())

# Регистрация: имя
@dp.message(Form.adding_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.adding_consent)
    await message.answer("ЗГОДА суб'єкта персональних даних на збір та обробку його персональних даних",
                        reply_markup=get_consent_keyboard())

# Регистрация: финишь
@dp.callback_query(F.data == "give_consent", Form.adding_consent)
async def process_consent(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    success, msg = add_new_user_db(callback.from_user.id, data["phone"], data["name"])
    if success:
        await callback.message.answer("Регистрация завершена! Выбери действие:", reply_markup=get_menu())
        await state.clear()
    else:
        await callback.message.answer(f"Ошибка регистрации: {msg}")
    await callback.answer()

# Вызвать главное меню
@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.answer("Вы в главном меню:", reply_markup=get_menu())
    await callback.answer()

# Вывод статуса
@dp.callback_query(F.data == "status_button")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.answer("📡 Статус: Соединение защищено! 🟢🛡 \nТраффик зашифрован! 🟢🔒", reply_markup=get_menu())
    #await callback.message.answer("Главное меню:", reply_markup=get_menu())
    await callback.answer()

# Добавление роутера: старт
@dp.callback_query(F.data == "add_router")
async def add_router_mac(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.adding_mac)
    await callback.message.answer("Введи MAC адрес роутера (формат XX:XX:XX:XX:XX:XX):")
    await callback.answer()

# Добавление роутера: MAC
@dp.message(Form.adding_mac)
async def add_router_validate_mac(message: Message, state: FSMContext):
    mac = message.text.strip()
    if not is_valid_mac(mac):
        await message.answer("Неверный формат MAC-адреса! Используйте формат XX:XX:XX:XX:XX:XX")
        return
    valid, msg = validate_router(mac)
    if not valid:
        await message.answer(msg)
        return
    await state.update_data(mac=mac)
    await state.set_state(Form.adding_router_name)
    await message.answer("Введи название роутера:")

# Добавление роутера: Финал и имя роутера
@dp.message(Form.adding_router_name)
async def add_router_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    success, msg = add_router_db(
        message.from_user.id,
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
        # Создаём список списков кнопок (каждая кнопка — в своей строке)
        keyboard_buttons = [
            [InlineKeyboardButton(text=f"{router['name']} ({router['mac']})", callback_data=f"router_{router['mac']}")]
            for router in routers
        ]

        # Добавляем кнопку "Главное меню"
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.answer("Ваши роутеры:", reply_markup=keyboard)
    else:
        await callback.message.answer("Список роутеров пуст!", reply_markup=get_menu())
    await callback.answer()

@dp.callback_query(F.data == "print_user_information")
async def print_user_information(callback: types.CallbackQuery):
    success, data = list_user_info_db(callback.from_user.id)

    if not success:
        await callback.message.answer(f"Ошибка: {data}", reply_markup=get_menu())
        await callback.answer()
        return

    # Формируем текст
    info_text = f"📱 {data['phone_number']}\n👤 {data['name']}\n"

    if data["routers"]:
        for router_name, mac in [(r[1], r[0]) for r in data["routers"]]:
            info_text += f"📶 {router_name} 🖧 {mac}\n"
    else:
        info_text += "⚠️ Роутеры не найдены"

    await callback.message.answer(info_text.strip(), reply_markup=get_menu())
    await callback.answer()

# Меню управления роутером
@dp.callback_query(F.data.startswith("router_"))
async def handle_router_selection(callback: types.CallbackQuery):
    mac = callback.data.replace("router_", "")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить роутер", callback_data=f"delete_{mac}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="list_routers")]
        ]
    )

    await callback.message.answer(
        f"Вы выбрали роутер:\nMAC: {mac}\nВыберите действие:",
        reply_markup=keyboard
    )
    await callback.answer()

# Удаление роутера
@dp.callback_query(F.data.startswith("delete_"))
async def delete_router(callback: types.CallbackQuery):
    mac = callback.data.replace("delete_", "")

    # Вызываем метод удаления и получаем статус и сообщение
    success, message = remove_router_db(callback.from_user.id, mac)
    await callback.message.answer(
        message,
        reply_markup=get_menu()
    )
    await callback.answer()

# Точка входа
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())