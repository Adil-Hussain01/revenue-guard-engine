import os

# Base default settings for synthetic data generation
GENERATOR_CONFIG = {
    "num_transactions": 1000,
    "num_contacts": 200,
    "num_products": 50,
    "date_range_months": 12,
    "anomaly_rates": {
        "missing_invoice": 0.05,
        "pricing_drift": 0.08,
        "duplicate_invoice": 0.03,
        "unauthorized_discount": 0.06,
        "payment_mismatch": 0.04,
        "stale_unpaid": 0.05,
    },
    "seed": 42,  # reproducibility
}
