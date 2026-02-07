# state_manager.py
import logging
from typing import Dict, Any, Optional
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)


class NavigationState(StatesGroup):
    """Состояния для навигации по SMI"""
    MAIN_MENU = State()
    CATEGORIES = State()
    PRODUCTS_LIST = State()
    PRODUCT_VIEW = State()
    CART_VIEW = State()
    ORDER_FORM = State()


class StateManager:
    """
    Менеджер состояний для навигации в SMI.
    Хранит историю переходов.
    """

    def __init__(self):
        # Храним историю навигации для каждого пользователя
        self.navigation_history: Dict[int, list] = {}

    async def push_state(self, user_id: int, state_data: dict):
        """Сохранить текущее состояние в историю"""
        if user_id not in self.navigation_history:
            self.navigation_history[user_id] = []

        # Ограничиваем историю 10 состояниями
        if len(self.navigation_history[user_id]) >= 10:
            self.navigation_history[user_id].pop(0)

        self.navigation_history[user_id].append(state_data)
        logger.debug(f"Pushed state for user {user_id}: {state_data.get('screen')}")

    async def pop_state(self, user_id: int) -> Optional[dict]:
        """Вернуться к предыдущему состоянию"""
        if user_id in self.navigation_history and self.navigation_history[user_id]:
            return self.navigation_history[user_id].pop()
        return None

    async def get_previous_state(self, user_id: int) -> Optional[dict]:
        """Получить предыдущее состояние без удаления"""
        if user_id in self.navigation_history and self.navigation_history[user_id]:
            return self.navigation_history[user_id][-1] if self.navigation_history[user_id] else None
        return None

    async def clear_history(self, user_id: int):
        """Очистить историю навигации"""
        if user_id in self.navigation_history:
            self.navigation_history[user_id] = []

    async def save_current_state(
            self,
            user_id: int,
            screen: str,
            data: Optional[dict] = None,
            fsm_context: Optional[FSMContext] = None
    ):
        """Сохранить текущее состояние"""
        state_data = {
            "screen": screen,
            "data": data or {},
            "timestamp": "..."  # Можно добавить временную метку
        }

        await self.push_state(user_id, state_data)

        if fsm_context:
            await fsm_context.update_data(
                last_screen=screen,
                screen_data=data
            )

    async def go_back(
            self,
            user_id: int,
            fsm_context: Optional[FSMContext] = None
    ) -> Optional[dict]:
        """Вернуться на шаг назад"""
        previous = await self.pop_state(user_id)

        if previous and fsm_context:
            await fsm_context.update_data(
                last_screen=previous.get("screen"),
                screen_data=previous.get("data", {})
            )

        return previous


# Создаём глобальный экземпляр
state_manager = StateManager()