# app/services/cart.py - ОБНОВЛЕННЫЙ С ПРОВЕРКАМИ

from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from app.db.session import get_session
from app.db.models import CartItem, Product


async def add_to_cart(user_id: int, product_id: int, quantity: int):
    """Добавить товар в корзину с проверкой доступности и остатков"""
    async for session in get_session():
        try:
            # Получаем товар с блокировкой для чтения
            product = await session.get(
                Product,
                product_id,
                with_for_update=True  # Блокируем запись на время проверки
            )

            # Проверяем существование товара
            if not product:
                return {'success': False, 'error': 'Товар не найден'}

            # Проверяем доступность
            if not product.available:
                return {'success': False, 'error': 'Товар временно недоступен'}

            # Проверяем остатки
            if product.stock_grams < quantity:
                available_qty = product.stock_grams
                if available_qty <= 0:
                    return {'success': False, 'error': 'Товар закончился'}
                else:
                    return {
                        'success': False,
                        'error': f'Доступно только {available_qty}г',
                        'available_qty': available_qty
                    }

            # Проверяем, есть ли уже в корзине
            result = await session.execute(
                select(CartItem).where(
                    CartItem.user_id == str(user_id),
                    CartItem.product_id == product_id
                )
            )
            existing_item = result.scalar_one_or_none()

            if existing_item:
                # Проверяем, не превысит ли общее количество остатки
                total_quantity = existing_item.quantity + quantity
                if total_quantity > product.stock_grams:
                    max_additional = product.stock_grams - existing_item.quantity
                    if max_additional <= 0:
                        return {
                            'success': False,
                            'error': f'В корзине уже максимальное количество'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Можно добавить еще {max_additional}г',
                            'available_qty': max_additional
                        }

                existing_item.quantity += quantity
            else:
                # Создаем новый элемент корзины
                item = CartItem(
                    user_id=str(user_id),
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(item)

            await session.commit()
            return {'success': True}

        except Exception as e:
            await session.rollback()
            print(f"Error adding to cart: {e}")
            return {'success': False, 'error': 'Ошибка сервера'}


async def get_cart_items(user_id: int):
    """Получить содержимое корзины с проверкой актуальности"""
    async for session in get_session():
        result = await session.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == str(user_id))
        )
        items = result.scalars().all()

        # Фильтруем недоступные товары
        valid_items = []
        items_to_remove = []

        for item in items:
            if item.product and item.product.available and item.product.stock_grams > 0:
                # Проверяем, не превышает ли количество в корзине остатки
                if item.quantity > item.product.stock_grams:
                    # Автоматически уменьшаем до доступного количества
                    item.quantity = item.product.stock_grams
                    if item.quantity <= 0:
                        items_to_remove.append(item.id)
                    else:
                        valid_items.append(item)
                else:
                    valid_items.append(item)
            else:
                items_to_remove.append(item.id)

        # Удаляем недоступные товары
        if items_to_remove:
            await session.execute(
                delete(CartItem).where(CartItem.id.in_(items_to_remove))
            )
            await session.commit()

        return valid_items


async def update_cart_item(user_id: int, product_id: int, new_quantity: int):
    """Обновить количество товара в корзине с проверкой"""
    if new_quantity <= 0:
        # Удаляем товар из корзины
        return await remove_from_cart(user_id, product_id)

    async for session in get_session():
        try:
            # Получаем товар с блокировкой
            product = await session.get(
                Product,
                product_id,
                with_for_update=True
            )

            if not product or not product.available:
                return {'success': False, 'error': 'Товар недоступен'}

            if product.stock_grams < new_quantity:
                return {
                    'success': False,
                    'error': f'Доступно только {product.stock_grams}г',
                    'available_qty': product.stock_grams
                }

            # Обновляем количество в корзине
            result = await session.execute(
                select(CartItem).where(
                    CartItem.user_id == str(user_id),
                    CartItem.product_id == product_id
                )
            )
            item = result.scalar_one_or_none()

            if item:
                item.quantity = new_quantity
                await session.commit()
                return {'success': True}
            else:
                return {'success': False, 'error': 'Товар не найден в корзине'}

        except Exception as e:
            await session.rollback()
            return {'success': False, 'error': 'Ошибка обновления'}


async def remove_from_cart(user_id: int, product_id: int):
    """Удалить товар из корзины"""
    async for session in get_session():
        await session.execute(
            delete(CartItem).where(
                CartItem.user_id == str(user_id),
                CartItem.product_id == product_id
            )
        )
        await session.commit()
        return {'success': True}


async def clear_cart(user_id: int):
    """Очистить корзину пользователя"""
    async for session in get_session():
        await session.execute(
            delete(CartItem).where(CartItem.user_id == str(user_id))
        )
        await session.commit()
        return {'success': True}


async def has_items_in_cart(user_id: int) -> bool:
    """Проверяет есть ли товары в корзине пользователя"""
    items = await get_cart_items(user_id)
    return len(items) > 0


async def get_cart_total(user_id: int) -> dict:
    """Рассчитать общую стоимость корзины с проверкой"""
    items = await get_cart_items(user_id)

    if not items:
        return {
            'success': False,
            'error': 'Корзина пуста',
            'total': 0,
            'items': []
        }

    total = 0.0
    valid_items = []
    unavailable_items = []

    for item in items:
        if item.product:
            # Проверяем актуальность товара
            if item.product.available and item.product.stock_grams >= item.quantity:
                item_price = item.product.price * item.quantity / 100
                total += item_price
                valid_items.append(item)
            else:
                unavailable_items.append({
                    'name': item.product.name,
                    'requested': item.quantity,
                    'available': item.product.stock_grams if item.product.available else 0
                })

    if unavailable_items:
        return {
            'success': False,
            'error': 'Некоторые товары стали недоступны',
            'unavailable_items': unavailable_items,
            'valid_items': valid_items,
            'total': total
        }

    return {
        'success': True,
        'total': total,
        'items': valid_items
    }


async def validate_cart_for_order(user_id: int) -> dict:
    """Проверка корзины перед оформлением заказа"""
    result = await get_cart_total(user_id)

    if not result['success']:
        return result

    # Дополнительные проверки для заказа
    items = result['items']

    if not items:
        return {
            'success': False,
            'error': 'Корзина пуста'
        }

    # Проверяем каждый товар еще раз (на случай параллельных изменений)
    async for session in get_session():
        for item in items:
            product = await session.get(Product, item.product_id)
            if not product or not product.available or product.stock_grams < item.quantity:
                return {
                    'success': False,
                    'error': 'Состав корзины изменился, обновите корзину'
                }

    return {
        'success': True,
        'items': items,
        'total': result['total']
    }