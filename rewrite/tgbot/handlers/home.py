from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from database.database import ORM
from database.models import Category, GeneralCategory
from tgbot.keyboards.callbacks import CategoryCallback

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, orm: ORM):
    # Проверка на существование пользователя в базе данных
    existing_user = True  # await orm.user_repo.find_user_by_tgid(message.from_user.id) is not None
    g_categories: list[GeneralCategory] = await orm.general_category_repo.select_all()

    if existing_user:
        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for gc in g_categories:
            count = sum(len(c.products) for c in gc.categories)
            button_text = f"{gc.name} ({count} Продуктов)"
            markup.inline_keyboard.append([
                InlineKeyboardButton(text=button_text, callback_data=CategoryCallback(id=gc.id).pack())
            ])
        await message.answer("Вы уже поделились своим номером телефона. Выберите категорию:", reply_markup=markup)
        # await ProductSearch.choosing_category.set()
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                       keyboard=[[KeyboardButton(text='Поделиться номером телефона',
                                                                 request_contact=True)]])
        await message.answer("Для продолжения работы с ботом, поделитесь вашим номером телефона.",
                             reply_markup=keyboard)
