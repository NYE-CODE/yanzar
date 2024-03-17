from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from config.bot_config import dp, bot, BotConfig
from datetime import datetime, timedelta
from keyboards.menu_keyboard import generate_main_keyboard
from sqlite_db import get_free_segways, get_segway_price, add_new_rental, get_segway_id

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage


# Initialize storage
storage = MemoryStorage()
dp.storage = storage


class ProfileStates(StatesGroup):
    id = State()
    name = State()
    equipment = State()
    money = State()


# Define cancel keyboard
cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отменить ❌"))


# Message handler for "Добавить ➕"
@dp.message_handler(Text(equals="Добавить ➕"))
async def create_command(message: types.Message):
    await message.answer("Вы находитесь на вкладке 'Добавить ➕'"
                         "\n"
                         "\nШаг 1/3"
                         "\nПришлите название проката:", reply_markup=cancel_keyboard)
    await ProfileStates.name.set()


# Message handler for cancel command
@dp.message_handler(Text(equals="Отменить ❌"), state="*")
async def cancel_command(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.reset_state()
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Процесс был Вами прерван!", reply_markup=main_keyboard)


# Message handler for entering name
@dp.message_handler(state=ProfileStates.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text

    buttons = await get_free_segways()
    keyboard = InlineKeyboardMarkup()

    for segway_id, segway_name, price in buttons:
        button_text = f"{segway_id}. {segway_name} - {price} руб."
        callback_data = f"button_{segway_name}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await message.answer('Шаг 2/3'
                         '\nВыберите сигвей из списка:', reply_markup=keyboard)
    await ProfileStates.next()


# Callback query handler for segway selection
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'),
                           state=ProfileStates.equipment)
async def process_segway_callback(callback_query: CallbackQuery, state: FSMContext):
    button_name = callback_query.data.replace('button_', '')

    async with state.proxy() as data:
        data["equipment"] = button_name

    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    await callback_query.message.answer('Шаг 3/3'
                                        '\nВведите сумму проката:')
    await ProfileStates.next()


# Message handler for checking input money
@dp.message_handler(lambda message: not message.text.isdigit(), state=ProfileStates.money)
async def checking_input_money(message: types.Message):
    return await message.reply("Вы ввели не число!")


# Message handler for adding money and creating rental
@dp.message_handler(state=ProfileStates.money)
async def add_money(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["money"] = message.text
        name = data["name"]
        equipment = data["equipment"]
        money = float(data["money"])  # Convert to float
        start_time = datetime.now()

        segway_id_tuple = await get_segway_id(equipment)
        segway_id = segway_id_tuple[0][0]

        # Retrieve segway price from the database
        segway_price_tuple = await get_segway_price(equipment)

        # Extract the first element from the tuple (assuming price is the first element)
        segway_price = segway_price_tuple[0] if segway_price_tuple else 0.0

        # Calculate end_time based on segway price and money
        # Assuming 10 minutes of rental per unit of money
        rental_duration = int(money / segway_price) * 10
        end_time = start_time + timedelta(minutes=rental_duration)

        # Add new rental to the database
        await add_new_rental(rental_name=name, start_time=start_time, end_time=end_time, status_id=1,
                             deposit_amount=money, segway_id=segway_id)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Прокат был успешно создан!", reply_markup=main_keyboard)
    await state.reset_state()
