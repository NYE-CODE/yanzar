from aiogram import types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher.filters import Text
from config.bot_config import dp, bot
from sqlite_db import get_segways, post_rentals, db_start, get_equipment_price

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from keyboards.menu_keyboard import *
from datetime import datetime, timedelta

storage = MemoryStorage()
dp.storage = storage

class ProfileStates(StatesGroup):
    name = State()
    equipment = State()
    money = State()


cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отменить ❌"))


@dp.message_handler(Text(equals="Добавить ➕"))
async def create_command(message: types.Message):
    await message.answer('Пришлите имя:', reply_markup=cancel_keyboard)
    await ProfileStates.name.set()


@dp.message_handler(Text(equals="Отменить ❌"), state="*")
async def cancel_command(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.reset_state()
    await message.answer("Вы прервали создание заказа!", reply_markup=menu_buttons)


@dp.message_handler(state=ProfileStates.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text

    buttons = await get_segways()
    keyboard = InlineKeyboardMarkup()

    for segway_name, price in buttons:
        button_text = f"{segway_name} - {price} руб."
        callback_data = f"button_{segway_name}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await message.answer('Выберите сигвей из списка:', reply_markup=keyboard)
    await ProfileStates.next()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'), state=ProfileStates.equipment)
async def process_segway_callback(callback_query: CallbackQuery, state: FSMContext):
    button_id = callback_query.data.replace('button_', '')

    async with state.proxy() as data:
        data["equipment"] = button_id

    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    await callback_query.message.answer('Введите сумму:')
    await ProfileStates.next()


@dp.message_handler(lambda message: not message.text.isdigit(), state=ProfileStates.money)
async def checking_input_money(message: types.Message):
    return await message.reply("Вы ввели не число!")


@dp.message_handler(state=ProfileStates.money)
async def add_money(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["money"] = message.text
        name = data["name"]
        equipment = data["equipment"]
        money = float(data["money"])  # Преобразуйте в число
        start_time = datetime.now()

    # Получите стоимость оборудования
    equipment_price = await get_equipment_price(equipment)

    if equipment_price <= 0:
        # Если не удалось получить стоимость оборудования, что-то пошло не так
        await message.answer("Произошла ошибка при получении стоимости оборудования.")
        return

    # Вычислите количество минут
    price_per_10_minutes = equipment_price
    minutes_available = (money / price_per_10_minutes) * 10

    # Вычислите время окончания аренды
    end_time = start_time + timedelta(minutes=minutes_available)

    # Создайте запись аренды
    total_cost = money
    await post_rentals(name, equipment, start_time, end_time, total_cost)

    await message.answer(f"{name}, {equipment}, {money} руб - {int(minutes_available)} минут")
    await message.answer("Прокат был успешно создан!", reply_markup=menu_buttons)
    await state.reset_state()







