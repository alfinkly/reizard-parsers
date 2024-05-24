from datetime import datetime
from typing import Annotated

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

intpk = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    pass


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    name: Mapped[str]


class Url(Base):
    __tablename__ = "urls"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    url: Mapped[str]
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))


class Product(Base):
    __tablename__ = "product"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    name: Mapped[str]
    price: Mapped[int]
    link: Mapped[str]
    image_url: Mapped[str]
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.utcnow())


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {'extend_existing': True}

    id: Mapped[intpk]
    name: Mapped[str]
