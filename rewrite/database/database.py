from sqlalchemy import create_engine, select, update, insert, Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

from rewrite.database.config import EnvSettings
from rewrite.database.models import Base, Site, Url, Product, Category


class ORM:
    def __init__(self):
        self.settings = EnvSettings()
        self.url_repo = None
        self.category_repo = None
        self.product_repo = None

    async def get_async_engine(self, echo=False):
        async_engine = create_async_engine(
            url=self.settings.asyncpg_url(),
            echo=echo
        )
        return async_engine

    def get_engine(self):
        async_engine = create_engine(
            url=self.settings.psycopg_url(),
            echo=True
        )
        return async_engine

    def recreate_tables(self):
        engine = self.get_engine()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        engine.echo = True

    async def get_async_sessionmaker(self):
        return async_sessionmaker(await self.get_async_engine())

    async def create_repos(self):
        self.url_repo = UrlRepo(await self.get_async_engine())
        self.category_repo = CategoryRepo(await self.get_async_engine())
        self.product_repo = ProductRepo(await self.get_async_engine())


class UrlRepo:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def update_url(self):
        async with self.engine.connect() as session:
            query = (update(Url)
                     .values(url="123")
                     .filter_by(id=1))
            await session.execute(query)

    async def select_urls(self, site_id):
        async with self.engine.connect() as session:
            query = (select(Url).filter_by(site_id=site_id))
            result = await session.execute(query)
            urls = result.all()
            print(f"{urls=}")
            return urls

    async def select_clever_urls(self):
        async with self.engine.connect() as session:
            query = (select(Url).filter_by(site_id=1))
            result = await session.execute(query)
            urls = result.scalars().all()
            return urls

    async def insert_url(self, product: Product):
        async with self.engine.connect() as session:
            session.add(product)
            await session.commit()


class ProductRepo:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def insert_or_update_product(self, product: Product):
        async with self.engine.connect() as s:
            query = (select(Product)
                     .filter_by(link=product.link))
            result = await s.execute(query)
            if result.one_or_none() is None:

                query = (insert(Product)
                         .values(name=product.name,
                                 price=product.price,
                                 link=product.link,
                                 image_url=product.image_url,
                                 category_id=product.category_id))
                await s.execute(query)
                await s.commit()


class CategoryRepo:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_category(self, category: Category):
        async with self.engine.connect() as s:
            query = (select(Category).filter_by(name=category.name))
            result = await s.execute(query)
            scalar = result.scalar_one_or_none()
            # print(f"{scalar=}")
            if scalar is not None:
                return scalar
            else:
                query = (insert(Category)
                         .values(name=category.name, site_id=category.site_id))
                await s.execute(query)
                await s.commit()
                return await self.get_category(category)
