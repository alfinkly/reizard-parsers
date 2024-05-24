import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from rewrite.clever.main import parse_clever
from rewrite.database.database import ORM, UrlRepo

orm = ORM()


async def start_parsers():
    await orm.create_repos()
    session = async_sessionmaker(await orm.get_async_engine())

    clever_task = asyncio.create_task(parse_clever(orm))

    # await asyncio.gather(task1, task2, task3)
    await asyncio.gather(clever_task)

# Запускаем главный асинхронный цикл
asyncio.run(start_parsers())
# orm.recreate_tables()