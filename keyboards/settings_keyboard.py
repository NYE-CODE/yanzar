from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardMarkup, KeyboardButton

settings_inline_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Добавить", callback_data="add_employee"),
            InlineKeyboardButton(text="Редактировать", callback_data="edit_employee")

        ],
        [
            InlineKeyboardButton(text="Удалить", callback_data="delete_employee")
         ]
    ]
)

cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отменить ❌"))