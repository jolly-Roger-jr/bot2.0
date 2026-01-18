# app/services/orders.py - НОВЫЙ ФАЙЛ

from datetime import datetime, timedelta
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from app.db.session import get_session
from app.db.models import Order, OrderItem, Product


class OrderService:
    """Сервис для управления заказами"""

    @staticmethod
    async def get_order(order_id: int):
        """Получить заказ по ID со всеми деталями"""
        async for session in get_session():
            result = await session.execute(
                select(Order)
                .options(
                    selectinload(Order.items).joinedload(OrderItem.product)
                )
                .where(Order.id == order_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_user_orders(user_id: str, limit: int = 20):
        """Получить заказы пользователя"""
        async for session in get_session():
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.user_id == user_id)
                .order_by(desc(Order.created_at))
                .limit(limit)
            )
            return result.scalars().all()

    @staticmethod
    async def get_all_orders(
            status: str = None,
            days: int = 30,
            limit: int = 50
    ):
        """Получить все заказы с фильтрацией"""
        async for session in get_session():
            query = select(Order).options(selectinload(Order.items))

            # Фильтр по статусу
            if status:
                query = query.where(Order.status == status)

            # Фильтр по времени
            if days:
                date_from = datetime.utcnow() - timedelta(days=days)
                query = query.where(Order.created_at >= date_from)

            # Сортировка и лимит
            query = query.order_by(desc(Order.created_at)).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update_order_status(order_id: int, new_status: str):
        """Обновить статус заказа"""
        valid_statuses = ['pending', 'confirmed', 'processing', 'completed', 'cancelled']

        if new_status not in valid_statuses:
            return False

        async for session in get_session():
            order = await session.get(Order, order_id)
            if not order:
                return False

            # Записываем старый статус для лога
            old_status = order.status
            order.status = new_status

            # Если отменяем заказ - возвращаем остатки
            if new_status == 'cancelled' and old_status != 'cancelled':
                await OrderService._restore_stock(order_id, session)

            await session.commit()

            # Логируем изменение
            print(f"Order #{order_id} status changed: {old_status} -> {new_status}")
            return True

    @staticmethod
    async def _restore_stock(order_id: int, session):
        """Вернуть остатки товаров при отмене заказа"""
        result = await session.execute(
            select(OrderItem)
            .options(joinedload(OrderItem.product))
            .where(OrderItem.order_id == order_id)
        )

        items = result.scalars().all()

        for item in items:
            if item.product:
                item.product.stock_grams += item.quantity

    @staticmethod
    async def search_orders(
            search_term: str,
            limit: int = 20
    ):
        """Поиск заказов по ID, имени, телефону или адресу"""
        async for session in get_session():
            try:
                # Пробуем поиск по ID
                order_id = int(search_term)
                query = select(Order).where(Order.id == order_id)
            except ValueError:
                # Поиск по текстовым полям
                search_pattern = f"%{search_term}%"
                query = select(Order).where(
                    or_(
                        Order.customer_name.ilike(search_pattern),
                        Order.phone.ilike(search_pattern),
                        Order.address.ilike(search_pattern),
                        Order.user_id == search_term
                    )
                )

            query = query.options(selectinload(Order.items))
            query = query.order_by(desc(Order.created_at)).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_order_stats(days: int = 7):
        """Статистика по заказам"""
        async for session in get_session():
            # Общая статистика
            total_result = await session.execute(
                select(
                    func.count(Order.id).label('total'),
                    func.sum(Order.total_amount).label('revenue'),
                    func.avg(Order.total_amount).label('avg_order')
                )
            )
            total_stats = total_result.first()

            # Статистика по статусам
            status_result = await session.execute(
                select(
                    Order.status,
                    func.count(Order.id).label('count')
                )
                .group_by(Order.status)
            )
            status_stats = {row[0]: row[1] for row in status_result.all()}

            # Статистика за последние N дней
            date_from = datetime.utcnow() - timedelta(days=days)
            recent_result = await session.execute(
                select(
                    func.count(Order.id).label('count'),
                    func.sum(Order.total_amount).label('revenue')
                )
                .where(Order.created_at >= date_from)
            )
            recent_stats = recent_result.first()

            return {
                'total': {
                    'orders': total_stats.total or 0,
                    'revenue': total_stats.revenue or 0,
                    'avg_order': total_stats.avg_order or 0
                },
                'by_status': status_stats,
                'recent': {
                    'days': days,
                    'orders': recent_stats.count or 0,
                    'revenue': recent_stats.revenue or 0
                }
            }

    @staticmethod
    async def get_todays_orders():
        """Получить сегодняшние заказы"""
        async for session in get_session():
            today = datetime.utcnow().date()

            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(func.date(Order.created_at) == today)
                .order_by(desc(Order.created_at))
            )
            return result.scalars().all()


# Глобальный экземпляр
order_service = OrderService()