"""
Дополнительные состояния для админки (поэтапное редактирование)
"""
from aiogram.fsm.state import State, StatesGroup

class AdminEditProductStates(StatesGroup):
    """Состояния для поэтапного редактирования товара"""
    waiting_confirm_name = State()
    waiting_confirm_description = State()
    waiting_confirm_price = State()
    waiting_confirm_stock = State()
    waiting_confirm_image = State()
    waiting_confirm_category = State()
    waiting_new_name = State()
    waiting_new_description = State()
    waiting_new_price = State()
    waiting_new_stock = State()
    waiting_new_image = State()
    waiting_new_category = State()
