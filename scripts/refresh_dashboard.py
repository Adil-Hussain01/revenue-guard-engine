import os
import sys

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.validation_controller import _get_engine
from visualization.chart_exporter import ChartExporter

def main():
    print("Initializing Engine...")
    engine = _get_engine()
    
    print("Running Full Reconciliation Scan...")
    results = engine.reconcile_all()
    print(f"Validated {len(results)} transactions.")
    
    # Check if we have data, if not, generate some first
    if len(results) == 0:
        print("No data found. Running data generator first...")
        from backend.data.synthetic_data_generator import SyntheticDataGenerator
        generator = SyntheticDataGenerator()
        dataset = generator.generate()
        generator.save(dataset)
        results = engine.reconcile_all()
    
    print("Exporting Dashboard Assets...")
    chart_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend/dashboard/static/charts")
    exporter = ChartExporter(chart_dir)
    exporter.export_all(results)
    
    print("Refresh Complete.")

if __name__ == "__main__":
    main()
