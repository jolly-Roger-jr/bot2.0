# app/services/cart.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
from sqlalchemy import select, delete
from app.db.session import get_session
from app.db.models import CartItem, Product, User


async def add_to_cart(user_id: int, product_id: int, quantity: int):
    """Добавить товар в корзину пользователя"""
    async for session in get_session():
        try:
            # 1. Проверяем наличие товара
            product = await session.get(Product, product_id)
            if not product:
                return {'success': False, 'error': 'Товар не найден'}

            if not product.available:
                return {'success': False, 'error': 'Товар временно недоступен'}

            if product.stock_grams < quantity:
                return {
                    'success': False,
                    'error': f'Доступно только {product.stock_grams}г',
                    'available_qty': product.stock_grams
                }

            # 2. Получаем или создаем пользователя
            user_result = await session.execute(
                select(User).where(User.telegram_id == str(user_id))
            )
            user = user_result.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=str(user_id),
                    username=None,  # Можно добавить позже
                    full_name=None
                )
                session.add(user)
                await session.flush()  # Получаем ID пользователя

            # 3. Проверяем, есть ли уже этот товар в корзине
            cart_result = await session.execute(
                select(CartItem).where(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id
                )
            )
            cart_item = cart_result.scalar_one_or_none()

            if cart_item:
                # Увеличиваем количество существующего товара
                cart_item.quantity += quantity
            else:
                # Создаем новый элемент корзины
                cart_item = CartItem(
                    user_id=user.id,
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(cart_item)

            await session.commit()
            return {'success': True, 'message': f'Добавлено {quantity}г товара "{product.name}"'}

        except Exception as e:
            await session.rollback()
            return {'success': False, 'error': f'Ошибка при добавлении в корзину: {str(e)}'}


async def get_cart_items(user_id: int):
    """Получить все товары в корзине пользователя"""
    async for session in get_session():
        try:
            # Находим пользователя
            user_result = await session.execute(
                select(User).where(User.telegram_id == str(user_id))
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return []

            # Получаем товары корзины с информацией о продуктах
            result = await session.execute(
                select(CartItem)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.user_id == user.id)
                .options(selectinload(CartItem.product))
            )

            items = result.scalars().all()
            return items

        except Exception as e:
            print(f"Ошибка при получении корзины: {e}")
            return []


async def get_cart_total(user_id: int):
    """Получить общую сумму корзины и список товаров"""
    try:
        items = await get_cart_items(user_id)

        if not items:
            return {'success': False, 'error': 'Корзина пуста'}

        cart_info = []
        total_amount = 0

        for item in items:
            if item.product:
                item_total = item.product.price * item.quantity / 100
                total_amount += item_total

                cart_info.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': item.product.name,
                    'price_per_100g': item.product.price,
                    'quantity': item.quantity,
                    'item_total': item_total,
                    'available': item.product.available,
                    'stock_grams': item.product.stock_grams,
                    'product': item.product  # Сохраняем объект продукта
                })

        return {
            'success': True,
            'items': cart_info,
            'total': total_amount,
            'items_count': len(cart_info)
        }

    except Exception as e:
        return {'success': False, 'error': f'Ошибка расчета корзины: {str(e)}'}


async def clear_cart(user_id: int):
    """Очистить корзину пользователя"""
    async for session in get_session():
        try:
            # Находим пользователя
            user_result = await session.execute(
                select(User).where(User.telegram_id == str(user_id))
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': 'Пользователь не найден'}

            # Удаляем все элементы корзины пользователя
            await session.execute(
                delete(CartItem).where(CartItem.user_id == user.id)
            )

            await session.commit()
            return {'success': True, 'message': 'Корзина очищена'}

        except Exception as e:
            await session.rollback()
            return {'success': False, 'error': f'Ошибка при очистке корзины: {str(e)}'}


async def update_cart_item(user_id: int, product_id: int, new_quantity: int):
    """Обновить количество товара в корзине"""
    if new_quantity <= 0:
        # Если количество 0 или меньше, удаляем товар
        return await remove_from_cart(user_id, product_id)

    async for session in get_session():
        try:
            # Проверяем наличие товара на складе
            product = await session.get(Product, product_id)
            if not product or not product.available:
                return {'success': False, 'error': 'Товар недоступен'}

            if product.stock_grams < new_quantity:
                return {
                    'success': False,
                    'error': f'Доступно только {product.stock_grams}г',
                    'available_qty': product.stock_grams
                }

            # Находим пользователя
            user_result = await session.execute(
                select(User).where(User.telegram_id == str(user_id))
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': 'Пользователь не найден'}

            # Находим товар в корзине
            cart_result = await session.execute(
                select(CartItem).where(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id
                )
            )
            cart_item = cart_result.scalar_one_or_none()

            if not cart_item:
                return {'success': False, 'error': 'Товар не найден в корзине'}

            # Обновляем количество
            cart_item.quantity = new_quantity
            await session.commit()

            return {'success': True, 'message': f'Количество обновлено: {new_quantity}г'}

        except Exception as e:
            await session.rollback()
            return {'success': False, 'error': f'Ошибка при обновлении: {str(e)}'}


async def remove_from_cart(user_id: int, product_id: int):
    """Удалить товар из корзины"""
    async for session in get_session():
        try:
            # Находим пользователя
            user_result = await session.execute(
                select(User).where(User.telegram_id == str(user_id))
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': 'Пользователь не найден'}

            # Удаляем товар из корзины
            await session.execute(
                delete(CartItem).where(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id
                )
            )

            await session.commit()
            return {'success': True, 'message': 'Товар удален из корзины'}

        except Exception as e:
            await session.rollback()
            return {'success': False, 'error': f'Ошибка при удалении: {str(e)}'}


async def validate_cart_for_order(user_id: int):
    """Проверить доступность всех товаров в корзине для оформления заказа"""
    try:
        cart_data = await get_cart_total(user_id)

        if not cart_data['success']:
            return cart_data

        unavailable_items = []

        for item in cart_data['items']:
            if not item['available']:
                unavailable_items.append({
                    'name': item['product_name'],
                    'requested': item['quantity'],
                    'available': 0,
                    'reason': 'Товар недоступен'
                })
            elif item['stock_grams'] < item['quantity']:
                unavailable_items.append({
                    'name': item['product_name'],
                    'requested': item['quantity'],
                    'available': item['stock_grams'],
                    'reason': 'Недостаточно остатков'
                })

        if unavailable_items:
            return {
                'success': False,
                'error': 'Некоторые товары недоступны',
                'unavailable_items': unavailable_items,
                'total': cart_data['total']
            }

        return {
            'success': True,
            'total': cart_data['total'],
            'items_count': cart_data['items_count'],
            'items': cart_data['items']
        }

    except Exception as e:
        return {'success': False, 'error': f'Ошибка проверки корзины: {str(e)}'}


async def get_cart_summary(user_id: int):
    """Краткая информация о корзине (для отображения в меню)"""
    try:
        cart_data = await get_cart_total(user_id)

        if not cart_data['success']:
            return {'items_count': 0, 'total': 0, 'has_items': False}

        return {
            'items_count': cart_data.get('items_count', 0),
            'total': cart_data.get('total', 0),
            'has_items': cart_data.get('items_count', 0) > 0
        }

    except Exception as e:
        print(f"Ошибка при получении сводки корзины: {e}")
        return {'items_count': 0, 'total': 0, 'has_items': False}


# Импорт для selectinload
from sqlalchemy.orm import selectinload