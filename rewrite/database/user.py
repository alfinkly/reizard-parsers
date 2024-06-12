from aiogram.types import Message
from sqlalchemy import select, update

from database.repo import Repo
from database.models import User


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

    async def insert_or_update(self, message: Message):
        async with self.sessionmaker() as session:
            user = self.user_from_message(message)
            existing_user = await session.execute(
                select(User).filter_by(tg_id=message.from_user.id)
            )
            existing_user = existing_user.scalar_one_or_none()

            if existing_user is None:
                session.add(user)
            else:
                existing_user.fullname = user.fullname
                existing_user.username = user.username
                existing_user.tg_id = user.tg_id
                existing_user.phone_number = user.phone_number

            await session.commit()

    @staticmethod
    def user_from_message(message: Message) -> User:
        user = User()
        user.username = message.from_user.username
        user.fullname = message.contact.first_name or "" + " " + message.contact.last_name or ""
        user.tg_id = message.from_user.id
        user.phone_number = message.contact.phone_number
        return user
