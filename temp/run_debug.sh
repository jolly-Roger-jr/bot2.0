#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python3 -c "
import asyncio
import logging

# Включаем максимально детальное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/debug.log', encoding='utf-8')
    ]
)

async def run():
    from barkery_bot import main
    await main()

asyncio.run(run())
" 2>&1 | tee logs/full_debug.log
