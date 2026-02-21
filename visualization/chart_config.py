"""
Global configuration for Matplotlib charts to ensure consistent premium look.
"""

# Colors
COLOR_SAFE = "#2ecc71"      # Green
COLOR_MONITOR = "#f1c40f"   # Yellow
COLOR_CRITICAL = "#e74c3c"  # Red
COLOR_BACKGROUND = "#1e1e2e" # Dark background
COLOR_TEXT = "#cdd6f4"       # Light text
COLOR_GRID = "#45475a"       # Subtle grid

CHART_STYLE = {
    "text.color": COLOR_TEXT,
    "axes.labelcolor": COLOR_TEXT,
    "axes.edgecolor": COLOR_GRID,
    "axes.facecolor": COLOR_BACKGROUND,
    "figure.facecolor": COLOR_BACKGROUND,
    "xtick.color": COLOR_TEXT,
    "ytick.color": COLOR_TEXT,
    "grid.color": COLOR_GRID,
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Roboto", "Arial", "DejaVu Sans"],
}

PNG_DPI = 150
PNG_TRANSPARENT = False
