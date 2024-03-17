from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardMarkup, KeyboardButton

segway_inline_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Добавить", callback_data="add_segway"),
            InlineKeyboardButton(text="Редактировать", callback_data="edit_segway")

        ],
        [
            InlineKeyboardButton(text="Удалить", callback_data="delete_segway")
         ]
    ]
)

cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отменить ❌"))