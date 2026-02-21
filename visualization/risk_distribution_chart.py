import matplotlib.pyplot as plt
import numpy as np
from visualization.chart_config import (
    COLOR_SAFE, COLOR_MONITOR, COLOR_CRITICAL, CHART_STYLE, PNG_DPI
)

def generate_risk_distribution(risk_scores, output_path):
    """
    Generates a histogram of risk scores with color-coded zones.
    Chart 1: Risk Score Distribution (Histogram)
    """
    if not risk_scores:
        risk_scores = [0] # Handle empty data
        
    plt.rcParams.update(CHART_STYLE)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 20 bins for 0-100
    n, bins, patches = ax.hist(risk_scores, bins=20, range=(0, 100), edgecolor='#11111b', alpha=0.8)
    
    # Color bins based on zones
    # Safe (0-30), Monitor (30-70), Critical (70-100)
    for i in range(len(patches)):
        bin_center = (bins[i] + bins[i+1]) / 2
        if bin_center < 30:
            patches[i].set_facecolor(COLOR_SAFE)
        elif bin_center < 70:
            patches[i].set_facecolor(COLOR_MONITOR)
        else:
            patches[i].set_facecolor(COLOR_CRITICAL)
            
    # Annotations
    mean_val = np.mean(risk_scores)
    median_val = np.median(risk_scores)
    
    ax.axvline(mean_val, color='#ffffff', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
    ax.axvline(median_val, color='#89dceb', linestyle=':', linewidth=2, label=f'Median: {median_val:.1f}')
    
    ax.set_title("Risk Score Distribution Across Transactions", fontsize=16, pad=20)
    ax.set_xlabel("Risk Score (0-100)")
    ax.set_ylabel("Number of Transactions")
    ax.legend(facecolor='#313244', edgecolor='#45475a')
    
    plt.grid(True, axis='y', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=PNG_DPI)
    plt.close()

if __name__ == "__main__":
    # Test generation
    test_scores = np.random.normal(50, 20, 1000).clip(0, 100)
    generate_risk_distribution(test_scores, "risk_distribution_test.png")
    print("Test chart generated: risk_distribution_test.png")
