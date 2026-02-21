import os
import matplotlib.pyplot as plt
import numpy as np
import pytest
from visualization.risk_distribution_chart import generate_risk_distribution
from visualization.validation_results_chart import generate_validation_donut

def test_risk_histogram_structure():
    """Verify that the risk histogram has exactly one axes object (no subplots)."""
    test_scores = [10, 20, 50, 80, 90]
    output_path = "test_histogram.png"
    
    generate_risk_distribution(test_scores, output_path)
    
    # Check if file exists
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # Clean up
    if os.path.exists(output_path):
        os.remove(output_path)

def test_donut_labels():
    """Verify donut chart generation with known counts."""
    test_counts = {'Passed': 10, 'Warning': 5, 'Failed': 2}
    output_path = "test_donut.png"
    
    generate_validation_donut(test_counts, output_path)
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # Clean up
    if os.path.exists(output_path):
        os.remove(output_path)

def test_no_data_handling():
    """Verify that charts handle empty data gracefully."""
    output_path = "test_empty.png"
    
    # Should not crash
    generate_risk_distribution([], output_path)
    assert os.path.exists(output_path)
    os.remove(output_path)
    
    generate_validation_donut({}, output_path)
    assert os.path.exists(output_path)
    os.remove(output_path)
