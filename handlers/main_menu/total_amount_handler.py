from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from keyboards.menu_keyboard import generate_main_keyboard
from keyboards.back_keyboard import back_keyboard
from config.bot_config import dp, BotConfig
from sqlite_db import get_total_amount_by_employee
from datetime import datetime


@dp.message_handler(Text(equals="Выручка 💰"))
async def view_rentals(message: types.Message, state: FSMContext):
    current_date = datetime.now().strftime('%Y-%m-%d')

    try:
        amounts = await get_total_amount_by_employee()

        if not amounts:
            await message.answer(f"Сегодня {current_date} не было проката.")
            return

        response_text = f"💰 {current_date} 💰\n"
        for total_amount in amounts:
            response_text += f"Выручка сотрудников {total_amount} рублей\n"

        await message.answer(response_text)
        await message.answer("По завершению вернитесь назад:", reply_markup=back_keyboard)

    except Exception as e:
        await message.answer("Произошла ошибка при получении данных. Пожалуйста, попробуйте позже.")
        print(f"Ошибка: {e}")




@dp.message_handler(Text(equals="Назад 🔙"), state="*")
async def back_command(message: types.Message, state: FSMContext):
    if state is not None:
        await state.reset_state()

    last_message = message.message_id - 2
    await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message)
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Вы вышли из 'Выручка'.", reply_markup=main_keyboard)



