# app/utils/timezone.py

import pytz
from datetime import datetime
from app.config import settings

# Часовой пояс Сербии (Белград)
SERBIA_TZ = pytz.timezone(settings.timezone)  # Europe/Belgrade

def get_serbia_time() -> datetime:
    """Получить текущее время в часовом поясе Сербии"""
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    return utc_now.astimezone(SERBIA_TZ)

def format_serbia_time(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматировать время в сербском часовом поясе"""
    if dt is None:
        dt = get_serbia_time()
    return dt.strftime(fmt)

def is_scheduled_time(hour: int = 4, minute: int = 0) -> bool:
    """Проверить, наступило ли запланированное время (по сербскому времени)"""
    serbia_time = get_serbia_time()
    return serbia_time.hour == hour and serbia_time.minute == minute