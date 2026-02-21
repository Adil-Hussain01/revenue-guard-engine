import matplotlib.pyplot as plt
import numpy as np
from visualization.chart_config import (
    COLOR_SAFE, COLOR_MONITOR, COLOR_CRITICAL, CHART_STYLE, PNG_DPI
)

def generate_prevention_metrics(output_path):
    """
    Generates Chart 2: Revenue Leakage Prevention (Grouped Bar)
    Comparing Before Automation vs After Engine.
    """
    plt.rcParams.update(CHART_STYLE)
    
    categories = ['Manual Review\nTime (Hrs)', 'Error Detection\nRate (%)', 'Audit\nVisibility (%)']
    before = [40, 35, 20]
    after = [8, 94, 98]
    
    x = np.arange(len(categories))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    rects1 = ax.bar(x - width/2, before, width, label='Before Engine', color='#585b70', alpha=0.8)
    rects2 = ax.bar(x + width/2, after, width, label='With Revenue Guard', color=COLOR_SAFE, alpha=0.9)
    
    ax.set_title("Engine Efficiency & Performance Gains", fontsize=16, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend(facecolor='#313244', edgecolor='#45475a')
    
    # Add percentage change labels
    # Manual Review: -80%, Error Detection: +169%, Audit Visibility: +390%
    changes = ["-80%", "+169%", "+390%"]
    
    for i, p in enumerate(rects2):
        height = p.get_height()
        ax.annotate(changes[i],
                    xy=(p.get_x() + p.get_width() / 2, height),
                    xytext=(0, 5),  # 5 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color=COLOR_SAFE)

    plt.tight_layout()
    plt.savefig(output_path, dpi=PNG_DPI)
    plt.close()

def generate_leakage_by_category(category_data, output_path):
    """
    Generates Chart 4: Leakage by Category (Horizontal Bar)
    category_data: Dict mapping category name to count/impact
    """
    if not category_data:
        category_data = {"N/A": 0}

    plt.rcParams.update(CHART_STYLE)
    
    categories = list(category_data.keys())
    values = list(category_data.values())
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    y_pos = np.arange(len(categories))
    
    # Use a gradient or consistent color
    ax.barh(y_pos, values, align='center', color=COLOR_CRITICAL, alpha=0.8)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Anomaly Count / Risk Impact')
    ax.set_title('Top Revenue Leakage Categories', fontsize=16, pad=20)
    
    plt.grid(True, axis='x', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=PNG_DPI)
    plt.close()

if __name__ == "__main__":
    generate_prevention_metrics("prevention_test.png")
    test_leakage = {
        "Pricing Drift": 45,
        "Missing Invoice": 12,
        "Duplicate Invoice": 8,
        "Unauthorized Discount": 22,
        "Payment Mismatch": 15,
        "Stale Invoice": 5
    }
    generate_leakage_by_category(test_leakage, "leakage_test.png")
    print("Test charts generated: prevention_test.png, leakage_test.png")
