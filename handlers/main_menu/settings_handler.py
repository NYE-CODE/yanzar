from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text
from aiogram import types
from config.bot_config import dp, bot, BotConfig
from keyboards.back_keyboard import back_keyboard
from keyboards.settings_keyboard import settings_inline_buttons, cancel_keyboard
from aiogram.dispatcher import FSMContext
from keyboards.menu_keyboard import generate_main_keyboard
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from sqlite_db import post_employee, update_employee, get_all_employees, delete_employee

storage = MemoryStorage()
dp.storage = storage


class SettingsStates(StatesGroup):
    employee_name = State()
    employee_status = State()
    employee_telegram = State()


class SettingsEditStates(StatesGroup):
    employee_name = State()
    employee_status = State()


class SettingsDeleteStates(StatesGroup):
    employee_name = State()

@dp.message_handler(Text(equals="Настройки ⚙"))
async def choose_segway_action(message: types.Message):
    await message.answer("Вы находитесь на вкладке 'Настройки ⚙'",
                         reply_markup=settings_inline_buttons)
    await message.answer("Выберите действие или вернитесь назад:",
                         reply_markup=back_keyboard)


@dp.message_handler(Text(equals=["Назад 🔙"]), state="*")
async def back_commands(message: types.Message, state: FSMContext):
    if state:
        await state.reset_state()

    last_message = message.message_id - 2
    await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    exit_message = "Вы вышли из вкладки 'Настройки ⚙'"
    await message.answer(exit_message, reply_markup=main_keyboard)


@dp.message_handler(Text(equals="Отменить ❌"), state="*")
async def cancel_command(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.reset_state()
    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer("Процесс был Вами прерван!", reply_markup=main_keyboard)


@dp.callback_query_handler(Text(equals=["add_employee"]))
async def create_employee_name(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    await callback.bot.send_message(chat_id, 'Процесс добавления сотрудника запущен 1/3 '
                                             '\nВведите имя нового сотрудника:', reply_markup=cancel_keyboard)
    await SettingsStates.employee_name.set()


@dp.callback_query_handler(Text(equals=["edit_employee"]))
async def choose_employee(callback: types.CallbackQuery):
    buttons = await get_all_employees()
    if not buttons:
        await callback.message.answer("Нет сотрудников.")
        return

    keyboard = InlineKeyboardMarkup()

    for employee_name, telegram_id, employee_status in buttons:
        button_text = f"{employee_name}, ид: {telegram_id}, статус: {employee_status}."
        callback_data = f"button_{employee_name}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await callback.message.edit_text('Процесс редактирования сотрудника запущен 1/2'
                                     '\nВыберите сотрудника из списка:', reply_markup=keyboard)
    await SettingsEditStates.employee_name.set()


@dp.message_handler(state=SettingsStates.employee_name)
async def process_employee_name(message: types.Message):
    async with FSMContext(storage=storage, chat=message.chat.id, user=message.from_user.id).proxy() as data:
        data["employee_name"] = message.text

    await message.answer('Процесс добавления сотрудника запущен 2/3'
                         '\nВведите 0 - сотрудник без прав администратора, 1 - сотрудник с правами администратора:')
    await SettingsStates.employee_status.set()


@dp.message_handler(lambda message: message.text not in ('0', '1'), state=SettingsStates.employee_status)
@dp.message_handler(lambda message: message.text not in ('0', '1'), state=SettingsEditStates.employee_status)
async def checking_input_status(message: types.Message):
    return await message.reply("Введите только 0 или 1!")


@dp.message_handler(state=SettingsStates.employee_status)
async def process_employee_status(message: types.Message):
    async with FSMContext(storage=storage, chat=message.chat.id, user=message.from_user.id).proxy() as data:
        data["status"] = message.text

    await message.answer('Процесс добавления сотрудника запущен 3/3'
                         '\nВведите telegram id сотрудника:')
    await SettingsStates.employee_telegram.set()


@dp.message_handler(lambda message: not message.text.isdigit(), state=SettingsStates.employee_telegram)
async def checking_input_telegram_id(message: types.Message):
    return await message.reply("Вы ввели не число!")


@dp.message_handler(state=SettingsStates.employee_telegram)
async def add_telegram(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["telegram_id"] = message.text
        employee_name = data["employee_name"]
        status = int(data["status"])
        telegram_id = int(data["telegram_id"])

    await post_employee(employee_name, status, telegram_id)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer(f"Сотрудник {employee_name} {telegram_id} со статусом {status}"
                         f"\nбыл успешно добавлен!",
                         reply_markup=main_keyboard)
    await state.finish()


# Код для редактирование сотрудника
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'),
                           state=SettingsEditStates.employee_name)
async def process_employee_change(callback_query: CallbackQuery, state: FSMContext):
    button_id = callback_query.data.replace('button_', '')

    async with state.proxy() as data:
        data["employee_name"] = button_id

    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    await callback_query.message.answer('Введите новый статус:', reply_markup=cancel_keyboard)
    await SettingsEditStates.employee_status.set()


@dp.message_handler(state=SettingsEditStates.employee_status)
async def edit_employee_status(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        name = data["employee_name"]
        status = int(message.text)  # Преобразуйте в число

    await update_employee(name, status)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await message.answer(f"Сотрудник {name} обновлен со статусом: {status}.",
                         reply_markup=main_keyboard)
    await state.finish()



@dp.callback_query_handler(Text(equals=["delete_employee"]))
async def choose_delete_employee(callback: types.CallbackQuery):
    buttons = await get_all_employees()
    if not buttons:
        await callback.message.answer("Нет сотрудников.")
        return

    keyboard = InlineKeyboardMarkup()

    for employee_name, telegram_id, employee_status in buttons:
        button_text = f"{employee_name}, ид: {telegram_id}, статус: {employee_status}."
        callback_data = f"button_{employee_name}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    await callback.message.edit_text('Процесс удаления сотрудника запущен'
                                     '\nВыберите сотрудника из списка:', reply_markup=keyboard)
    await SettingsDeleteStates.employee_name.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('button_'),
                           state=SettingsDeleteStates.employee_name)
async def delete_employee_callback(callback_query: CallbackQuery, state: FSMContext):
    button_id = callback_query.data.replace('button_', '')

    await delete_employee(button_id)

    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Сотрудник успешно удален.", reply_markup=main_keyboard)
    await state.finish()
