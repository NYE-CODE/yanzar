from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


type_rentals_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton("Активный прокат", callback_data="active_rentals"),
            InlineKeyboardButton("Прокат за сегодня", callback_data="todays_rentals")
        ]
    ]
)



async def generate_rentals_keyboard(current_index, total_count, status):
    if total_count > 1 and status == 'Отменена':
        inline_keyboard = [
            [
                InlineKeyboardButton("⏪ предыдущий", callback_data="prev_rental"),
                InlineKeyboardButton(f"{current_index + 1}/{total_count}", callback_data="current_rental"),
                InlineKeyboardButton("следующий ⏩", callback_data="next_rental")
            ]
        ]
    elif total_count <= 1 and status != 'Отменена':
        inline_keyboard = [
            [
                InlineKeyboardButton("Завершить", callback_data="finish_rental"),
                InlineKeyboardButton("Продлить", callback_data="extension_rental")
            ],
            [
                InlineKeyboardButton("Изменить", callback_data="change_rental"),
                InlineKeyboardButton("Отменить", callback_data="cancel_rental")
            ]
        ]
    elif total_count <= 1 and status == 'Отменена':
        inline_keyboard = []
    else:
        inline_keyboard = [
            [
                InlineKeyboardButton("Завершить", callback_data="finish_rental"),
                InlineKeyboardButton("Продлить", callback_data="extension_rental")
            ],
            [
                InlineKeyboardButton("Изменить", callback_data="change_rental"),
                InlineKeyboardButton("Отменить", callback_data="cancel_rental")
            ],
            [
                InlineKeyboardButton("⏪ предыдущий", callback_data="prev_rental"),
                InlineKeyboardButton(f"{current_index + 1}/{total_count}", callback_data="current_rental"),
                InlineKeyboardButton("следующий ⏩", callback_data="next_rental")
            ]
        ]

    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return markup