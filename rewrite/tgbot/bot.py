import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database.config import EnvSettings
from database.database import ORM
from tgbot.handlers import home
from tgbot.middlewares.orm import ORMMiddleware


async def run_tgbot(orm: ORM):
    config = EnvSettings()
    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.message.middleware(ORMMiddleware(orm))
    dp.callback_query.middleware(ORMMiddleware(orm))
    dp.include_routers(home.router)
    await dp.start_polling(bot=bot)