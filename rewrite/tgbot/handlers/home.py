from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, \
    KeyboardButton

from database.database import ORM

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, orm: ORM):
    user_id = message.from_user.id
    existing_user = await orm.user_repo.find_user_by_tgid(message.from_user.id) or True
    categories = await orm.category_repo.select_all_category()
    if existing_user:
        markup = InlineKeyboardMarkup()
        for category in categories:
            button_text = f"{category.name} ({len(category.products)} Продуктов)"
            markup.add(InlineKeyboardButton(text=button_text, callback_data='category:' + category))
        await message.answer("Вы уже поделились своим номером телефона. Выберите категорию:", reply_markup=markup)
        # await ProductSearch.choosing_category.set()
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                       keyboard=[[KeyboardButton(text='Поделиться номером телефона',
                                                                 request_contact=True)]])
        await message.answer("Для продолжения работы с ботом, поделитесь вашим номером телефона.",
                             reply_markup=keyboard)

