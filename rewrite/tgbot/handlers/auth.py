from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.database import ORM
from database.models import User
from tgbot.handlers.states import ProductSearch
from tgbot.keyboards.home import generate_category_markup

router = Router()


# @router.callback_query(text='share_contact')  # todo do CWU
# async def prompt_for_contact(callback: CallbackQuery):
#     await callback.answer()
#     await callback.message.answer("Пожалуйста, отправьте ваш контакт через прикрепление -> Контакт.")
#     await callback.message.delete()


@router.message(F.contact)
async def contact_received(message: Message, state: FSMContext, orm: ORM):
    await orm.user_repo.insert_or_update(message)
    await message.answer("Спасибо за предоставленную информацию!")

    markup = await generate_category_markup(orm)
    await message.answer("Выберите категорию:", reply_markup=markup)
    await state.set_state(ProductSearch.choosing_category)