#!/bin/bash
# Скрипт управления Barkery Bot

case "$1" in
    start)
        echo "🚀 Запуск Barkery Bot..."
        nohup python3 barkery_bot.py > bot.log 2>&1 &
        echo $! > bot.pid
        echo "✅ Бот запущен с PID: $(cat bot.pid)"
        echo "📋 Логи: bot.log"
        ;;
    stop)
        if [ -f bot.pid ]; then
            PID=$(cat bot.pid)
            echo "🛑 Остановка бота (PID: $PID)..."
            kill $PID
            rm -f bot.pid
            echo "✅ Бот остановлен"
        else
            echo "❌ Файл bot.pid не найден"
            echo "Попробуйте найти процесс: ps aux | grep barkery_bot"
        fi
        ;;
    restart)
        echo "🔄 Перезапуск бота..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f bot.pid ]; then
            PID=$(cat bot.pid)
            if ps -p $PID > /dev/null; then
                echo "✅ Бот работает (PID: $PID)"
                echo "📊 Логи (последние 5 строк):"
                tail -5 bot.log
            else
                echo "❌ Бот не работает (PID: $PID не существует)"
                rm -f bot.pid
            fi
        else
            echo "❌ Бот не запущен"
        fi
        ;;
    logs)
        if [ -f "bot.log" ]; then
            echo "📋 Показать логи (последние 50 строк):"
            tail -50 bot.log
        else
            echo "❌ Файл логов не найден"
        fi
        ;;
    test)
        echo "🧪 Тестирование проекта..."
        python3 -m py_compile admin.py handlers.py services.py && echo "✅ Синтаксис корректен"
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить бота"
        echo "  stop    - Остановить бота"
        echo "  restart - Перезапустить бота"
        echo "  status  - Проверить статус бота"
        echo "  logs    - Показать логи"
        echo "  test    - Протестировать синтаксис"
        exit 1
        ;;
esac
