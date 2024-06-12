from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload

from database.repo import Repo
from database.models import Category, GeneralCategory


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
