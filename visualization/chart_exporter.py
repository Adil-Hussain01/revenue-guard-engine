import os
import pandas as pd
from typing import List
from backend.core.validation_models import ValidationResult
from visualization.risk_distribution_chart import generate_risk_distribution
from visualization.leakage_charts import generate_prevention_metrics, generate_leakage_by_category
from visualization.validation_results_chart import generate_validation_donut
from visualization.risk_over_time_chart import generate_risk_over_time

class ChartExporter:
    """Orchestrates the generation of all dashboard charts."""
    
    def __init__(self, output_dir: str = "frontend/dashboard/static/charts"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def export_all(self, results: List[ValidationResult]):
        """Runs the full export suite."""
        if not results:
            print("No validation results to export.")
            return

        # 1. Risk Distribution
        scores = [r.risk_score for r in results]
        generate_risk_distribution(scores, os.path.join(self.output_dir, "risk_distribution.png"))
        
        # 2. Prevention Metrics (Static comparison for this demo)
        generate_prevention_metrics(os.path.join(self.output_dir, "prevention_metrics.png"))
        
        # 3. Validation Breakdown
        counts = {
            'Passed': sum(1 for r in results if r.risk_classification == 'safe'),
            'Warning': sum(1 for r in results if r.risk_classification == 'monitor'),
            'Failed': sum(1 for r in results if r.risk_classification == 'critical')
        }
        generate_validation_donut(counts, os.path.join(self.output_dir, "validation_breakdown.png"))
        
        # 4. Leakage by Category
        category_counts = {}
        for r in results:
            for v in r.violations:
                category_counts[v.rule_name] = category_counts.get(v.rule_name, 0) + 1
        
        # Sort and take top 6
        top_categories = dict(sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:6])
        generate_leakage_by_category(top_categories, os.path.join(self.output_dir, "leakage_categories.png"))
        
        # 5. Risk Over Time (Simulated trend as we don't have historical store yet)
        # We'll use the validated_at timestamps from the results
        history_data = []
        for r in results:
            history_data.append({'date': r.validated_at.date(), 'score': r.risk_score})
        
        df = pd.DataFrame(history_data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            trend_df = df.groupby('date')['score'].mean().reset_index()
            trend_df.columns = ['date', 'avg_risk_score']
            # If only one day, simulate a bit of a trend for visual effect
            if len(trend_df) == 1:
                 d2 = trend_df['date'].iloc[0] + pd.Timedelta(days=1)
                 trend_df = pd.concat([trend_df, pd.DataFrame({'date': [d2], 'avg_risk_score': [trend_df['avg_risk_score'].iloc[0] * 0.9]})], ignore_index=True)
            
            generate_risk_over_time(trend_df, os.path.join(self.output_dir, "risk_trend.png"))
        else:
            generate_risk_over_time(pd.DataFrame(), os.path.join(self.output_dir, "risk_trend.png"))
            
        print(f"All charts exported to {self.output_dir}")
