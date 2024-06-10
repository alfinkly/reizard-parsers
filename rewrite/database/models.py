from datetime import datetime
from typing import Annotated

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at_pk = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at_pk = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"),
                                               onupdate=text("TIMEZONE('utc', now())"))]


class Base(DeclarativeBase):
    pass


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    name: Mapped[str]

    urls: Mapped[list["Url"]] = relationship("Url", back_populates="site")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="site")


class Url(Base):
    __tablename__ = "urls"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    url: Mapped[str]
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))

    site: Mapped["Site"] = relationship("Site", back_populates="urls")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    name: Mapped[str]
    price: Mapped[str]
    link: Mapped[str]
    image_url: Mapped[str]
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    created_at: Mapped[created_at_pk]
    updated_at: Mapped[updated_at_pk]

    category: Mapped["Category"] = relationship("Category", back_populates="products")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    name: Mapped[str]
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))

    site: Mapped["Site"] = relationship("Site", back_populates="categories")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[intpk]
    tg_id: Mapped[int]
    name: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[created_at_pk]
