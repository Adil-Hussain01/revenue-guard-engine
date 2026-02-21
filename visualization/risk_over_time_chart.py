import matplotlib.pyplot as plt
import pandas as pd
from visualization.chart_config import (
    COLOR_SAFE, COLOR_MONITOR, COLOR_CRITICAL, CHART_STYLE, PNG_DPI
)

def generate_risk_over_time(history_df, output_path):
    """
    Generates Chart 5: Risk Score Over Time (Line Chart)
    history_df: DataFrame with 'date' and 'avg_risk_score' columns
    """
    plt.rcParams.update(CHART_STYLE)
    
    if history_df.empty:
        # Create dummy data if empty
        history_df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=6, freq='M'),
            'avg_risk_score': [0] * 6
        })

    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Zones bands
    ax.axhspan(0, 30, color=COLOR_SAFE, alpha=0.1, label='Safe Zone')
    ax.axhspan(30, 70, color=COLOR_MONITOR, alpha=0.1, label='Monitor Zone')
    ax.axhspan(70, 100, color=COLOR_CRITICAL, alpha=0.1, label='Critical Zone')
    
    ax.plot(history_df['date'], history_df['avg_risk_score'], 
            marker='o', color='#ffffff', linewidth=3, markersize=8, 
            label='Avg Risk Score')
    
    ax.set_title("Trend: Average Transaction Risk (6 Months)", fontsize=16, pad=20)
    ax.set_xlabel("Time Period")
    ax.set_ylabel("Average Risk Score")
    ax.set_ylim(0, 100)
    
    ax.legend(facecolor='#313244', edgecolor='#45475a', loc='upper left')
    
    plt.grid(True, linestyle='--', alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=PNG_DPI)
    plt.close()

if __name__ == "__main__":
    # Test data
    dates = pd.date_range(start='2024-01-01', periods=6, freq='M')
    scores = [25, 28, 45, 32, 22, 18]
    test_df = pd.DataFrame({'date': dates, 'avg_risk_score': scores})
    generate_risk_over_time(test_df, "risk_time_test.png")
    print("Test chart generated: risk_time_test.png")
