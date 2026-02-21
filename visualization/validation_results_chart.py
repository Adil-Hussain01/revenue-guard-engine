import matplotlib.pyplot as plt
from visualization.chart_config import (
    COLOR_SAFE, COLOR_MONITOR, COLOR_CRITICAL, CHART_STYLE, PNG_DPI
)

def generate_validation_donut(counts, output_path):
    """
    Generates Chart 3: Validation Result Breakdown (Donut)
    counts: Dict with 'Passed', 'Warning', 'Failed' keys
    """
    plt.rcParams.update(CHART_STYLE)
    
    labels = ['Passed', 'Warning', 'Failed']
    sizes = [counts.get('Passed', 0), counts.get('Warning', 0), counts.get('Failed', 0)]
    colors = [COLOR_SAFE, COLOR_MONITOR, COLOR_CRITICAL]
    
    # Filter out empty segments to avoid warnings/clutter
    filtered_labels = []
    filtered_sizes = []
    filtered_colors = []
    for l, s, c in zip(labels, sizes, colors):
        if s > 0:
            filtered_labels.append(l)
            filtered_sizes.append(s)
            filtered_colors.append(c)
            
    if not filtered_sizes:
        filtered_labels = ['No Data']
        filtered_sizes = [1]
        filtered_colors = ['#585b70']

    fig, ax = plt.subplots(figsize=(8, 8))
    
    wedges, texts, autotexts = ax.pie(
        filtered_sizes, 
        labels=filtered_labels, 
        colors=filtered_colors,
        autopct='%1.1f%%', 
        startangle=140, 
        pctdistance=0.85,
        wedgeprops={'width': 0.4, 'edgecolor': '#11111b'}
    )
    
    # Style the text
    for text in texts:
        text.set_color('white')
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        
    ax.set_title("System Health: Validation Outcomes", fontsize=16, pad=20)
    
    # Add total count in center
    total = sum(sizes)
    ax.text(0, 0, f"Total\n{total}", ha='center', va='center', fontsize=20, fontweight='bold', color='white')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=PNG_DPI)
    plt.close()

if __name__ == "__main__":
    test_counts = {'Passed': 750, 'Warning': 180, 'Failed': 70}
    generate_validation_donut(test_counts, "validation_donut_test.png")
    print("Test chart generated: validation_donut_test.png")
