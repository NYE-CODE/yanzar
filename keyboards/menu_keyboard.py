from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def generate_main_keyboard(is_admin):
    menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)

    if is_admin:
        menu_buttons.row(KeyboardButton('Добавить ➕'), KeyboardButton('Активный прокат 👀️'))
        menu_buttons.row(KeyboardButton('Оборудование 🛴'), KeyboardButton('Выручка 💰'))
        menu_buttons.row(KeyboardButton('Отчеты 🗒️'))
        menu_buttons.row(KeyboardButton('Настройки ⚙'))
    else:
        menu_buttons.row(KeyboardButton('Добавить ➕'), KeyboardButton('Активный прокат 👀️'))
        menu_buttons.row(KeyboardButton('Выручка 💰'))

    return menu_buttons
