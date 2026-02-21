import pytest
from datetime import datetime, timedelta

from backend.data.synthetic_data_generator import SyntheticDataGenerator
from backend.data.config import GENERATOR_CONFIG

def test_volume_and_entity_integrity():
    generator = SyntheticDataGenerator()
    dataset = generator.generate()

    assert len(dataset.orders) == GENERATOR_CONFIG["num_transactions"]
    assert len(dataset.contacts) == GENERATOR_CONFIG["num_contacts"]
    
    # Check that every invoice references a valid order
    order_ids = {o.order_id for o in dataset.orders}
    for inv in dataset.invoices:
        assert inv.order_id in order_ids

def test_anomaly_rates():
    config = GENERATOR_CONFIG.copy()
    config["num_transactions"] = 2000 # larger sample for better rate accuracy
    generator = SyntheticDataGenerator(config=config)
    dataset = generator.generate()
    
    total = len(dataset.orders)
    
    # Check missing invoices
    missing_inv_count = sum(1 for a in dataset.anomaly_manifest if a.type == "missing_invoice")
    expected_missing = int(total * config["anomaly_rates"]["missing_invoice"])
    assert missing_inv_count == expected_missing
    
    # Check pricing drift
    drift_count = sum(1 for a in dataset.anomaly_manifest if a.type == "pricing_drift")
    expected_drift = int(total * config["anomaly_rates"]["pricing_drift"])
    assert drift_count == expected_drift

def test_determinism():
    gen1 = SyntheticDataGenerator()
    ds1 = gen1.generate()
    
    gen2 = SyntheticDataGenerator()
    ds2 = gen2.generate()
    
    assert ds1.orders[0].order_id == ds2.orders[0].order_id
    assert ds1.orders[0].total_amount == ds2.orders[0].total_amount

def test_date_ranges():
    generator = SyntheticDataGenerator()
    dataset = generator.generate()
    
    total_months = GENERATOR_CONFIG["date_range_months"]
    start_limit = datetime.now() - timedelta(days=30 * total_months + 10)
    
    for order in dataset.orders:
        assert order.order_date.timestamp() > start_limit.timestamp()
