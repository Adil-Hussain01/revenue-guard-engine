import json
import os
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

from backend.api.crm_models import (
    Contact, Deal, Opportunity, Order, LineItem
)

# Exception class for propagating CRM errors to HTTP endpoints
class CRMException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CRMStore:
    def __init__(self, data_dir: str = "generated_data"):
        self.data_dir = data_dir
        
        # In-memory storage dictionaries
        self.contacts: Dict[str, Contact] = {}
        self.deals: Dict[str, Deal] = {}
        self.opportunities: Dict[str, Opportunity] = {}
        self.orders: Dict[str, Order] = {}
        
        # Load up data from Epic 1 synthetic generation
        self.load_seed_data()

    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parses a datetime string and ensures it's timezone-aware (UTC)."""
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
        return dt.replace(tzinfo=timezone.utc)
        
    def load_seed_data(self):
        """Loads contacts, deals, opportunities, and orders from generated JSONs."""
        self.contacts.clear()
        self.deals.clear()
        self.opportunities.clear()
        self.orders.clear()

        # Load Contacts
        try:
            with open(os.path.join(self.data_dir, "contacts.json"), "r") as f:
                data = json.load(f)
                for item in data:
                    c = Contact(
                        contact_id=item["contact_id"],
                        name=item["name"],
                        email=item["email"],
                        company=item["company"],
                        phone=item.get("phone"),
                        created_at=self._parse_datetime(item.get("created_at", "2025-01-01 00:00:00.0")),
                        updated_at=self._parse_datetime(item.get("updated_at", item.get("created_at", "2025-01-01 00:00:00.0"))),
                        is_active=item.get("is_active", True)
                    )
                    self.contacts[c.contact_id] = c
        except FileNotFoundError:
            print("Warning: contacts.json not found. Starting empty.")

        # Load Deals
        try:
            with open(os.path.join(self.data_dir, "deals.json"), "r") as f:
                data = json.load(f)
                for item in data:
                    d = Deal(
                        deal_id=item["deal_id"],
                        contact_id=item["contact_id"],
                        stage=item["stage"],
                        value=Decimal(str(item["value"])),
                        assigned_to=item["assigned_to"],
                        created_at=self._parse_datetime(item.get("created_at", "2025-01-01 00:00:00.0")),
                        updated_at=self._parse_datetime(item.get("updated_at", item.get("created_at", "2025-01-01 00:00:00.0")))
                    )
                    self.deals[d.deal_id] = d
        except FileNotFoundError:
            print("Warning: deals.json not found. Starting empty.")

        # Load Opportunities
        try:
            with open(os.path.join(self.data_dir, "opportunities.json"), "r") as f:
                data = json.load(f)
                for item in data:
                    o = Opportunity(
                        opportunity_id=item["opportunity_id"],
                        deal_id=item["deal_id"],
                        contact_id=item.get("contact_id", "CNT-GENERIC"),
                        status=item.get("status", "open"),
                        expected_close_date=self._parse_datetime(item.get("expected_close_date", "2026-01-01 00:00:00.0")),
                        created_at=self._parse_datetime(item.get("created_at", "2025-01-01 00:00:00.0")),
                        updated_at=self._parse_datetime(item.get("updated_at", item.get("created_at", "2025-01-01 00:00:00.0")))
                    )
                    self.opportunities[o.opportunity_id] = o
        except FileNotFoundError:
            print("Warning: opportunities.json not found. Starting empty.")

        # Load Orders
        # Epic 1 synthetic orders logic uses a slightly different format (referencing Epic 1)
        # Note: If the generated format differs slightly (like line items are absent in Epic 1 export),
        # we will generate synthetic line items to satisfy the Epic 2 spec requirement.
        try:
            with open(os.path.join(self.data_dir, "orders.json"), "r") as f:
                data = json.load(f)
                for item in data:
                    total = Decimal(str(item["total_amount"]))
                    discount_amt = Decimal(str(item.get("discount_applied", "0.0")))
                    subtotal = total + discount_amt
                    
                    discount_pct = Decimal("0.0")
                    if subtotal > 0:
                        discount_pct = (discount_amt / subtotal) * Decimal("100.0")

                    # Map Epic 1 status to Epic 2 spec order_status
                    # Assuming generated 'status' is 'completed', map to 'confirmed' or 'fulfilled'
                    mapped_status = "confirmed"
                    if item.get("status") == "completed":
                        mapped_status = "fulfilled"
                        
                    # We create dummy line items if missing from source data
                    line_items = []
                    item_qty = 1
                    line_items.append(LineItem(
                        product_id="PROD-GEN", 
                        product_name="Generic API Product",
                        quantity=item_qty,
                        unit_price=subtotal,
                        total_price=subtotal
                    ))

                    # Epic 1 orders don't have approval status natively; assume approved if fulfilled
                    approval_status = "approved" if mapped_status == "fulfilled" else "pending"

                    o = Order(
                        order_id=item["order_id"],
                        opportunity_id=item["opportunity_id"],
                        contact_id=item["contact_id"],
                        line_items=line_items,
                        subtotal=subtotal,
                        discount_pct=discount_pct,
                        discount_amount=discount_amt,
                        total_amount=total,
                        approval_status=approval_status,
                        order_status=mapped_status,
                        order_date=self._parse_datetime(item.get("order_date", "2025-01-01 00:00:00.0")),
                        approved_by="system" if approval_status == "approved" else None,
                        approved_at=self._parse_datetime(item.get("order_date", "2025-01-01 00:00:00.0")) if approval_status == "approved" else None
                    )
                    self.orders[o.order_id] = o
        except FileNotFoundError:
            print("Warning: orders.json not found. Starting empty.")

    # --- Pagination Helper ---
    def _paginate(self, records: List[Any], page: int, page_size: int) -> Tuple[List[Any], Dict[str, int]]:
        total = len(records)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = records[start:end]
        return items, {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages
        }

    # --- Contacts DB Operations ---
    def get_contacts(self, page: int = 1, page_size: int = 20):
        items = list(self.contacts.values())
        return self._paginate(items, page, page_size)

    def get_contact(self, contact_id: str) -> Contact:
        if contact_id not in self.contacts:
            raise CRMException("Contact not found", 404)
        return self.contacts[contact_id]

    def add_contact(self, contact: Contact):
        self.contacts[contact.contact_id] = contact

    def remove_contact(self, contact_id: str):
        if contact_id not in self.contacts:
            raise CRMException("Contact not found", 404)
        del self.contacts[contact_id]

    # --- Deals DB Operations ---
    def get_deals(self, stage: Optional[str] = None, contact_id: Optional[str] = None, page: int = 1, page_size: int = 20):
        items = list(self.deals.values())
        if stage:
            items = [d for d in items if d.stage == stage]
        if contact_id:
            items = [d for d in items if d.contact_id == contact_id]
        return self._paginate(items, page, page_size)

    def get_deal(self, deal_id: str) -> Deal:
        if deal_id not in self.deals:
            raise CRMException("Deal not found", 404)
        return self.deals[deal_id]

    def add_deal(self, deal: Deal):
        if deal.contact_id not in self.contacts:
            raise CRMException("Referenced contact_id does not exist", 409)
        self.deals[deal.deal_id] = deal

    # --- Opportunities DB Operations ---
    def get_opportunities(self, page: int = 1, page_size: int = 20):
        items = list(self.opportunities.values())
        return self._paginate(items, page, page_size)

    def get_opportunity(self, opportunity_id: str) -> Opportunity:
        if opportunity_id not in self.opportunities:
            raise CRMException("Opportunity not found", 404)
        return self.opportunities[opportunity_id]

    def add_opportunity(self, opp: Opportunity):
        if opp.contact_id not in self.contacts:
            raise CRMException("Referenced contact_id does not exist", 409)
        if opp.deal_id not in self.deals:
            raise CRMException("Referenced deal_id does not exist", 409)
        self.opportunities[opp.opportunity_id] = opp

    # --- Orders DB Operations ---
    def get_orders(self, status: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None, page: int = 1, page_size: int = 20):
        items = list(self.orders.values())
        if status:
            items = [o for o in items if o.order_status == status]
        if date_from:
            dt_from = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            items = [o for o in items if o.order_date >= dt_from]
        if date_to:
            dt_to = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
            items = [o for o in items if o.order_date <= dt_to]
            
        items.sort(key=lambda x: x.order_date, reverse=True)
        return self._paginate(items, page, page_size)

    def get_order(self, order_id: str) -> Order:
        if order_id not in self.orders:
            raise CRMException("Order not found", 404)
        return self.orders[order_id]

    def add_order(self, order: Order):
        if order.contact_id not in self.contacts:
            raise CRMException("Referenced contact_id does not exist", 409)
        if order.opportunity_id not in self.opportunities:
            raise CRMException("Referenced opportunity_id does not exist", 409)
        self.orders[order.order_id] = order
