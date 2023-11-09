from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


#  клавиатура главного меню
menu_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton('Добавить ➕')
        ],
        [
            KeyboardButton('Активный прокат 👀️'),
            KeyboardButton('Прокат за сегодня 🗒️')
        ],
        [
            KeyboardButton('Изменить прайс 🧮'),
            KeyboardButton('Выручка 💰')
        ],
        [
            KeyboardButton('Настройки ⚙')
        ]
    ],
    resize_keyboard=True
)

