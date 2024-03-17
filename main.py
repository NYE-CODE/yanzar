from aiogram import executor
from config.bot_config import dp
from handlers.start_handler import *
from handlers.main_menu.add_handler import *
from handlers.main_menu.active_rentals_handler import *
from handlers.main_menu.report_handler import *
from handlers.main_menu.total_amount_handler import *
from handlers.main_menu.segway_handler import *
from handlers.main_menu.settings_handler import *
from handlers.schedule import *
from sqlite_db import db_start


async def on_startup(_):
    await db_start()
    print('Подключение к ДБ')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


