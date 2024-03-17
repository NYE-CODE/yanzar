import asyncio
from datetime import datetime, timedelta
from aiogram import types
from aiogram.types import ParseMode, CallbackQuery, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from keyboards.back_keyboard import back_keyboard
from keyboards.menu_keyboard import generate_main_keyboard
from keyboards.rental_keyboard import generate_rentals_keyboard
from config.bot_config import dp, bot, BotConfig
from sqlite_db import (
    get_active_rentals, finish_rental_request, get_segway_price, post_extension_rental, cancel_rental, get_free_segways,
    change_rental_request, get_segway_price_id, finish_rental_recalculate_request
)


class ViewRental(StatesGroup):
    View = State()
    Extension = State()
    Cancel_description = State()
    Equipment = State()


# Message handler for cancel command
@dp.message_handler(Text(equals="Отменить ❌"), state="*")
async def cancel_command(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.reset_state()
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Процесс был Вами прерван!", reply_markup=main_keyboard)


@dp.message_handler(Text(equals="Активный прокат 👀️"))
async def view_rentals(message: types.Message, state: FSMContext):
    try:
        rentals = await get_active_rentals()
        if not rentals:
            await message.answer("На данный момент нет активных аренд.")
            return

        async with state.proxy() as state_data:
            state_data.update({
                'rentals': rentals,
                'current_index': 0,
                'total_count': len(rentals)
            })

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
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Вы вышли из списка аренд", reply_markup=main_keyboard)


async def format_rental_info(rentals, current_index):
    rental = rentals[current_index]
    rental_id, rental_name, segway_name, start_time, end_time, \
    status, total_price = rental

    def parse_datetime(dt_str):
        format_str = '%Y-%m-%d %H:%M:%S.%f' if '.' in dt_str else '%Y-%m-%d %H:%M:%S'
        return datetime.strptime(dt_str, format_str) if dt_str else None

    start_datetime = parse_datetime(start_time)
    end_datetime = parse_datetime(end_time)

    start_formatted = start_datetime.strftime('%d.%m.%Y %H:%M') if start_datetime else "-"
    end_formatted = end_datetime.strftime('%d.%m.%Y %H:%M') if end_datetime else "-"

    rental_info = (
        f"Прокат №{rental_id}\n"
        f"Название аренды: {rental_name}\n"
        f"Сигвей: {segway_name}\n"
        f"Начало аренды: {start_formatted}\n"
        f"Окончание аренды: {end_formatted}\n"
        f"Сумма: {total_price} руб.\n"
        f"Статус: {status}\n"
    )

    return rental_info


@dp.callback_query_handler(Text(equals=["prev_rental", "next_rental"]), state=ViewRental.View)
async def switch_rental(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_index, rentals, total_count = data['current_index'], data['rentals'], data['total_count']

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
    rentals, current_index = data['rentals'], data['current_index']
    rental_id = rentals[current_index][0]

    # Generate inline keyboard with two options: "Recalculate" and "Finish"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="С пересчетом", callback_data="finish_with_recalculation"))
    keyboard.add(InlineKeyboardButton(text="Без пересчета", callback_data="finish_without_recalculation"))

    last_message = callback.message.message_id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message)

    await callback.message.answer(
        f"Выберите вариант завершения аренды №{rental_id}:",
        reply_markup=keyboard
    )


@dp.callback_query_handler(Text(equals="finish_with_recalculation"), state=ViewRental.View)
async def handle_finish_with_recalculation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    rentals = data['rentals']
    current_index = data['current_index']
    rental = rentals[current_index]
    rental_id, segway_name, end_time, deposit_amount_str = rental[0], rental[2], rental[3], rental[6]

    # Преобразование deposit_amount из строки в float, если это необходимо
    deposit_amount = float(deposit_amount_str)

    # Получить цену за минуту аренды
    segway_price_info = await get_segway_price(segway_name)
    segway_price_per_10_min = float(segway_price_info[0]) if segway_price_info else 0

    # Рассчитать неиспользованное время
    end_time_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S.%f')
    now_dt = datetime.now()
    unused_time_seconds = max((end_time_dt - now_dt).total_seconds(), 0)
    unused_time_minutes = unused_time_seconds / 60

    # Рассчитать сумму для возврата
    refund_amount = min(unused_time_minutes * segway_price_per_10_min / 10, deposit_amount)

    # Обновить запись в базе данных с учетом перерасчета
    remaining_deposit = deposit_amount - refund_amount
    await finish_rental_recalculate_request(rental_id, remaining_deposit)

    # Отправить сообщение об успешном завершении операции
    await callback.message.answer(
        text=f"Аренда №{rental_id} завершена с перерасчетом. Возврат: {refund_amount:.2f} руб.",
        reply_markup=await generate_main_keyboard(BotConfig.is_admin)
    )
    await state.reset_state()






@dp.callback_query_handler(Text(equals="finish_without_recalculation"), state=ViewRental.View)
async def handle_finish_without_recalculation(callback: CallbackQuery, state: FSMContext):
    await finish_rental(callback, state, recalculate=False)


async def finish_rental(callback: CallbackQuery, state: FSMContext, recalculate: bool):
    data = await state.get_data()
    rentals, current_index = data['rentals'], data['current_index']
    rental_id = rentals[current_index][0]
    current_segway_name = rentals[current_index][2]
    current_end_time = rentals[current_index][4]
    deposit_amount = rentals[current_index][6]

    # Finish the rental request
    if recalculate:
        current_segway_price = await get_segway_price(current_segway_name)
        current_segway_price = current_segway_price[0]
        unused_time_cost = await calculate_unused_time_cost(current_end_time, current_segway_price)

        total_amount = deposit_amount - unused_time_cost
        await finish_rental_recalculate_request(rental_id, total_amount)
    else:
        await finish_rental_request(rental_id)

    last_message = callback.message.message_id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await callback.message.answer(
        f"Аренда №{rental_id} была успешно {'пересчитана' if recalculate else 'завершена'}!",
        reply_markup=main_keyboard
    )
    await state.reset_state()


@dp.callback_query_handler(Text(equals=["extension_rental"]), state=ViewRental.View)
async def extension_rental(callback: CallbackQuery, state: FSMContext):
    await ViewRental.Extension.set()

    last_message = callback.message.message_id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message)

    await callback.message.answer("Введите сумму, на которую хотите продлить аренду.")


# Message handler for checking input money
@dp.message_handler(lambda message: not message.text.isdigit(), state=ViewRental.Extension)
async def checking_input_money(message: types.Message):
    return await message.reply("Вы ввели не число!")


async def calculate_new_end_time(extension_money, equipment_price, end_time):
    price_per_10_minutes = equipment_price / 10
    minutes_available = extension_money / price_per_10_minutes

    # Преобразование строки в формате '%Y-%m-%d %H:%M:%S.%f' в объект datetime
    end_time_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S.%f')

    extended_datetime = end_time_datetime + timedelta(minutes=minutes_available)
    return extended_datetime, minutes_available


@dp.message_handler(state=ViewRental.Extension)
async def extension_rental(message: types.Message, state: FSMContext):
    extension_money = float(message.text)

    async with state.proxy() as state_data:
        rentals, current_index = state_data.get('rentals', []), state_data.get('current_index', 0)
        rental = rentals[current_index]
        rental_id, end_time, equipment_type = rental[0], rental[4], rental[2]

        # Получение стоимости 10 минут на сигвее equipment_type
        equipment_price = await get_segway_price(equipment_type)
        new_end_time, minutes_available = await calculate_new_end_time(extension_money, equipment_price[0], end_time)

        # Получение текущей стоимости всего проката
        total_cost = float(rental[6])

        # Получение новой конечной стоимости проката
        new_total_cost = total_cost + extension_money

        await post_extension_rental(rental_id, new_end_time, new_total_cost)

        main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
        await message.answer(f"Аренда успешно продлена. Новое время окончания аренды: {new_end_time}",
                             reply_markup=main_keyboard)

    await state.finish()


@dp.callback_query_handler(Text(equals=["cancel_rental"]), state=ViewRental.View)
async def describe_cancel(callback: CallbackQuery, state: FSMContext):
    await ViewRental.Cancel_description.set()

    last_message = callback.message.message_id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message)

    await callback.message.answer("Введите причину отмены проката:")


@dp.message_handler(state=ViewRental.Cancel_description)
async def handle_cancel_rental(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rentals, current_index = data['rentals'], data['current_index']
    rental_id = rentals[current_index][0]
    description = message.text  # Access description from the message

    await cancel_rental(rental_id, description)

    last_message = message.message_id
    await bot.delete_message(chat_id=message.chat.id, message_id=last_message)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer(f"Аренда №{rental_id} была отменена!", reply_markup=main_keyboard)
    await state.reset_state()


@dp.callback_query_handler(Text(equals="change_rental"), state=ViewRental.View)
async def handle_change_rental(callback: CallbackQuery, state: FSMContext):
    buttons = await get_free_segways()
    keyboard = InlineKeyboardMarkup()

    last_message = callback.message.message_id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message)

    for segway_id, segway_name, price in buttons:
        button_text = f"{segway_id}. {segway_name} - {price} руб."
        callback_data = f"button_{segway_id}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await callback.message.answer("Выберите новый сегвей:", reply_markup=keyboard)
    await ViewRental.Equipment.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'), state=ViewRental.Equipment)
async def process_segway_callback(callback_query: CallbackQuery, state: FSMContext):
    try:
        # получили айди нового сегвея
        button_id = callback_query.data.replace('button_', '')

        data = await state.get_data()
        current_rental_id = data['rentals'][0][0]
        rental_name = data['rentals'][0][1]
        current_segway_name = data['rentals'][0][2]
        current_end_time = data['rentals'][0][4]


        current_segway_price = await get_segway_price(current_segway_name)
        current_segway_price = current_segway_price[0]

        print(data['rentals'][0])
        print(current_segway_price)

        unused_time_cost = await calculate_unused_time_cost(current_end_time, current_segway_price)
        print(f"Стоимость неиспользованного времени: {unused_time_cost} руб.")

        new_segway_price_tuple = await get_segway_price_id(button_id)
        new_segway_price = new_segway_price_tuple[0]

        new_end_time = await calculate_new_end_time_change(unused_time_cost, new_segway_price)
        print(f"Новое время окончания проката: {new_end_time}")

        await change_rental_request(current_rental_id, rental_name, new_end_time, 1, unused_time_cost, button_id)

        await callback_query.message.delete()

        main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
        await callback_query.message.answer("Прокат был успешно изменен!", reply_markup=main_keyboard)
        await state.reset_state()

    except Exception as e:
        print(f"Error in process_segway_callback: {e}")


async def calculate_unused_time_cost(current_end_time, current_segway_price):
    # Преобразование строки в формате '%Y-%m-%d %H:%M:%S.%f' в объект datetime
    if isinstance(current_end_time, str):
        current_end_time = datetime.strptime(current_end_time, '%Y-%m-%d %H:%M:%S.%f')

    now = datetime.now()

    # Вычисление оставшегося времени только если текущее время меньше времени окончания аренды
    if now < current_end_time:
        remaining_time = current_end_time - now
        unused_time_minutes = remaining_time.total_seconds() / 60
        unused_time_cost = (unused_time_minutes / 10) * current_segway_price
    else:
        unused_time_cost = 0

    return unused_time_cost



async def calculate_new_end_time_change(unused_time_cost, new_segway_price):
    # Вычисление времени, которое можно прокатить на новом сегвее за оставшиеся деньги
    new_time_minutes = (unused_time_cost / new_segway_price) * 10

    # Расчет нового времени окончания проката, ограничиваем его текущим временем + 24 часа
    new_end_time = datetime.now() + timedelta(minutes=new_time_minutes)

    return new_end_time
