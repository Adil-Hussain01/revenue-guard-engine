import os
import sys

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.data.synthetic_data_generator import SyntheticDataGenerator

def main():
    print("Initializing Generator...")
    generator = SyntheticDataGenerator()
    print("Generating Dataset...")
    dataset = generator.generate()
    print(f"Generated {len(dataset.orders)} transactions.")
    
    output_dir = os.path.join(os.path.dirname(__file__), "generated_data")
    print(f"Saving Dataset (JSON + CSV) to {output_dir}...")
    generator.save(dataset, output_dir=output_dir)
    print("Done.")

if __name__ == "__main__":
    main()
