from app.db.session import get_session
from app.repositories import catalog as repo
from app.schemas.product import ProductDTO

async def get_categories() -> list[str]:
    async for session in get_session():
        return await repo.get_categories(session)

async def get_products_by_category(category_name: str) -> list[ProductDTO]:
    async for session in get_session():
        products = await repo.get_products_by_category(session, category_name)
        return [ProductDTO.from_orm(p) for p in products]