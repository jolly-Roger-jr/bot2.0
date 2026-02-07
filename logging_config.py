"""
Конфигурация логирования для Barkery Shop
"""
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from functools import wraps
from typing import Callable, Any

def setup_logging():
    """Настройка логирования для всего приложения"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"barkery_{datetime.now().strftime('%Y%m')}.log"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Логирование настроено. Файл: {log_file}")

class OperationLogger:
    """Класс для логирования операций"""
    
    @staticmethod
    def log_operation(operation: str, user_id: int = None, details: dict = None, 
                     status: str = "success", error: str = None):
        logger = logging.getLogger("operations")
        
        log_data = {
            "operation": operation,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id:
            log_data["user_id"] = user_id
            
        if details:
            log_data["details"] = details
            
        if error:
            log_data["error"] = error
            
        if status == "success":
            logger.info(log_data)
        else:
            logger.error(log_data)

    # ДОБАВЬТЕ ЭТОТ МЕТОД:
    @staticmethod
    def log_admin_operation(admin_id: int, action: str, target: str,
                            details: dict = None):
        """Логирование админских операций"""
        logger = logging.getLogger("admin_operations")

        log_entry = {
            "admin_id": admin_id,
            "action": action,
            "target": target,
            "timestamp": datetime.now().isoformat()
        }

        if details:
            log_entry["details"] = details

        logger.info(log_entry)

    @staticmethod
    def log_order(order_id: int, user_id: int, amount: float,
                  items_count: int, status: str):
        """Логирование заказа"""
        logger = logging.getLogger("orders")

        log_entry = {
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "items_count": items_count,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(log_entry)


class PerformanceMonitor:
    """Мониторинг производительности"""

    def __init__(self):
        self.operations = {}
        self.slow_threshold = 1.0  # 1 секунда

    def track_operation(self, operation_name: str):
        """Декоратор для отслеживания времени выполнения"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                return await self._measure_performance(
                    func, operation_name, *args, **kwargs
                )

            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                return self._measure_performance_sync(
                    func, operation_name, *args, **kwargs
                )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def _measure_performance(self, func: Callable, operation_name: str, *args, **kwargs) -> Any:
        """Измерение производительности асинхронной функции"""
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            self._record_operation(operation_name, execution_time, success=True)

            # Логируем медленные операции
            if execution_time > self.slow_threshold:
                logger = logging.getLogger("performance")
                logger.warning(
                    f"Медленная операция: {operation_name} "
                    f"заняла {execution_time:.2f}с"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._record_operation(operation_name, execution_time, success=False)

            logger = logging.getLogger("performance")
            logger.error(
                f"Ошибка в операции {operation_name} "
                f"после {execution_time:.2f}с: {e}"
            )
            raise

    def _measure_performance_sync(self, func: Callable, operation_name: str, *args, **kwargs) -> Any:
        """Измерение производительности синхронной функции"""
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            self._record_operation(operation_name, execution_time, success=True)

            if execution_time > self.slow_threshold:
                logger = logging.getLogger("performance")
                logger.warning(
                    f"Медленная синхронная операция: {operation_name} "
                    f"заняла {execution_time:.2f}с"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._record_operation(operation_name, execution_time, success=False)

            logger = logging.getLogger("performance")
            logger.error(
                f"Ошибка в синхронной операции {operation_name} "
                f"после {execution_time:.2f}с: {e}"
            )
            raise

    def _record_operation(self, name: str, duration: float, success: bool):
        """Запись информации об операции"""
        if name not in self.operations:
            self.operations[name] = {
                "count": 0,
                "total_time": 0.0,
                "success_count": 0,
                "error_count": 0,
                "max_time": 0.0,
                "min_time": float('inf')
            }

        op_stats = self.operations[name]
        op_stats["count"] += 1
        op_stats["total_time"] += duration

        if success:
            op_stats["success_count"] += 1
        else:
            op_stats["error_count"] += 1

        op_stats["max_time"] = max(op_stats["max_time"], duration)
        op_stats["min_time"] = min(op_stats["min_time"], duration)

    def get_stats(self) -> Dict:
        """Получить статистику производительности"""
        stats = {}

        for name, data in self.operations.items():
            avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0

            stats[name] = {
                "count": data["count"],
                "avg_time_seconds": round(avg_time, 3),
                "max_time_seconds": round(data["max_time"], 3),
                "min_time_seconds": round(data["min_time"], 3),
                "success_rate": round(data["success_count"] / data["count"] * 100, 1) if data["count"] > 0 else 0,
                "errors": data["error_count"]
            }

        return stats

    def reset_stats(self):
        """Сбросить статистику"""
        self.operations = {}


# Функция для настройки расширенного логирования
def setup_production_logging(log_level: str = "INFO"):
    """Настройка логирования для продакшена"""
    # Создаем директории для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Директории для разных типов логов
    (log_dir / "errors").mkdir(exist_ok=True)
    (log_dir / "performance").mkdir(exist_ok=True)
    (log_dir / "operations").mkdir(exist_ok=True)

    # Основной логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Очищаем существующие обработчики
    root_logger.handlers.clear()

    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 1. Файловый обработчик для общего лога
    general_log = log_dir / "barkery.log"
    file_handler = RotatingFileHandler(
        general_log,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 2. Файловый обработчик для ошибок
    error_log = log_dir / "errors" / "errors.log"
    error_handler = RotatingFileHandler(
        error_log,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # 3. Файловый обработчик для производительности
    perf_log = log_dir / "performance" / "performance.log"
    perf_handler = RotatingFileHandler(
        perf_log,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.WARNING)
    perf_handler.setFormatter(formatter)

    # 4. Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Добавляем обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(perf_handler)
    root_logger.addHandler(console_handler)

    # Настраиваем логгер производительности
    perf_logger = logging.getLogger("performance")
    perf_logger.setLevel(logging.WARNING)

    logging.info(f"✅ Производственное логирование настроено. Уровень: {log_level}")

    return root_logger


# СОЗДАЕМ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР МОНИТОРА
performance_monitor = PerformanceMonitor()


# ДОБАВЛЯЕМ ДЕКОРАТОР ДЛЯ ИМПОРТА
def monitor_performance(operation_name: str = None):
    """
    Декоратор для мониторинга производительности

    Использование:
        @monitor_performance("get_products")
        async def get_products():
            pass
    """

    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__
        return performance_monitor.track_operation(name)(func)

    return decorator