import asyncio

from sqlalchemy import create_engine, select, update, insert, Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload

from database.config import EnvSettings
from database.models import Base, Site, Url, Product, Category, User, GeneralCategory


class ORM:
    def __init__(self):
        self.settings = EnvSettings()
        self.url_repo: UrlRepo = None
        self.category_repo: CategoryRepo = None
        self.product_repo: ProductRepo = None
        self.user_repo: UserRepo = None
        self.general_category_repo: GeneralCategoryRepo = None

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

    async def get_async_sessionmaker(self) -> async_sessionmaker:
        return async_sessionmaker(await self.get_async_engine(echo=True))

    async def create_repos(self):
        sessionmaker = await self.get_async_sessionmaker()
        self.url_repo = UrlRepo(sessionmaker)
        self.category_repo = CategoryRepo(sessionmaker)
        self.product_repo = ProductRepo(sessionmaker)
        self.user_repo = UserRepo(sessionmaker)
        self.general_category_repo = GeneralCategoryRepo(sessionmaker)


class Repo:
    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker


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


class CategoryRepo(Repo):
    async def get_category_id(self, category: Category):
        async with self.sessionmaker() as session:
            query = (
                select(Category)
                .filter_by(name=category.name)
            )
            result = await session.execute(query)
            scalar = result.scalar_one_or_none()
            if scalar is not None:
                return scalar.id
            else:
                query = (
                    insert(Category)
                    .values(name=category.name, site_id=category.site_id)
                )
                await session.execute(query)
                await session.commit()
                return await self.get_category_id(category)

    async def select_all_category(self):
        async with self.sessionmaker() as session:
            query = (
                select(Category)
                .options(selectinload(Category.products))
            )
            result = await session.execute(query)
            categories = result.scalars().all()
            return categories


class UserRepo(Repo):
    async def find_user_by_tgid(self, tgid):
        async with self.sessionmaker() as session:
            query = (
                select(User)
                .filter_by(tg_id=tgid)
            )
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user


class GeneralCategoryRepo(Repo):
    async def select_all(self):
        async with self.sessionmaker() as session:
            query = (
                select(GeneralCategory)
                .options(selectinload(GeneralCategory.categories).selectinload(Category.products))
            )
            result = await session.execute(query)
            g_categories = result.scalars().all()
            return g_categories

    async def select_by_id(self, id):
        async with self.sessionmaker() as session:
            query = (
                select(GeneralCategory)
                .filter_by(id=id)
                .options(selectinload(GeneralCategory.categories).selectinload(Category.products))
            )
            result = await session.execute(query)
            g_categories = result.scalars().one()
            return g_categories