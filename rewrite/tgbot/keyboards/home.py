from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.database import ORM
from database.models import GeneralCategory
from tgbot.keyboards.callbacks import CategoryCallback


async def generate_category_markup(orm: ORM):
    g_categories: list[GeneralCategory] = await orm.general_category_repo.select_all()
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for gc in g_categories:
        count = sum(len(c.products) for c in gc.categories)
        button_text = f"{gc.name} ({count} Продуктов)"
        markup.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=CategoryCallback(id=gc.id).pack())
        ])
    return markup