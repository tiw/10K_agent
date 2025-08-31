"""
Financial Analysis Module

Advanced financial analysis capabilities including funnel analysis,
trend analysis, drill-down analysis, efficiency calculation, and comprehensive metrics calculation.
"""

from .funnel_analyzer import FunnelAnalyzer, FunnelLevel, FinancialFunnel
from .trend_analyzer import TrendAnalyzer, TrendPoint, TrendAnalysis, ComprehensiveTrendReport
from .drill_down_engine import DrillDownEngine, DrillDownAnalysis, BreakdownItem, BreakdownType
from .efficiency_calculator import EfficiencyCalculator, EfficiencyMetric, ConversionAnalysis, MarginAnalysis, CapitalEfficiencyAnalysis
from .metrics_calculator import MetricsCalculator, MetricDefinition, MetricResult, TrendMetric

__all__ = [
    "FunnelAnalyzer",
    "FunnelLevel", 
    "FinancialFunnel",
    "TrendAnalyzer",
    "TrendPoint",
    "TrendAnalysis", 
    "ComprehensiveTrendReport",
    "DrillDownEngine",
    "DrillDownAnalysis",
    "BreakdownItem",
    "BreakdownType",
    "EfficiencyCalculator",
    "EfficiencyMetric",
    "ConversionAnalysis",
    "MarginAnalysis",
    "CapitalEfficiencyAnalysis",
    "MetricsCalculator",
    "MetricDefinition",
    "MetricResult",
    "TrendMetric"
]