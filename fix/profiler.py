"""
Инструмент для профилирования производительности бота
"""
import time
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    stage: str
    duration_ms: float
    details: Dict = None


class BotProfiler:
    """Профайлер для анализа производительности"""

    def __init__(self):
        self.results: List[ProfileResult] = []
        self.current_stage = None
        self.start_time = None

    @contextmanager
    def stage(self, name: str):
        """Контекстный менеджер для измерения этапа"""
        start = time.time()
        self.current_stage = name
        try:
            yield
        finally:
            duration = (time.time() - start) * 1000
            self.results.append(ProfileResult(
                stage=name,
                duration_ms=duration
            ))
            logger.debug(f"⏱️  {name}: {duration:.1f}ms")
            self.current_stage = None

    async def async_stage(self, name: str, coro):
        """Измерить асинхронную операцию"""
        start = time.time()
        self.current_stage = name
        try:
            result = await coro
            return result
        finally:
            duration = (time.time() - start) * 1000
            self.results.append(ProfileResult(
                stage=name,
                duration_ms=duration,
                details={'async': True}
            ))
            logger.debug(f"⏱️  {name}: {duration:.1f}ms")
            self.current_stage = None

    def start_profiling(self):
        """Начать профилирование"""
        self.results.clear()
        self.start_time = time.time()
        logger.info("🧪 Начинаю профилирование...")

    def get_report(self) -> Dict:
        """Получить отчет"""
        total = (time.time() - self.start_time) * 1000 if self.start_time else 0

        stages = {}
        for result in self.results:
            if result.stage not in stages:
                stages[result.stage] = {
                    'count': 0,
                    'total_ms': 0,
                    'avg_ms': 0,
                    'max_ms': 0
                }

            stage_data = stages[result.stage]
            stage_data['count'] += 1
            stage_data['total_ms'] += result.duration_ms
            stage_data['max_ms'] = max(stage_data['max_ms'], result.duration_ms)

        # Вычисляем средние
        for stage_data in stages.values():
            if stage_data['count'] > 0:
                stage_data['avg_ms'] = stage_data['total_ms'] / stage_data['count']

        # Сортируем по времени
        sorted_stages = sorted(
            stages.items(),
            key=lambda x: x[1]['total_ms'],
            reverse=True
        )

        return {
            'total_duration_ms': total,
            'stage_count': len(self.results),
            'stages': dict(sorted_stages),
            'bottlenecks': [
                (stage, data)
                for stage, data in sorted_stages
                if data['avg_ms'] > 50  # Более 50 мс - узкое место
            ]
        }

    def print_report(self):
        """Напечатать отчет"""
        report = self.get_report()

        print("\n" + "="*60)
        print("🧪 ОТЧЕТ ПРОФИЛИРОВАНИЯ")
        print("="*60)
        print(f"📊 Общее время: {report['total_duration_ms']:.1f}ms")
        print(f"📈 Этапов выполнено: {report['stage_count']}")

        print("\n📋 ДЕТАЛИ ПО ЭТАПАМ:")
        print("-"*60)
        for stage, data in report['stages'].items():
            print(f"  {stage}:")
            print(f"    • Количество: {data['count']}")
            print(f"    • Среднее время: {data['avg_ms']:.1f}ms")
            print(f"    • Максимальное: {data['max_ms']:.1f}ms")
            print(f"    • Всего: {data['total_ms']:.1f}ms")

        print("\n⚠️  УЗКИЕ МЕСТА (более 50ms):")
        print("-"*60)
        if report['bottlenecks']:
            for stage, data in report['bottlenecks']:
                print(f"  ❌ {stage}: {data['avg_ms']:.1f}ms (в среднем)")
        else:
            print("  ✅ Узких мест не обнаружено!")

        print("="*60)

        # Сохраняем в файл
        with open('profiler_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Отчет сохранен в profiler_report.json")


# Глобальный профайлер
profiler = BotProfiler()


# Декоратор для измерения функций
def profile_function(name: str = None):
    """Декоратор для профилирования функции"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if name:
                stage_name = name
            else:
                stage_name = f"func:{func.__name__}"

            with profiler.stage(stage_name):
                return func(*args, **kwargs)
        return wrapper

    return decorator


# Декоратор для асинхронных функций
def profile_async_function(name: str = None):
    """Декоратор для профилирования асинхронной функции"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if name:
                stage_name = name
            else:
                stage_name = f"async_func:{func.__name__}"

            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start) * 1000
                profiler.results.append(ProfileResult(
                    stage=stage_name,
                    duration_ms=duration,
                    details={'async': True}
                ))
                logger.debug(f"⏱️  {stage_name}: {duration:.1f}ms")

        return wrapper

    return decorator