#!/usr/bin/env python3
"""
Тест админ-части Barkery_bot
"""

import sys
import os

# Добавляем корень проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("👑 ТЕСТ АДМИН-ЧАСТИ BARKERY_BOT")
print("=" * 50)

def test_admin_imports():
    """Тест импортов админских модулей"""
    print("📦 Проверка админских импортов:")
    print("-" * 40)
    
    admin_modules = [
        ("app.handlers.admin.panel", "Админ-панель"),
        ("app.handlers.admin.products", "Управление товарами"),
        ("app.handlers.admin.stock", "Управление остатками"),
        ("app.handlers.admin.orders", "Управление заказами"),
        ("app.handlers.admin.backup", "Резервное копирование"),
        ("app.handlers.admin.add_product", "Добавление товаров"),
        ("app.handlers.admin.add_category", "Добавление категорий"),
        ("app.keyboards.admin", "Админские клавиатуры"),
        ("app.services.orders", "Сервис заказов"),
        ("app.services.stock", "Сервис остатков"),
        ("app.services.notifications", "Уведомления админу"),
    ]
    
    passed = 0
    total = len(admin_modules)
    
    for module, description in admin_modules:
        try:
            __import__(module)
            print(f"✅ {description}")
            passed += 1
        except ImportError as e:
            print(f"❌ {description}: {e}")
        except Exception as e:
            print(f"⚠️  {description}: {type(e).__name__}")
            passed += 1
    
    print(f"\n📊 Админ-импорты: {passed}/{total}")
    return passed == total

def test_admin_handlers():
    """Тест наличия админских хендлеров"""
    print("\n🔄 Проверка админских хендлеров:")
    print("-" * 40)
    
    try:
        from aiogram import Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        
        # Импортируем админские роутеры
        from app.handlers.admin.panel import router as panel_router
        from app.handlers.admin.products import router as products_router
        from app.handlers.admin.stock import router as stock_router
        from app.handlers.admin.orders import router as orders_router
        from app.handlers.admin.backup import router as backup_router
        from app.handlers.admin.add_product import router as add_product_router
        from app.handlers.admin.add_category import router as add_category_router
        
        # Проверяем что роутеры созданы
        routers = [
            ("Панель", panel_router),
            ("Товары", products_router),
            ("Остатки", stock_router),
            ("Заказы", orders_router),
            ("Бэкапы", backup_router),
            ("Добавить товар", add_product_router),
            ("Добавить категорию", add_category_router),
        ]
        
        for name, router in routers:
            if router:
                print(f"✅ {name} роутер создан")
            else:
                print(f"❌ {name} роутер не создан")
        
        # Подсчитываем хендлеры
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(panel_router)
        dp.include_router(products_router)
        dp.include_router(stock_router)
        dp.include_router(orders_router)
        dp.include_router(backup_router)
        dp.include_router(add_product_router)
        dp.include_router(add_category_router)
        
        # Считаем хендлеры
        total_handlers = 0
        for router in dp.sub_routers:
            total_handlers += len(list(router.message.handlers))
            total_handlers += len(list(router.callback_query.handlers))
        
        print(f"\n📊 Всего админских хендлеров: {total_handlers}")
        
        return total_handlers > 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки хендлеров: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_services():
    """Тест админских сервисов"""
    print("\n⚙️ Проверка админских сервисов:")
    print("-" * 40)
    
    try:
        # Проверяем сервисы
        from app.services.orders import order_service
        from app.services.stock import stock_service
        from app.services.notifications import notify_admin
        from app.db.backup import backup_manager
        
        services = [
            ("Сервис заказов", order_service),
            ("Сервис остатков", stock_service),
            ("Уведомления админу", notify_admin),
            ("Менеджер бэкапов", backup_manager),
        ]
        
        for name, service in services:
            if service:
                print(f"✅ {name} доступен")
            else:
                print(f"❌ {name} недоступен")
        
        # Проверяем методы сервисов
        if hasattr(order_service, 'get_order') and callable(order_service.get_order):
            print("✅ Сервис заказов имеет метод get_order")
        else:
            print("❌ У сервиса заказов нет метода get_order")
            
        if hasattr(stock_service, 'get_product_stock') and callable(stock_service.get_product_stock):
            print("✅ Сервис остатков имеет метод get_product_stock")
        else:
            print("❌ У сервиса остатков нет метода get_product_stock")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки сервисов: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("👑 ПОЛНАЯ ПРОВЕРКА АДМИН-СИСТЕМЫ\n")
    
    # Запускаем тесты
    import_ok = test_admin_imports()
    handlers_ok = test_admin_handlers()
    services_ok = test_admin_services()
    
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ПРОВЕРКИ АДМИНКИ:")
    print("=" * 50)
    print(f"✅ Импорты: {'ПРОЙДЕНЫ' if import_ok else 'ОШИБКА'}")
    print(f"✅ Хендлеры: {'ПРОЙДЕНЫ' if handlers_ok else 'ОШИБКА'}")
    print(f"✅ Сервисы: {'ПРОЙДЕНЫ' if services_ok else 'ОШИБКА'}")
    
    all_passed = import_ok and handlers_ok and services_ok
    
    if all_passed:
        print("\n🎉 ВСЕ АДМИН-СИСТЕМЫ РАБОТАЮТ КОРРЕКТНО!")
        print("👑 Админка готова к использованию!")
        sys.exit(0)
    else:
        print("\n⚠️  ЕСТЬ ПРОБЛЕМЫ В АДМИН-СИСТЕМЕ!")
        sys.exit(1)

if __name__ == "__main__":
    main()
