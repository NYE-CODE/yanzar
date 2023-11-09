from aiogram import Bot, Dispatcher
from dotenv import dotenv_values
import logging



config = dotenv_values('./config/.env')
API_TOKEN = config['API_TOKEN']

logging.basicConfig(level=logging.INFO)

bot = Bot(API_TOKEN)
dp = Dispatcher(bot)