import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

def create_architecture_diagram():
    """Generates a high-level system architecture diagram."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Define box styles
    box_style = dict(boxstyle="round,pad=0.5", fc="#f0f0f0", ec="#333333", lw=2)
    arrow_props = dict(arrowstyle="->", color="#555555", lw=2)

    # Draw nodes
    # Data Source
    ax.text(15, 80, "Synthetic Data\nGenerator (Faker)", ha="center", va="center", size=12, bbox=dict(boxstyle="round,pad=0.5", fc="#e1f5fe", ec="#0277bd", lw=2))
    
    # API Layer
    ax.text(50, 80, "API Simulation Layer\n(FastAPI)", ha="center", va="center", size=12, bbox=dict(boxstyle="round,pad=0.5", fc="#fff9c4", ec="#fbc02d", lw=2))
    
    # Core Engine
    ax.text(50, 50, "Validation Engine\n(12+ Rules)", ha="center", va="center", size=14, weight='bold', bbox=dict(boxstyle="round,pad=0.8", fc="#e8f5e9", ec="#2e7d32", lw=2))
    
    # Outputs
    ax.text(20, 20, "Risk Scoring\n(0-100)", ha="center", va="center", size=12, bbox=dict(boxstyle="round,pad=0.5", fc="#ffebee", ec="#c62828", lw=2))
    ax.text(50, 20, "Audit Logs\n(JSON)", ha="center", va="center", size=12, bbox=dict(boxstyle="round,pad=0.5", fc="#f3e5f5", ec="#7b1fa2", lw=2))
    ax.text(80, 20, "Visualization\nDashboard", ha="center", va="center", size=12, bbox=dict(boxstyle="round,pad=0.5", fc="#e0f7fa", ec="#006064", lw=2))

    # Draw edges
    ax.annotate("", xy=(30, 80), xytext=(65, 80), arrowprops=arrow_props) # Gen -> API (Wait, this is backwards in my head, let's fix)
    # Actually: Generator -> API. So 15 -> 50.
    ax.annotate("", xy=(32, 80), xytext=(28, 80), arrowprops=arrow_props) 
    
    # Let's draw manual arrows for better control
    # Generator -> API
    ax.arrow(28, 80, 8, 0, head_width=2, head_length=2, fc='k', ec='k')
    
    # API -> Engine
    ax.arrow(50, 72, 0, -12, head_width=2, head_length=2, fc='k', ec='k')
    
    # Engine -> Risk
    ax.arrow(40, 45, -12, -15, head_width=2, head_length=2, fc='k', ec='k')
    
    # Engine -> Audit
    ax.arrow(50, 42, 0, -12, head_width=2, head_length=2, fc='k', ec='k')
    
    # Engine -> Visuals
    ax.arrow(60, 45, 12, -15, head_width=2, head_length=2, fc='k', ec='k')

    plt.title("Revenue Leakage Engine - System Architecture", fontsize=16, weight='bold', pad=20)
    plt.tight_layout()
    plt.savefig("system_architecture.png", dpi=300)
    plt.close()

def create_leakage_dashboard():
    """Generates a mock dashboard showing leakage metrics."""
    # Data simulation
    categories = ['Price Mismatch', 'Missing Invoice', 'Tax Error', 'Status Sync', 'Duplicate']
    values = [4500, 12000, 2300, 800, 150]
    colors = ['#ff9999', '#ffcc99', '#99ff99', '#ffcc00', '#66b3ff']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Pie Chart
    wedges, texts, autotexts = ax1.pie(values, labels=categories, autopct='%1.1f%%', startangle=90, colors=colors, explode=(0.05, 0.1, 0, 0, 0))
    ax1.set_title("Revenue Leakage by Category", fontsize=14, weight='bold')
    
    # Bar Chart - Monthly Trend
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    leakage_trend = [2000, 1800, 4500, 3200, 2800, 1500] # Spike in March
    
    bars = ax2.bar(months, leakage_trend, color='#4dd0e1')
    ax2.set_title("Monthly Revenue Leakage Trend ($)", fontsize=14, weight='bold')
    ax2.set_ylabel("Leakage Amount ($)")
    
    # Highlight the spike
    bars[2].set_color('#ef5350')
    ax2.text(2, 4600, "Anomaly Spike!", ha='center', color='#d32f2f', weight='bold')

    plt.suptitle("Revenue Integrity Dashboard - Q1/Q2 2024", fontsize=18, weight='bold')
    plt.tight_layout()
    plt.savefig("leakage_dashboard.png", dpi=300)
    plt.close()

def create_risk_heatmap():
    """Generates a risk heatmap."""
    # Generate mock risk data
    np.random.seed(42)
    data = np.random.rand(10, 10) * 100 # 10x10 grid of transactions
    
    # Inject high risk cluster
    data[2:5, 6:9] = np.random.uniform(80, 100, (3, 3))
    
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(data, cmap='RdYlGn_r', interpolation='nearest') # Red is high risk (100), Green is low (0)
    
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Risk Score (0-100)", rotation=-90, va="bottom")
    
    ax.set_title("Transaction Risk Heatmap", fontsize=16, weight='bold')
    ax.set_xlabel("Transaction Batch ID")
    ax.set_ylabel("Validation Rule ID")
    
    # Annotate a high risk area
    rect = patches.Rectangle((5.5, 1.5), 3, 3, linewidth=2, edgecolor='red', facecolor='none')
    ax.add_patch(rect)
    ax.text(9, 3, "Critical Pricing Errors\n(Rule ID 6-8)", color='red', weight='bold', ha='left')

    plt.tight_layout()
    plt.savefig("risk_heatmap.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    print("Generating visuals...")
    create_architecture_diagram()
    print("- Created system_architecture.png")
    create_leakage_dashboard()
    print("- Created leakage_dashboard.png")
    create_risk_heatmap()
    print("- Created risk_heatmap.png")
    print("Done!")
