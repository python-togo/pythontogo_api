from fastapi import APIRouter

from app.routers.shop.categories import api_router as categories_router
from app.routers.shop.products import api_router as products_router
from app.routers.shop.orders import api_router as orders_router
from app.routers.shop.customers import api_router as customers_router
from app.routers.shop.payments import api_router as payments_router
from app.routers.shop.coupons import api_router as coupons_router
from app.routers.shop.dashboard import api_router as dashboard_router
from app.routers.shop.store import api_router as store_router

# Admin routes — JWT + role admin/staff
shop_router = APIRouter(prefix="/admin/shop")
shop_router.include_router(dashboard_router)
shop_router.include_router(categories_router)
shop_router.include_router(products_router)
shop_router.include_router(orders_router)
shop_router.include_router(customers_router)
shop_router.include_router(payments_router)
shop_router.include_router(coupons_router)

# Client routes — public + JWT pour cart/orders
client_shop_router = APIRouter(prefix="/shop")
client_shop_router.include_router(store_router)
