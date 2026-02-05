"""
Конфигурация логирования для Barkery Shop
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

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