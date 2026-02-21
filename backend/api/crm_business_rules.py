from decimal import Decimal
from typing import Literal

from backend.api.crm_models import Order, Deal
from backend.api.crm_store import CRMException

# Order of stages to validate linear progression
DEAL_STAGES = ["prospect", "negotiation", "proposal", "closed_won", "closed_lost"]

def validate_deal_stage_progression(current_stage: str, new_stage: str):
    """
    Ensures a deal stage only moves forward, except for closing out logic.
    Throws CRMException (409) if moved backwards.
    """
    if current_stage not in DEAL_STAGES or new_stage not in DEAL_STAGES:
        raise CRMException("Invalid deal stage", 400)
        
    current_idx = DEAL_STAGES.index(current_stage)
    new_idx = DEAL_STAGES.index(new_stage)
    
    # Can always move to closed states, can't move backwards
    if new_stage not in ["closed_won", "closed_lost"]:
        if new_idx < current_idx:
            raise CRMException(
                f"Cannot move deal backward from {current_stage} to {new_stage}",
                409
            )

def validate_order_discount(discount_pct: Decimal, approval_status: str):
    """
    Enforces the discount cap. Any discount > 15% requires approval_status to be 'approved'.
    Throws CRMException (409) if violated.
    """
    if discount_pct > Decimal("15.0") and approval_status != "approved":
        raise CRMException(
            "Orders with discount > 15% require explicit managerial approval",
            409
        )

def validate_invoice_gate(order_status: str, approval_status: str):
    """
    Validates that if an order transitions near fulfillment (mocking an invoice step logic),
    that it has been approved.
    (This simulates the boundary before creating invoices upstream).
    """
    if order_status in ["confirmed", "fulfilled"] and approval_status != "approved":
         # In a real CRM, standard orders might not require approval, but our rule
         # is that if 'approved' tracking exists it should be met for fulfillment
         raise CRMException(
            f"Cannot transition order to {order_status} without approval",
            409
         )
