import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from arbuz.main import parse_arbuz
from clever.main import parse_clever
from database.database import ORM, UrlRepo
from tgbot.bot import run_tgbot


async def start_parsers():
    orm = ORM()
    await orm.create_repos()
    clever_task = asyncio.create_task(parse_clever(orm))
    arbuz_task = asyncio.create_task(parse_arbuz(orm))
    tgbot_task = asyncio.create_task(run_tgbot(orm))
    await asyncio.gather(tgbot_task)

# Запускаем главный асинхронный цикл
asyncio.run(start_parsers())
# orm.recreate_tables()