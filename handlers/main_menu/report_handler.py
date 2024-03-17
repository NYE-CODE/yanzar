from datetime import datetime
import os
from aiogram import types
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile
from aiogram.types import InlineKeyboardMarkup, CallbackQuery
from keyboards.menu_keyboard import generate_main_keyboard
from keyboards.back_keyboard import back_keyboard
from config.bot_config import dp, BotConfig
from sqlite_db import get_monthly_rentals
import pandas as pd
from io import BytesIO


@dp.message_handler(Text(equals="Отчеты 🗒️"))
async def view_rentals(message: types.Message):
    try:
        rentals = await get_monthly_rentals()
        if not rentals:
            await message.answer("Сегодня не было проката.")
            return

        download_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [dict(text="Скачать", callback_data="download_sheet")]
            ]
        )

        await message.answer("Нажмите, чтобы скачать файл с данными.", parse_mode=ParseMode.MARKDOWN,
                             reply_markup=download_keyboard)
        await message.answer("Выберите действие или вернитесь назад:", reply_markup=back_keyboard)

    except Exception as e:
        await message.answer("Произошла ошибка при получении данных. Пожалуйста, попробуйте позже.")
        print(f"Ошибка: {e}")







@dp.callback_query_handler(Text(equals=["download_sheet"]))
async def download_sheet(callback: CallbackQuery):
    try:
        rentals = await get_monthly_rentals()
        data = await format_rental_info(rentals)

        # Создание DataFrame из данных
        columns = ['Аренда ID', 'Название Аренды', 'Начало Аренды', 'Конец Аренды', 'Статус Аренды',
                   'Сумма Депозита', 'Сигвей', 'Описание Отмены', 'Сумма Возврата']

        df = pd.DataFrame(data, columns=columns)

        # Создание буфера для хранения Excel-файла
        excel_buffer = BytesIO()

        # Создание объекта ExcelWriter
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter', datetime_format='yyyy-mm-dd',
                            date_format='yyyy-mm-dd') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')

            # Получение объекта workbook и worksheet
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # Установка ширины столбцов равной длине названия столбцов
            for col_num, value in enumerate(columns):
                column_len = max(df[value].astype(str).apply(len).max(), len(value))
                worksheet.set_column(col_num, col_num, column_len)

        # Сброс курсора в начало буфера
        excel_buffer.seek(0)

        # Получение текущей даты
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Формирование имени файла
        excel_filename = f'отчет за {current_date}.XLSX'

        # Отправка файла пользователю
        await callback.bot.send_document(chat_id=callback.from_user.id,
                                         document=InputFile(excel_buffer, filename=excel_filename),
                                         caption=excel_filename)

    except Exception as e:
        await callback.answer("Произошла ошибка при формировании файла. Пожалуйста, попробуйте позже.")
        print(f"Ошибка: {e}")


@dp.message_handler(Text(equals="Назад 🔙"), state="*")
async def back_command(message: types.Message, state: FSMContext):
    if state is not None:
        await state.reset_state()

    last_message = message.message_id - 2
    await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message)
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Вы вышли из 'Отчет за сегодня'", reply_markup=main_keyboard)


async def format_rental_info(rentals):
    formatted_rentals = []
    for rental in rentals:
        formatted_rental = {
            'Аренда ID': rental[0],
            'Название Аренды': rental[1],
            'Начало Аренды': rental[2],
            'Конец Аренды': rental[3],
            'Статус Аренды': rental[4],
            'Сумма Депозита': rental[5],
            'Сигвей': rental[6],
            'Описание Отмены': rental[7] or "Нет отмены",
            'Сумма Возврата': rental[8] or 0
        }
        formatted_rentals.append(formatted_rental)

    return formatted_rentals

