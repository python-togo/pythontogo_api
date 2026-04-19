from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class CouponType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_id: UUID | None = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CategorySummary(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    parent_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    event_id: UUID
    category_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    base_price: Decimal = Decimal("0.00")
    is_active: bool = True


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    image_url: str | None = None
    base_price: Decimal | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductSummary(BaseModel):
    id: UUID
    event_id: UUID
    category_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    base_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Product Variants ──────────────────────────────────────────────────────────

class VariantCreate(BaseModel):
    name: str
    sku: str
    price_override: Decimal | None = None
    stock_quantity: int = 0
    attributes: dict = Field(default_factory=dict)
    is_active: bool = True


class VariantUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    price_override: Decimal | None = None
    stock_quantity: int | None = None
    attributes: dict | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VariantSummary(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    sku: str
    price_override: Decimal | None = None
    stock_quantity: int
    attributes: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemSummary(BaseModel):
    id: UUID
    order_id: UUID
    product_variant_id: UUID
    quantity: int
    unit_price: Decimal
    created_at: datetime


class OrderSummary(BaseModel):
    id: UUID
    event_id: UUID
    user_id: UUID
    coupon_id: UUID | None = None
    status: OrderStatus
    total_amount: Decimal
    discount_amount: Decimal
    shipping_address: dict
    created_at: datetime
    updated_at: datetime


class OrderDetail(OrderSummary):
    items: list[OrderItemSummary] = Field(default_factory=list)


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentSummary(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    status: PaymentStatus
    method: str | None = None
    reference: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Coupons ───────────────────────────────────────────────────────────────────

class CouponCreate(BaseModel):
    event_id: UUID | None = None
    code: str
    type: CouponType
    value: Decimal
    max_uses: int | None = None
    expires_at: datetime | None = None
    is_active: bool = True


class CouponUpdate(BaseModel):
    event_id: UUID | None = None
    code: str | None = None
    type: CouponType | None = None
    value: Decimal | None = None
    max_uses: int | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CouponSummary(BaseModel):
    id: UUID
    event_id: UUID | None = None
    code: str
    type: CouponType
    value: Decimal
    max_uses: int | None = None
    uses_count: int
    expires_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_users: int
    total_orders: int
    total_revenue: Decimal
    recent_orders: list[OrderSummary] = Field(default_factory=list)


# ── Cart (Redis session) ──────────────────────────────────────────────────────

class CartItem(BaseModel):
    variant_id: UUID
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartLineDetail(BaseModel):
    variant_id: UUID
    quantity: int
    sku: str
    name: str
    unit_price: Decimal
    subtotal: Decimal


class CartSummary(BaseModel):
    items: list[CartLineDetail] = Field(default_factory=list)
    coupon_code: str | None = None
    subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")


class CheckoutPayload(BaseModel):
    event_id: UUID
    shipping_address: dict = Field(default_factory=dict)
    coupon_code: str | None = None


# ── Public product detail (with variants) ─────────────────────────────────────

class ProductDetail(ProductSummary):
    variants: list[VariantSummary] = Field(default_factory=list)
