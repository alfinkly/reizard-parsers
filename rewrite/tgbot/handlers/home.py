from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from database.database import ORM
from database.models import Category, GeneralCategory
from tgbot.keyboards.callbacks import CategoryCallback
from tgbot.keyboards.home import generate_category_markup

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, orm: ORM):
    existing_user = await orm.user_repo.find_user_by_tgid(message.from_user.id)

    if existing_user:
        markup = await generate_category_markup(orm)
        await message.answer("Вы уже поделились своим номером телефона. Выберите категорию:",
                             reply_markup=markup)
        # await ProductSearch.choosing_category.set()
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True,
                                       keyboard=[[
                                           KeyboardButton(text='Поделиться номером телефона', request_contact=True)
                                       ]])
        await message.answer("Для продолжения работы с ботом, поделитесь вашим номером телефона по кнопке ниже. 🔽",
                             reply_markup=keyboard)
