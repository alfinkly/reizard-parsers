from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from database.database import ORM
from database.models import GeneralCategory, Category
from tgbot.keyboards.callbacks import CategoryCallback

router = Router()


@router.callback_query(CategoryCallback.filter())
async def process_category_selection(callback: CallbackQuery, callback_data: CategoryCallback, orm: ORM):
    g_categories: GeneralCategory = await orm.general_category_repo.select_by_id(callback_data.id)
    message_text = f"Продукты в категории '{g_categories.name}':"
    for c in g_categories.categories:
        c: Category
        message_text += f"<b>\n\n{c.name}:'\n'</b>"
        message_text += "\n".join([c.products[i].name for i in range(len(c.products[0:10]))])
        if len(c.products) > 10:
            message_text += f"\nеще {len(c.products)-10} продуктов..."

    await callback.bot.send_message(callback.from_user.id, message_text, parse_mode=ParseMode.HTML)
    await callback.answer()
