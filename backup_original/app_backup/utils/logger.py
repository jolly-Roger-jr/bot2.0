# app/utils/logger.py
import logging
import json
from datetime import datetime


class OrderLogger:
    def __init__(self):
        self.logger = logging.getLogger('order_logger')

    async def log_order(self, order_id: int, user_id: str, action: str, details: dict):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'order_id': order_id,
            'user_id': user_id,
            'action': action,
            'details': details
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))