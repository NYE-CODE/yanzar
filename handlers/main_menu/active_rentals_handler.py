from datetime import datetime, timedelta
from aiogram import types
from aiogram.types import ParseMode, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    KeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from keyboards.menu_keyboard import menu_buttons
from keyboards.back_keyboard import back_keyboard
from keyboards.rental_keyboard import generate_rentals_keyboard, type_rentals_keyboard
from config.bot_config import dp
from sqlite_db import get_active_rentals, get_segway_price, post_extension_rental, finish_rental_request
import asyncio


class ViewRental(StatesGroup):
    View = State()
    Extension = State()


@dp.message_handler(Text(equals="Активный прокат 👀️"))
async def view_rentals(message: types.Message, state: FSMContext):
    try:
        rentals = await get_active_rentals()
        if not rentals:
            await message.answer("На данный момент нет активных аренд.")
            return

        async with state.proxy() as state_data:
            state_data['rentals'] = rentals
            state_data['current_index'] = 0
            state_data['total_count'] = len(rentals)

        current_index = state_data['current_index']
        status = rentals[current_index][-1]

        rental_info = await format_rental_info(rentals, current_index)
        markup = await generate_rentals_keyboard(current_index, len(rentals), status)

        await message.answer(rental_info, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        await message.answer("Выберите действие или вернитесь назад:", reply_markup=back_keyboard)
        await ViewRental.next()

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


async def format_rental_info(rentals, current_index):
    rental = rentals[current_index]
    rental_id, user_id, equipment_id, start_time, end_time, status, total_cost, \
    something1, something2, something3, something4, something5, something6, \
    extension_time = rental

    def parse_datetime(dt_str):
        if isinstance(dt_str, str):
            format = '%Y-%m-%d %H:%M:%S.%f' if '.' in dt_str else '%Y-%m-%d %H:%M:%S'
            return datetime.strptime(dt_str, format)
        else:
            return None

    start_datetime = parse_datetime(start_time)
    end_datetime = parse_datetime(end_time)
    extension_datetime = parse_datetime(extension_time) if isinstance(extension_time, str) else None

    start_formatted = start_datetime.strftime('%d.%m.%Y %H:%M') if start_datetime else "Нет данных"
    end_formatted = end_datetime.strftime('%d.%m.%Y %H:%M') if end_datetime else "Нет данных"
    extension_formatted = extension_datetime.strftime('%d.%m.%Y %H:%M') if extension_datetime else "Не продлена"

    rental_info = (
        f"Аренда №{rental_id}\n"
        f"Пользователь: {user_id}\n"
        f"Оборудование: {equipment_id}\n"
        f"Начало аренды: {start_formatted}\n"
        f"Окончание аренды: {end_formatted}\n"
        f"Время продления: {extension_formatted}\n"
        f"Сумма: {total_cost} руб.\n"
        f"Статус: {status}\n\n"
        f"Время начала продления: {something1}\n"
        f"хз: {something2}\n"
        f"хз: {something3}\n"
        f"Старый сигвей: {something4}\n"
        f"Новый сигвей: {something5}\n"
        f"Сумма продления: {something6}\n\n"
    )

    return rental_info


@dp.callback_query_handler(Text(equals=["prev_rental", "next_rental"]), state=ViewRental.View)
async def switch_rental(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_index = data['current_index']
    rentals = data['rentals']
    total_count = data['total_count']

    if not rentals:
        return

    if callback.data == 'prev_rental':
        current_index = (current_index - 1) % len(rentals)
    elif callback.data == 'next_rental':
        current_index = (current_index + 1) % len(rentals)

    status = rentals[current_index][-1]
    markup = await generate_rentals_keyboard(current_index, total_count, status)

    rental_info = await format_rental_info(rentals, current_index)

    async with state.proxy() as state_data:
        state_data['current_index'] = current_index

    if rental_info != callback.message.text:
        await callback.message.edit_text(rental_info, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        await asyncio.sleep(0.1)


@dp.callback_query_handler(Text(equals="finish_rental"), state=ViewRental.View)
async def handle_finish_rental(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rentals = data['rentals']
    current_index = data['current_index']
    rental = rentals[current_index]
    rental_id = rental[0]

    await finish_rental_request(rental_id)

    await callback.message.answer(f"Прокат {rental_id} был успешно завершен!", reply_markup=menu_buttons)
    await state.reset_state()




# @dp.callback_query_handler(Text(equals=["extension_rental"]), state=ViewRental.View)
# async def extension_rental(callback: CallbackQuery, state: FSMContext):
#     await ViewRental.Extension.set()
#     await callback.message.answer("Введите сумму, на которую хотите продлить аренду.")
#
#
# @dp.message_handler(state=ViewRental.Extension)
# async def input_extension_money(message: types.Message, state: FSMContext):
#     try:
#         extension_money = float(message.text)
#         if extension_money > 0:
#             async with state.proxy() as state_data:
#                 rentals = state_data.get('rentals')
#                 current_index = state_data.get('current_index')
#                 if current_index < len(rentals):
#                     rental = rentals[current_index]
#                     rental_id = rental[0]
#                     end_time = rental[4]
#                     extension_time = rental[7]
#                     equipment_price = await get_segway_price(rental[2])
#
#                     def parse_datetime(dt_str):
#                         format = '%Y-%m-%d %H:%M:%S.%f' if '.' in dt_str else '%Y-%m-%d %H:%M:%S'
#                         return datetime.strptime(dt_str, format)
#
#                     if equipment_price > 0:
#                         price_per_10_minutes = equipment_price / 10
#                         minutes_available = (extension_money / price_per_10_minutes) * 10
#                         current_end_time = parse_datetime(extension_time) if extension_time else parse_datetime(end_time)
#                         extended_end_time = current_end_time + timedelta(minutes=minutes_available)
#                         format = '%Y-%m-%d %H:%M:%S.%f' if '.' in extension_time else '%Y-%m-%d %H:%M:%S'
#                         extended_end_time_str = extended_end_time.strftime(format)
#                         await post_extension_rental(rental_id, extended_end_time_str, extension_money)
#                         await message.answer(f"Аренда успешно продлена. Новое время окончания аренды: {extended_end_time_str}")
#                     else:
#                         await message.answer("Ошибка: Невозможно получить стоимость оборудования.")
#                 else:
#                     await message.answer("Ошибка: Невозможно продлить аренду.")
#         else:
#             await message.answer("Ошибка: Введите положительную сумму.")
#     except ValueError:
#         await message.answer("Ошибка: Введите корректную сумму денег.")
#     await state.finish()