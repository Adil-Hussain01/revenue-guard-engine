import os
import json
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

from .models import (
    Contact, Deal, Opportunity, Order,
    Invoice, Payment, LedgerEntry,
    GeneratedDataset
)
from .config import GENERATOR_CONFIG
from .anomaly_injector import AnomalyInjector

class DataIngestor:
    """Orchestrates end-to-end dataset ingestion."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initializes the Data Generator with configurable boundaries and anomaly rates.

        Args:
            config (Dict[str, Any], optional): Dictionary specifying scale parameters and anomaly distributions.
        """
        self.config = config or GENERATOR_CONFIG
        self.seed = self.config.get("seed", 42)
        self.faker = Faker()
        self.faker.seed_instance(self.seed)
        random.seed(self.seed)
        self.rng = random.Random(self.seed)

    def generate(self) -> GeneratedDataset:
        """
        Executes the dataset generation sequence (Contacts -> Dependencies -> Anomalies).

        Returns:
            GeneratedDataset: Complete structured dataset populated with anomalies.
        """
        num_contacts = self.config["num_contacts"]
        num_transactions = self.config["num_transactions"]
        date_range_months = self.config["date_range_months"]

        start_date = datetime.now() - timedelta(days=30 * date_range_months)

        # 1. Generate Contacts
        contacts = []
        for i in range(num_contacts):
            contact_id = f"CNT-{i+1:04d}"
            contacts.append(Contact(
                contact_id=contact_id,
                name=self.faker.name(),
                email=self.faker.email(),
                company=self.faker.company(),
                created_at=self.faker.date_time_between(start_date=start_date)
            ))

        # 2. Generate Base Transactions
        deals, opportunities, orders = [], [], []
        invoices, payments, ledger_entries = [], [], []

        for i in range(num_transactions):
            contact = self.rng.choice(contacts)
            txn_date = self.faker.date_time_between(start_date=contact.created_at)

            # Deal
            deal_id = f"DL-{i+1:05d}"
            deal_value = round(self.rng.uniform(500, 10000), 2)
            deals.append(Deal(
                deal_id=deal_id,
                contact_id=contact.contact_id,
                stage="closed_won",
                value=deal_value,
                assigned_to=self.faker.name(),
                created_at=txn_date
            ))

            # Opportunity
            opp_id = f"OPP-{i+1:05d}"
            product_id = f"PROD-{self.rng.randint(1, self.config.get('num_products', 50)):03d}"
            qty = self.rng.randint(1, 10)
            unit_price = round(deal_value / qty, 2)
            discount_pct = round(self.rng.uniform(0, 15), 1)

            opportunities.append(Opportunity(
                opportunity_id=opp_id,
                deal_id=deal_id,
                product_id=product_id,
                quantity=qty,
                unit_price=unit_price,
                discount_pct=discount_pct,
                approval_status="approved"
            ))

            # Order
            order_id = f"ORD-{i+1:05d}"
            total_amount = round((qty * unit_price) * (1 - discount_pct/100), 2)
            discount_applied = round((qty * unit_price) - total_amount, 2)
            order_date = txn_date + timedelta(hours=self.rng.randint(1, 72))

            orders.append(Order(
                order_id=order_id,
                opportunity_id=opp_id,
                contact_id=contact.contact_id,
                total_amount=total_amount,
                discount_applied=discount_applied,
                order_date=order_date,
                status="completed"
            ))

            # Invoice
            invoice_id = f"INV-{i+1:05d}"
            issue_date = order_date + timedelta(days=self.rng.randint(1, 5))
            due_date = issue_date + timedelta(days=30)
            
            invoices.append(Invoice(
                invoice_id=invoice_id,
                order_id=order_id,
                amount_due=total_amount,
                amount_paid=total_amount,
                status="paid",
                issue_date=issue_date,
                due_date=due_date
            ))

            # Payment
            payment_id = f"PAY-{i+1:05d}"
            payment_date = issue_date + timedelta(days=self.rng.randint(1, 28))
            
            payments.append(Payment(
                payment_id=payment_id,
                invoice_id=invoice_id,
                amount=total_amount,
                payment_method=self.rng.choice(["credit_card", "ach", "wire"]),
                payment_date=payment_date,
                status="completed"
            ))

            # Ledger Entry
            entry_id = f"LEDG-{i+1:05d}"
            ledger_entries.append(LedgerEntry(
                entry_id=entry_id,
                invoice_id=invoice_id,
                debit=total_amount,
                credit=total_amount,
                account="Accounts Receivable",
                posted_date=payment_date
            ))

        dataset = GeneratedDataset(
            contacts=contacts,
            deals=deals,
            opportunities=opportunities,
            orders=orders,
            invoices=invoices,
            payments=payments,
            ledger_entries=ledger_entries,
            anomaly_manifest=[]
        )

        # 3. Inject Anomalies
        rates = self.config.get("anomaly_rates", {})
        injector = AnomalyInjector(rates=rates, rng=self.rng)
        dataset = injector.inject(dataset)

        return dataset

    def save(self, dataset: GeneratedDataset, output_dir: str = "output", formats: List[str] = None):
        """
        Serializes the generated dataset to permanent storage in requested formats.

        Args:
            dataset (GeneratedDataset): The dataset to save representing all transactions.
            output_dir (str): Relative or absolute target output destination.
            formats (List[str]): Extracted format options. Combines 'json' and 'csv'.
        """
        if formats is None:
            formats = ["json", "csv"]
            
        os.makedirs(output_dir, exist_ok=True)
        
        entities = {
            "contacts": [c.model_dump() for c in dataset.contacts],
            "deals": [d.model_dump() for d in dataset.deals],
            "opportunities": [o.model_dump() for o in dataset.opportunities],
            "orders": [o.model_dump() for o in dataset.orders],
            "invoices": [i.model_dump() for i in dataset.invoices],
            "payments": [p.model_dump() for p in dataset.payments],
            "ledger_entries": [l.model_dump() for l in dataset.ledger_entries],
            "anomaly_manifest": [a.model_dump() for a in dataset.anomaly_manifest]
        }
        
        for name, data_list in entities.items():
            if "json" in formats:
                with open(os.path.join(output_dir, f"{name}.json"), "w") as f:
                    json.dump(data_list, f, indent=2, default=str)
            if "csv" in formats and data_list:
                df = pd.DataFrame(data_list)
                df.to_csv(os.path.join(output_dir, f"{name}.csv"), index=False)
