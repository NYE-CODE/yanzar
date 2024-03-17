from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from config.bot_config import dp, bot, BotConfig
from aiogram import types
from aiogram.dispatcher.filters import Text
from keyboards.back_keyboard import back_keyboard
from keyboards.menu_keyboard import generate_main_keyboard
from keyboards.segway_keyboard import segway_inline_buttons, cancel_keyboard

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from sqlite_db import post_segway, get_free_segways, update_segway, delete_segway

storage = MemoryStorage()
dp.storage = storage


class SegwayCreateStates(StatesGroup):
    segway_name = State()
    segway_price = State()


class SegwayEditStates(StatesGroup):
    segway_name = State()
    segway_price = State()


class SegwayDeleteStates(StatesGroup):
    segway_name = State()


@dp.message_handler(Text(equals="Оборудование 🛴"))
async def choose_segway_action(message: types.Message):
    await message.answer("Вы находитесь на вкладке 'Оборудование 🛴'",
                         reply_markup=segway_inline_buttons)
    await message.answer("Выберите действие или вернитесь назад:",
                         reply_markup=back_keyboard)


@dp.message_handler(Text(equals=["Назад 🔙"]), state="*")
async def back_commands(message: types.Message, state: FSMContext):
    if state:
        await state.reset_state()

    last_message = message.message_id - 2
    await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    exit_message = "Вы вышли из вкладки 'Оборудование 🛴'"
    await message.answer(exit_message, reply_markup=main_keyboard)


@dp.message_handler(Text(equals="Отменить ❌"), state="*")
async def cancel_command(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.reset_state()
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Процесс был Вами прерван!", reply_markup=main_keyboard)


@dp.callback_query_handler(Text(equals=["add_segway"]))
async def create_segway_name(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    await callback.bot.send_message(chat_id, 'Процесс создания оборудования запущен 1/2 '
                                             '\nВведите название для нового оборудования:', reply_markup=cancel_keyboard)
    await SegwayCreateStates.segway_name.set()


@dp.callback_query_handler(Text(equals=["edit_segway"]))
async def choose_segway(callback: types.CallbackQuery):
    buttons = await get_free_segways()
    if not buttons:
        await callback.message.answer("Все оборудования сейчас заняты.")
        return

    keyboard = InlineKeyboardMarkup()

    for segway_id, segway_name, price in buttons:
        button_text = f"{segway_id}. {segway_name} - {price} руб."
        callback_data = f"button_{segway_name}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await callback.message.edit_text('Процесс изменения оборудования зарущен 1/2'
                                     '\nВыберите оборудование из списка:', reply_markup=keyboard)
    await SegwayEditStates.segway_name.set()


# Код для создания сигвея
@dp.message_handler(state=SegwayCreateStates.segway_name)
async def process_segway_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["segway_name"] = message.text

    await message.answer('Введите стоимость за 10 минут проката:')
    await SegwayCreateStates.segway_price.set()  # Переход к следующему состоянию



@dp.message_handler(lambda message: not message.text.isdigit(), state=SegwayCreateStates.segway_price)
async def checking_input_money(message: types.Message):
    return await message.reply("Вы ввели не число!")


@dp.message_handler(state=SegwayCreateStates.segway_price)
async def add_money(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # Debugging: print or log the data to see if 'name' key exists
        print(data)  # or use logging

        if "segway_name" in data:
            segway = data["segway_name"]
        else:
            # Handle the case where 'name' is not in data
            await message.reply("Error: Name not found in the state data.")
            return  # Exit the function to avoid further processing

        data["money"] = message.text
        price = float(data["money"])  # Convert to number

    await post_segway(segway, price)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer(f"Оборудование: {segway} со стоимостью {price} рублей"
                         f"\nбыл успешно создан!", reply_markup=main_keyboard)
    await state.finish()



# Код для редактирования сигвея
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'),
                           state=SegwayEditStates.segway_name)
async def process_segway_callback(callback_query: CallbackQuery, state: FSMContext):
    button_id = callback_query.data.replace('button_', '')

    async with state.proxy() as data:
        data["segway_name"] = button_id

    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    await callback_query.message.answer('Введите новый прайс:', reply_markup=cancel_keyboard)
    await SegwayEditStates.next()


@dp.message_handler(state=SegwayEditStates.segway_price)
async def edit_segway_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        name = data["segway_name"]
        money = float(message.text)  # Преобразуйте в число

    await update_segway(name, money)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer(f"Оборудование {name} обновлено. Новый прайс: {money} руб.",
                         reply_markup=main_keyboard)
    await state.finish()


@dp.callback_query_handler(Text(equals=["delete_segway"]))
async def choose_segway_for_deleting(callback: types.CallbackQuery):
    buttons = await get_free_segways()
    if not buttons:
        await callback.message.answer("Все оборудования сейчас заняты.")
        return

    keyboard = InlineKeyboardMarkup()

    for segway_id, segway_name, price in buttons:
        button_text = f"{segway_id}. {segway_name} - {price} руб."
        callback_data = f"button_{segway_name}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await callback.message.edit_text('Выберите оборудование для удаления:', reply_markup=keyboard)
    await SegwayDeleteStates.segway_name.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'),
                           state=SegwayDeleteStates.segway_name)
async def delete_segway_callback(callback_query: CallbackQuery, state: FSMContext):
    button_id = callback_query.data.replace('button_', '')

    await delete_segway(button_id)

    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оборудование успешно удалено.", reply_markup=main_keyboard)
    await state.finish()

