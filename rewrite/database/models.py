from datetime import datetime
from typing import Annotated

from sqlalchemy import ForeignKey, text, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at_pk = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at_pk = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"),
                                                  onupdate=text("TIMEZONE('utc', now())"))]


class Base(DeclarativeBase):
    __table_args__ = {'extend_existing': True}


class Site(Base):
    __tablename__ = "site"

    id: Mapped[intpk]
    name: Mapped[str]

    urls: Mapped[list["Url"]] = relationship("Url", back_populates="site")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="site")


class Url(Base):
    __tablename__ = "url"

    id: Mapped[intpk]
    url: Mapped[str]
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id", ondelete="CASCADE"))

    site: Mapped["Site"] = relationship("Site", back_populates="urls")


class Product(Base):
    __tablename__ = "product"

    id: Mapped[intpk]
    name: Mapped[str]
    price: Mapped[str]
    link: Mapped[str]
    image_url: Mapped[str]
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id", ondelete="CASCADE"))
    created_at: Mapped[created_at_pk]
    updated_at: Mapped[updated_at_pk]

    category: Mapped["Category"] = relationship("Category", back_populates="products")


class Category(Base):
    __tablename__ = "category"

    id: Mapped[intpk]
    name: Mapped[str]
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id", ondelete="CASCADE"))

    site: Mapped["Site"] = relationship("Site", back_populates="categories")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
    general_categories: Mapped[list["GeneralCategory"]] = relationship(
        "GeneralCategory",
        secondary="general_category_category",
        back_populates="categories"
    )


class GeneralCategory(Base):
    __tablename__ = "general_category"

    id: Mapped[intpk]
    name: Mapped[str]
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary="general_category_category",
        back_populates="general_categories"
    )


class GeneralCategoryCategory(Base):
    __tablename__ = "general_category_category"

    general_category_id: Mapped[int] = mapped_column(ForeignKey("general_category.id", ondelete="CASCADE"),
                                                     primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id", ondelete="CASCADE"), primary_key=True)


class User(Base):
    __tablename__ = "user"

    id: Mapped[intpk]
    tg_id: Mapped[int]
    name: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[created_at_pk]
    updated_at: Mapped[updated_at_pk]
