import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from arbuz.main import parse_arbuz
from clever.main import parse_clever
from database.database import ORM, UrlRepo

orm = ORM()


async def start_parsers():
    await orm.create_repos()
    clever_task = asyncio.create_task(parse_clever(orm))
    arbuz_task = asyncio.create_task(parse_arbuz(orm))
    await asyncio.gather(arbuz_task, clever_task)

# Запускаем главный асинхронный цикл
asyncio.run(start_parsers())
# orm.recreate_tables()