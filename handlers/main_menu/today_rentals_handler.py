from datetime import datetime
from aiogram import types
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from keyboards.menu_keyboard import menu_buttons
from keyboards.back_keyboard import back_keyboard
from config.bot_config import dp
from sqlite_db import get_today_rentals


@dp.message_handler(Text(equals="Прокат за сегодня 🗒️"))
async def view_rentals(message: types.Message, state: FSMContext):
    try:
        rentals = await get_today_rentals()
        if not rentals:
            await message.answer("Сегодня не было проката.")
            return

        rental_info = await format_rental_info(rentals)

        await message.answer(rental_info, parse_mode=ParseMode.MARKDOWN)
        await message.answer("Выберите действие или вернитесь назад:", reply_markup=back_keyboard)


    except Exception as e:
        await message.answer("Произошла ошибка при получении данных. Пожалуйста, попробуйте позже.")
        print(f"Ошибка: {e}")



@dp.message_handler(Text(equals="Назад 🔙"), state="*")
async def back_command(message: types.Message, state: FSMContext):
    if state is not None:
        await state.reset_state()

    last_message = message.message_id - 2
    await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message)
    await message.answer("Вы вышли из списка аренд", reply_markup=menu_buttons)


async def format_rental_info(rentals):
    rental_info = {}

    for rental in rentals:
        rental_info[len(rental_info) + 1] = rental

    return rental_info
