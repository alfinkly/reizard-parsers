from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.repo import Repo
from database.models import Product, Category, Site


class ProductRepo(Repo):
    async def insert_or_update_product(self, product: Product):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .filter_by(link=product.link)
            )
            result = await session.execute(query)
            if result.one_or_none() is None:
                session.add(product)
                await session.commit()

    async def select_all(self):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .options(selectinload(Product.category))
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def select_site_products(self, site_id: int):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .join(Category)
                .join(Site)
                .where(Site.id == site_id)
            )
            result = await session.execute(query)
            products = result.scalars().all()
            return products

    async def search_by_name(self, name: str):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .filter(Product.name.ilike(f'%{name}%'))
            )
            result = await session.execute(query)
            products = result.unique().scalars().all()
            await session.close()
            return products