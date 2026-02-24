"""
Мониторинг здоровья бота
"""
import logging
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            "start_time": self.start_time,
            "total_messages": 0,
            "total_orders": 0,
            "total_errors": 0,
            "last_backup": None,
            "db_size_mb": 0,
            "uptime_hours": 0
        }

    async def check_health(self) -> Dict:
        """Проверка состояния системы"""
        try:
            from database import get_session, Order
            from sqlalchemy import select, func
            import os

            # 1. Проверка БД
            async with get_session() as session:
                # Проверяем соединение
                result = await session.execute(select(func.count(Order.id)))
                order_count = result.scalar() or 0

                # Получаем размер БД
                from config import settings
                db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
                if os.path.exists(db_path):
                    self.stats["db_size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)

            # 2. Проверка бекапов
            from backup import backup_manager
            backup_stats = await backup_manager.get_backup_stats()

            # 3. Рассчитываем аптайм
            uptime = datetime.now() - self.start_time
            self.stats["uptime_hours"] = round(uptime.total_seconds() / 3600, 1)

            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "connected": True,
                    "orders_count": order_count,
                    "size_mb": self.stats["db_size_mb"]
                },
                "backups": backup_stats,
                "uptime_hours": self.stats["uptime_hours"],
                "performance": {
                    "total_messages": self.stats["total_messages"],
                    "total_orders": self.stats["total_orders"],
                    "error_rate": round(self.stats["total_errors"] / max(self.stats["total_messages"], 1) * 100, 2)
                }
            }

            # Проверяем критичные условия
            if self.stats["db_size_mb"] > 100:  # БД больше 100MB
                health_status["status"] = "warning"
                health_status["warnings"] = ["Database size exceeds 100MB"]

            if backup_stats["total_backups"] == 0:
                health_status["status"] = "warning"
                health_status["warnings"] = health_status.get("warnings", []) + ["No backups available"]

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def increment_message(self):
        self.stats["total_messages"] += 1

    def increment_order(self):
        self.stats["total_orders"] += 1

    def increment_error(self):
        self.stats["total_errors"] += 1

    def update_backup_time(self):
        self.stats["last_backup"] = datetime.now()


# Глобальный экземпляр
health_monitor = HealthMonitor()