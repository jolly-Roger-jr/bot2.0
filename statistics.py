"""
Модуль статистики для Barkery Shop
"""
import logging

logger = logging.getLogger(__name__)

class StatisticsService:
    async def get_dashboard_stats(self):
        try:
            from database import get_session, Order, Product, User
            from sqlalchemy import func, select
            
            async with get_session() as session:
                result = await session.execute(select(func.count(Order.id)))
                total_orders = result.scalar() or 0
                
                result = await session.execute(select(func.count(User.id)))
                total_users = result.scalar() or 0
                
                result = await session.execute(select(func.count(Product.id)))
                total_products = result.scalar() or 0
                
                result = await session.execute(select(func.sum(Order.total_amount)))
                total_revenue = float(result.scalar() or 0)
                
                avg = total_revenue / total_orders if total_orders > 0 else 0
                
                return {
                    "total_orders": total_orders,
                    "total_users": total_users,
                    "total_products": total_products,
                    "total_revenue": total_revenue,
                    "avg_order_value": avg
                }
        except Exception as e:
            logger.error(f"Ошибка статистики: {e}")
            return {
                "total_orders": 0,
                "total_users": 0,
                "total_products": 0,
                "total_revenue": 0,
                "avg_order_value": 0
            }

statistics_service = StatisticsService()
