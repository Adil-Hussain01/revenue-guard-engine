from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Generic, TypeVar
from datetime import datetime, timezone
from decimal import Decimal

T = TypeVar("T")

class PaginatedMetadata(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginatedMetadata

# --- Contacts ---

class ContactBase(BaseModel):
    name: str
    email: str
    company: str
    phone: Optional[str] = None
    is_active: bool = True

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class Contact(ContactBase):
    contact_id: str
    created_at: datetime
    updated_at: datetime


# --- Deals ---

class DealBase(BaseModel):
    contact_id: str
    stage: Literal["prospect", "negotiation", "proposal", "closed_won", "closed_lost"]
    value: Decimal
    assigned_to: str

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    stage: Optional[Literal["prospect", "negotiation", "proposal", "closed_won", "closed_lost"]] = None
    value: Optional[Decimal] = None
    assigned_to: Optional[str] = None

class Deal(DealBase):
    deal_id: str
    created_at: datetime
    updated_at: datetime


# --- Opportunities ---

class OpportunityBase(BaseModel):
    deal_id: str
    contact_id: str
    status: Literal["open", "won", "lost"]
    expected_close_date: datetime

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    status: Optional[Literal["open", "won", "lost"]] = None
    expected_close_date: Optional[datetime] = None

class Opportunity(OpportunityBase):
    opportunity_id: str
    created_at: datetime
    updated_at: datetime


# --- Orders ---

class LineItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

class OrderCreate(BaseModel):
    opportunity_id: str
    contact_id: str
    line_items: List[LineItem]
    # Calculation overrides or will be computed
    subtotal: Optional[Decimal] = None
    discount_pct: Decimal = Decimal("0.0")

class OrderStatusUpdate(BaseModel):
    order_status: Literal["draft", "confirmed", "fulfilled", "cancelled"]

class OrderDiscountUpdate(BaseModel):
    discount_pct: Decimal

class Order(BaseModel):
    order_id: str
    opportunity_id: str
    contact_id: str
    line_items: List[LineItem]
    subtotal: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    approval_status: Literal["pending", "approved", "rejected"]
    order_status: Literal["draft", "confirmed", "fulfilled", "cancelled"]
    order_date: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
