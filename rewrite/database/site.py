from sqlalchemy import update, select

from database.repo import Repo
from database.models import Url, Product


class UrlRepo(Repo):
    async def update_url(self):
        async with self.sessionmaker() as session:
            query = (
                update(Url)
                .values(url="123")
                .filter_by(id=1)
            )
            await session.execute(query)
            await session.commit()

    async def select_urls(self, site_id):
        async with self.sessionmaker() as session:
            query = (
                select(Url)
                .filter_by(site_id=site_id)
            )
            result = await session.execute(query)
            urls = result.scalars().all()
            return urls

    async def select_clever_urls(self):
        async with self.sessionmaker() as session:
            query = (
                select(Url).filter_by(site_id=1)
            )
            result = await session.execute(query)
            urls = result.scalars().all()
            return urls

    async def insert_url(self, product: Product):
        async with self.sessionmaker() as session:
            session.add(product)
            await session.commit()
