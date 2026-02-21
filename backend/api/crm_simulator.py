from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from datetime import date, datetime, timezone
import uuid
from decimal import Decimal

from backend.api.crm_models import (
    Contact, ContactCreate, ContactUpdate,
    Deal, DealCreate, DealUpdate,
    Opportunity, OpportunityCreate, OpportunityUpdate,
    Order, OrderCreate, OrderStatusUpdate, OrderDiscountUpdate,
    PaginatedResponse, PaginatedMetadata
)
from backend.api.crm_store import CRMStore, CRMException
from backend.api.crm_business_rules import validate_deal_stage_progression, validate_order_discount

router = APIRouter(prefix="/api/v1/crm", tags=["CRM Simulator"])

# Global store initialized on app startup
_store = CRMStore()

def get_store() -> CRMStore:
    return _store

# Helper to map exceptions
def handle_crm_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CRMException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
    return wrapper

# --- Contacts ---

@router.get("/contacts", response_model=PaginatedResponse[Contact])
def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store: CRMStore = Depends(get_store)
):
    items, meta = store.get_contacts(page, page_size)
    return {"data": items, "pagination": meta}

@router.get("/contacts/{id}", response_model=Contact)
def get_contact(id: str, store: CRMStore = Depends(get_store)):
    try:
        return store.get_contact(id)
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/contacts", response_model=Contact, status_code=201)
def create_contact(contact_in: ContactCreate, store: CRMStore = Depends(get_store)):
    contact = Contact(
        contact_id=f"CNT-{uuid.uuid4().hex[:6]}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **contact_in.model_dump()
    )
    store.add_contact(contact)
    return contact

@router.put("/contacts/{id}", response_model=Contact)
def update_contact(id: str, contact_in: ContactUpdate, store: CRMStore = Depends(get_store)):
    try:
        existing = store.get_contact(id)
        update_data = contact_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now(timezone.utc)
        return existing
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete("/contacts/{id}", status_code=204)
def delete_contact(id: str, store: CRMStore = Depends(get_store)):
    try:
        # Soft-delete by setting is_active = False (Epic 2 Spec allows deletion, 
        # but the model has is_active flag. We'll do hard delete on store to keep logic clean per spec "Soft-delete contact")
        # In this instance we flip the bit instead of physically removing it although store supports remove
        existing = store.get_contact(id)
        existing.is_active = False
        existing.updated_at = datetime.now(timezone.utc)
        return None
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# --- Deals ---

@router.get("/deals", response_model=PaginatedResponse[Deal])
def list_deals(
    stage: Optional[str] = Query(None),
    contact_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store: CRMStore = Depends(get_store)
):
    items, meta = store.get_deals(stage, contact_id, page, page_size)
    return {"data": items, "pagination": meta}

@router.get("/deals/{id}", response_model=Deal)
def get_deal(id: str, store: CRMStore = Depends(get_store)):
    try:
        return store.get_deal(id)
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/deals", response_model=Deal, status_code=201)
def create_deal(deal_in: DealCreate, store: CRMStore = Depends(get_store)):
    try:
        deal = Deal(
            deal_id=f"DEL-{uuid.uuid4().hex[:6]}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **deal_in.model_dump()
        )
        store.add_deal(deal)
        return deal
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.put("/deals/{id}", response_model=Deal)
def update_deal(id: str, deal_in: DealUpdate, store: CRMStore = Depends(get_store)):
    try:
        existing = store.get_deal(id)
        update_data = deal_in.model_dump(exclude_unset=True)
        
        if "stage" in update_data:
            validate_deal_stage_progression(existing.stage, update_data["stage"])
            
        for key, value in update_data.items():
            setattr(existing, key, value)
            
        existing.updated_at = datetime.now(timezone.utc)
        return existing
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# --- Opportunities ---

@router.get("/opportunities", response_model=PaginatedResponse[Opportunity])
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store: CRMStore = Depends(get_store)
):
    items, meta = store.get_opportunities(page, page_size)
    return {"data": items, "pagination": meta}

@router.get("/opportunities/{id}", response_model=Opportunity)
def get_opportunity(id: str, store: CRMStore = Depends(get_store)):
    try:
        return store.get_opportunity(id)
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/opportunities", response_model=Opportunity, status_code=201)
def create_opportunity(opp_in: OpportunityCreate, store: CRMStore = Depends(get_store)):
    try:
        opp = Opportunity(
            opportunity_id=f"OPP-{uuid.uuid4().hex[:6]}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **opp_in.model_dump()
        )
        store.add_opportunity(opp)
        return opp
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.put("/opportunities/{id}", response_model=Opportunity)
def update_opportunity(id: str, opp_in: OpportunityUpdate, store: CRMStore = Depends(get_store)):
    try:
        existing = store.get_opportunity(id)
        update_data = opp_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now(timezone.utc)
        return existing
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# --- Orders ---

@router.get("/orders", response_model=PaginatedResponse[Order])
def list_orders(
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store: CRMStore = Depends(get_store)
):
    items, meta = store.get_orders(status, date_from, date_to, page, page_size)
    return {"data": items, "pagination": meta}

@router.get("/orders/{id}", response_model=Order)
def get_order(id: str, store: CRMStore = Depends(get_store)):
    try:
        return store.get_order(id)
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/orders", response_model=Order, status_code=201)
def create_order(order_in: OrderCreate, store: CRMStore = Depends(get_store)):
    try:
        subtotal = sum(item.total_price for item in order_in.line_items)
        if order_in.subtotal is not None:
             # Just use what was passed for mock purposes
             subtotal = order_in.subtotal
             
        discount_amount = (order_in.discount_pct / Decimal("100.0")) * subtotal
        total_amount = subtotal - discount_amount
        
        # New orders are unapproved drafts
        order = Order(
            order_id=f"ORD-{uuid.uuid4().hex[:6]}",
            approval_status="pending",
            order_status="draft",
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            order_date=datetime.now(timezone.utc),
            **order_in.model_dump(exclude={"subtotal"})
        )
        
        # Enforce rule: if they immediately submitted >15%, block it unless it's managed externally
        # The schema requires explicit approval tracking, so this validates
        validate_order_discount(order.discount_pct, order.approval_status)
        
        store.add_order(order)
        return order
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.put("/orders/{id}/status", response_model=Order)
def update_order_status(id: str, status_update: OrderStatusUpdate, store: CRMStore = Depends(get_store)):
    try:
        existing = store.get_order(id)
        
        # CRM Spec Rule: Invoice / Fulfillment Gate -> Only approved orders can proceed realistically
        if status_update.order_status in ["confirmed", "fulfilled"] and existing.approval_status != "approved":
             raise CRMException(f"Cannot transition order to {status_update.order_status} without approval", 409)
             
        existing.order_status = status_update.order_status
        return existing
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get("/orders/{id}/discount")
def get_order_discount(id: str, store: CRMStore = Depends(get_store)):
    try:
        order = store.get_order(id)
        return {
            "discount_pct": order.discount_pct,
            "discount_amount": order.discount_amount
        }
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/orders/{id}/discount", response_model=Order)
def apply_order_discount(id: str, discount_update: OrderDiscountUpdate, store: CRMStore = Depends(get_store)):
    try:
        existing = store.get_order(id)
        
        validate_order_discount(discount_update.discount_pct, existing.approval_status)
        
        existing.discount_pct = discount_update.discount_pct
        existing.discount_amount = (existing.discount_pct / Decimal("100.0")) * existing.subtotal
        existing.total_amount = existing.subtotal - existing.discount_amount
        return existing
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/orders/{id}/approve", response_model=Order)
def approve_order(id: str, store: CRMStore = Depends(get_store)):
    try:
        existing = store.get_order(id)
        existing.approval_status = "approved"
        existing.approved_by = "sales_manager_mock"
        existing.approved_at = datetime.now(timezone.utc)
        return existing
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
