from aiogram.fsm.state import StatesGroup, State


class ProductSearch(StatesGroup):
    choosing_category = State()