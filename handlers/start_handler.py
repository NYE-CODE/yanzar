from aiogram import types
from config.bot_config import dp, bot
from keyboards.menu_keyboard import *


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await bot.send_message(message.chat.id,
                           text='Добро пожаловать в панель администратора - Okay Segway!',
                           reply_markup=menu_buttons)

