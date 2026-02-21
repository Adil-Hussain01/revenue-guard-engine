import random
from typing import Dict, Any
from datetime import datetime, timedelta
import uuid

from .models import GeneratedDataset, AnomalyRecord

class AnomalyInjector:
    """Applies business-realistic anomalies to clean data."""

    def __init__(self, rates: Dict[str, float], rng: random.Random):
        """
        Initializes the AnomalyInjector.

        Args:
            rates (Dict[str, float]): The distribution percentages for each anomaly type.
            rng (random.Random): A seeded random number generator for deterministic injection.
        """
        self.rates = rates
        self.rng = rng

    def inject(self, dataset: GeneratedDataset) -> GeneratedDataset:
        """
        Iterates over the dataset and injects statistical anomalies matching the `rates` config.

        Args:
            dataset (GeneratedDataset): The pristine generated dataset.

        Returns:
            GeneratedDataset: The dataset populated with missing entries, drifted values, etc.
        """
        total_txns = len(dataset.orders)
        
        missing_inv_target = int(total_txns * self.rates.get("missing_invoice", 0.05))
        pricing_drift_target = int(total_txns * self.rates.get("pricing_drift", 0.08))
        duplicate_inv_target = int(total_txns * self.rates.get("duplicate_invoice", 0.03))
        unauth_disc_target = int(total_txns * self.rates.get("unauthorized_discount", 0.06))
        payment_mis_target = int(total_txns * self.rates.get("payment_mismatch", 0.04))
        stale_unpaid_target = int(total_txns * self.rates.get("stale_unpaid", 0.05))

        indices = list(range(total_txns))
        self.rng.shuffle(indices)

        start = 0
        missing_inv_idx = set(indices[start:start+missing_inv_target])
        start += missing_inv_target
        pricing_drift_idx = set(indices[start:start+pricing_drift_target])
        start += pricing_drift_target
        duplicate_inv_idx = set(indices[start:start+duplicate_inv_target])
        start += duplicate_inv_target
        unauth_disc_idx = set(indices[start:start+unauth_disc_target])
        start += unauth_disc_target
        payment_mis_idx = set(indices[start:start+payment_mis_target])
        start += payment_mis_target
        stale_unpaid_idx = set(indices[start:start+stale_unpaid_target])

        manifest = []
        new_invoices = []
        new_payments = []
        new_ledger = []
        
        now = datetime.now()

        invoice_lookup = {i.order_id: i for i in dataset.invoices}
        payment_lookup = {p.invoice_id: p for p in dataset.payments}
        ledger_lookup = {l.invoice_id: l for l in dataset.ledger_entries}

        for i, order in enumerate(dataset.orders):
            invoice = invoice_lookup.get(order.order_id)
            payment = payment_lookup.get(invoice.invoice_id) if invoice else None
            ledger = ledger_lookup.get(invoice.invoice_id) if invoice else None

            if i in missing_inv_idx:
                manifest.append(AnomalyRecord(
                    anomaly_id=f"ANO-MISS-{order.order_id}",
                    type="missing_invoice",
                    affected_entity="invoice",
                    entity_id=order.order_id,
                    related_entity_id=order.order_id,
                    expected_value=1.0,
                    actual_value=0.0,
                    injected_at=now
                ))
                invoice = None
                payment = None
                ledger = None
                
            elif i in pricing_drift_idx and invoice:
                expected = invoice.amount_due
                drift_type = self.rng.choice([1.05, 1.10, 0.9])
                actual = round(expected * drift_type, 2)
                
                invoice.amount_due = actual
                invoice.amount_paid = actual
                if payment:
                    payment.amount = actual
                if ledger:
                    ledger.debit = actual
                    ledger.credit = actual
                    
                manifest.append(AnomalyRecord(
                    anomaly_id=f"ANO-DRIFT-{invoice.invoice_id}",
                    type="pricing_drift",
                    affected_entity="invoice",
                    entity_id=invoice.invoice_id,
                    related_entity_id=order.order_id,
                    expected_value=expected,
                    actual_value=actual,
                    drift_pct=round((actual - expected) / expected * 100, 2),
                    injected_at=now
                ))

            elif i in duplicate_inv_idx and invoice:
                new_inv_id = f"{invoice.invoice_id}-DUP"
                dup_invoice = invoice.model_copy()
                dup_invoice.invoice_id = new_inv_id
                new_invoices.append(dup_invoice)
                
                manifest.append(AnomalyRecord(
                    anomaly_id=f"ANO-DUP-{invoice.invoice_id}",
                    type="duplicate_invoice",
                    affected_entity="invoice",
                    entity_id=new_inv_id,
                    related_entity_id=order.order_id,
                    expected_value=1.0,
                    actual_value=2.0,
                    injected_at=now
                ))

            elif i in unauth_disc_idx:
                opp_id = order.opportunity_id
                opp = next(o for o in dataset.opportunities if o.opportunity_id == opp_id)
                expected_pct = opp.discount_pct
                
                new_pct = round(self.rng.uniform(16.0, 35.0), 1)
                opp.discount_pct = new_pct
                opp.approval_status = "pending"
                
                new_total = round((opp.quantity * opp.unit_price) * (1 - new_pct/100), 2)
                order.total_amount = new_total
                order.discount_applied = round((opp.quantity * opp.unit_price) - new_total, 2)
                
                if invoice:
                    invoice.amount_due = new_total
                    invoice.amount_paid = new_total
                if payment:
                    payment.amount = new_total
                if ledger:
                    ledger.debit = new_total
                    ledger.credit = new_total

                manifest.append(AnomalyRecord(
                    anomaly_id=f"ANO-DISC-{opp.opportunity_id}",
                    type="unauthorized_discount",
                    affected_entity="opportunity",
                    entity_id=opp.opportunity_id,
                    related_entity_id=order.order_id,
                    expected_value=expected_pct,
                    actual_value=new_pct,
                    injected_at=now
                ))

            elif i in payment_mis_idx and invoice and payment:
                expected = invoice.amount_due
                actual = round(expected * self.rng.uniform(0.1, 0.9), 2)
                payment.amount = actual
                if ledger:
                    ledger.credit = actual
                    
                manifest.append(AnomalyRecord(
                    anomaly_id=f"ANO-PAY-{payment.payment_id}",
                    type="payment_mismatch",
                    affected_entity="payment",
                    entity_id=payment.payment_id,
                    related_entity_id=invoice.invoice_id,
                    expected_value=expected,
                    actual_value=actual,
                    injected_at=now
                ))

            elif i in stale_unpaid_idx and invoice:
                days_ago = self.rng.randint(65, 100)
                invoice.issue_date = now - timedelta(days=days_ago)
                invoice.due_date = invoice.issue_date + timedelta(days=30)
                invoice.status = "unpaid"
                invoice.amount_paid = 0.0
                
                payment = None
                
                manifest.append(AnomalyRecord(
                    anomaly_id=f"ANO-STALE-{invoice.invoice_id}",
                    type="stale_unpaid",
                    affected_entity="invoice",
                    entity_id=invoice.invoice_id,
                    related_entity_id=order.order_id,
                    expected_value=0.0,
                    actual_value=days_ago,
                    injected_at=now
                ))

            if invoice:
                new_invoices.append(invoice)
            if payment:
                new_payments.append(payment)
            if ledger:
                new_ledger.append(ledger)

        dataset.invoices = new_invoices
        dataset.payments = new_payments
        dataset.ledger_entries = new_ledger
        dataset.anomaly_manifest = manifest

        return dataset
