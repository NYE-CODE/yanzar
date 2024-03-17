from aiogram import types
from aiogram.dispatcher import FSMContext
from config.bot_config import dp, bot, BotConfig, set_admin_status
from handlers.schedule import scheduler
from sqlite_db import get_employee
from keyboards.menu_keyboard import generate_main_keyboard


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    telegram_id = message.from_user.id
    employee_data = await get_employee(telegram_id)

    # Проверяем, что полученный список не пуст
    if employee_data:
        # Извлекаем первый кортеж из списка
        employee_tuple = employee_data[0]

        # Теперь корректно распаковываем данные сотрудника из кортежа
        employee, current_user_id, is_admin_db = employee_tuple

        set_admin_status(is_admin_db)
        main_keyboard = await generate_main_keyboard(BotConfig.is_admin)

        await bot.send_message(
            message.chat.id,
            text=f'{employee}, добро пожаловать в панель {"администратора" if is_admin_db else "сотрудника"}!',
            reply_markup=main_keyboard
        )
        await scheduler(message.chat.id)
    else:
        await bot.send_message(message.chat.id, text='Доступ отклонен!', reply_markup=types.ReplyKeyboardRemove())

