from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage

from config.settings import BOT_TOKEN

bot = Bot(BOT_TOKEN, parse_mode="html")
dp = Dispatcher(bot=bot, storage=MemoryStorage())
