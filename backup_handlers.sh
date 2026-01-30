#!/bin/bash
# Скрипт для создания и управления бэкапами handlers.py

BACKUP_DIR="backup"
MAX_BACKUPS=3

# Создаем директорию если ее нет
mkdir -p "$BACKUP_DIR"

# Создание нового бэкапа
if [ "$1" = "create" ] || [ -z "$1" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="handlers_${TIMESTAMP}.py"
    
    if [ ! -f "handlers.py" ]; then
        echo "❌ Файл handlers.py не найден"
        exit 1
    fi
    
    # Копируем файл
    cp handlers.py "${BACKUP_DIR}/${BACKUP_NAME}"
    
    # Создаем инфофайл
    cat > "${BACKUP_DIR}/${BACKUP_NAME}.info" << INFO
# Бэкап файла: handlers.py
# Дата создания: $(date)
# Размер: $(wc -l < handlers.py) строк
# Комментарий: $2
INFO
    
    echo "✅ Бэкап создан: $BACKUP_NAME"
    echo "📊 Строк: $(wc -l < handlers.py)"
    
    # Удаляем старые бэкапы
    BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}/handlers_"*.py 2>/dev/null | wc -l)
    if [ $BACKUP_COUNT -gt $MAX_BACKUPS ]; then
        OLDEST=$(ls -1t "${BACKUP_DIR}/handlers_"*.py | tail -1)
        rm "$OLDEST"
        rm "${OLDEST}.info" 2>/dev/null
        echo "🗑️  Удален старый бэкап: $(basename $OLDEST)"
    fi
    
    echo "📁 Оставлено бэкапов: $(ls -1 "${BACKUP_DIR}/handlers_"*.py 2>/dev/null | wc -l)"

# Показать список бэкапов
elif [ "$1" = "list" ]; then
    echo "📂 Список бэкапов handlers.py:"
    echo "========================================"
    
    if ls -1 "${BACKUP_DIR}/handlers_"*.py >/dev/null 2>&1; then
        ls -1t "${BACKUP_DIR}/handlers_"*.py | while read -r backup; do
            BASENAME=$(basename "$backup")
            SIZE=$(wc -l < "$backup")
            MTIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup")
            
            echo "📄 $BASENAME"
            echo "   📅 $MTIME"
            echo "   📊 $SIZE строк"
            
            INFO_FILE="${backup}.info"
            if [ -f "$INFO_FILE" ]; then
                COMMENT=$(grep "^# Комментарий:" "$INFO_FILE" | cut -d: -f2-)
                if [ -n "$COMMENT" ]; then
                    echo "   💬 $COMMENT"
                fi
            fi
            echo
        done
    else
        echo "📭 Бэкапов не найдено"
    fi

# Восстановить бэкап
elif [ "$1" = "restore" ]; then
    if [ -z "$2" ]; then
        echo "❌ Укажите номер бэкапа для восстановления"
        echo "   Используйте: $0 list для просмотра списка"
        exit 1
    fi
    
    BACKUP_FILE=$(ls -1t "${BACKUP_DIR}/handlers_"*.py | sed -n "${2}p")
    
    if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Бэкап №$2 не найден"
        exit 1
    fi
    
    # Создаем бэкап текущего файла перед восстановлением
    if [ -f "handlers.py" ]; then
        CURRENT_BACKUP="handlers_before_restore_$(date +"%Y%m%d_%H%M%S").py"
        cp handlers.py "${BACKUP_DIR}/${CURRENT_BACKUP}"
        echo "✅ Создан бэкап текущего файла: $CURRENT_BACKUP"
    fi
    
    # Восстанавливаем
    cp "$BACKUP_FILE" handlers.py
    echo "✅ Восстановлен бэкап: $(basename $BACKUP_FILE)"
    echo "📊 Строк: $(wc -l < handlers.py)"

# Проверить синтаксис
elif [ "$1" = "check" ]; then
    echo "🔍 Проверка синтаксиса handlers.py..."
    if python3 -m py_compile handlers.py 2>/dev/null; then
        echo "✅ Синтаксис корректен"
        echo "📊 Строк: $(wc -l < handlers.py)"
    else
        echo "❌ Синтаксическая ошибка"
        python3 -m py_compile handlers.py
    fi

# Справка
else
    echo "🔄 Скрипт управления бэкапами handlers.py"
    echo "========================================"
    echo "Команды:"
    echo "  $0 create [комментарий]  - Создать новый бэкап"
    echo "  $0 list                  - Показать список бэкапов"
    echo "  $0 restore <номер>       - Восстановить бэкап"
    echo "  $0 check                 - Проверить синтаксис"
    echo ""
    echo "Примеры:"
    echo "  $0 create \"После исправления штучных товаров\""
    echo "  $0 list"
    echo "  $0 restore 1"
    echo "  $0 check"
fi
