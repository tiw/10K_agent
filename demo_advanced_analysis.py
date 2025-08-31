#!/usr/bin/env python3
"""
Advanced Financial Analysis Demo

This script demonstrates the advanced financial analysis capabilities
including funnel analysis, trend analysis, drill-down analysis, and efficiency calculations.
"""

import sys
import json
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from xbrl_financial_service import XBRLParser, FinancialService, Config
from xbrl_financial_service.analysis import (
    FunnelAnalyzer, TrendAnalyzer, DrillDownEngine, EfficiencyCalculator
)
from xbrl_financial_service.utils.logging import setup_logging


def demo_advanced_analysis():
    """Demonstrate advanced financial analysis capabilities"""
    print("🚀 Advanced Financial Analysis Demo")
    print("=" * 60)
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Create configuration
    config = Config()
    config.enable_parallel_processing = True
    
    # Create parser
    parser = XBRLParser(config)
    
    # Define file paths for Apple's 10-K filing
    file_paths = {
        'schema': 'aapl-20240928.xsd',
        'calculation': 'aapl-20240928_cal.xml',
        'definition': 'aapl-20240928_def.xml',
        'label': 'aapl-20240928_lab.xml',
        'presentation': 'aapl-20240928_pre.xml',
        'instance': 'aapl-20240928_htm.xml'
    }
    
    # Check which files are available
    available_files = {}
    missing_files = []
    
    for file_type, file_path in file_paths.items():
        if Path(file_path).exists():
            available_files[file_type] = file_path
        else:
            missing_files.append(f"{file_type}: {file_path}")
    
    if missing_files:
        print(f"⚠️  Missing files: {', '.join(missing_files)}")
        print(f"This demo requires Apple's XBRL files to be in the current directory.")
        return False
    
    try:
        print(f"📊 Parsing Apple's XBRL filing...")
        
        # Parse the filing
        filing_data = parser.parse_filing(available_files)
        
        print(f"✅ Successfully parsed filing!")
        print(f"   Company: {filing_data.company_info.name}")
        print(f"   Total Facts: {len(filing_data.all_facts)}")
        
        # Create financial service
        service = FinancialService(filing_data, config)
        
        # Demonstrate Funnel Analysis
        print(f"\n🔄 FUNNEL ANALYSIS")
        print("=" * 40)
        
        funnel_analyzer = FunnelAnalyzer(filing_data)
        
        # Profitability funnel
        profitability_funnel = funnel_analyzer.get_profitability_funnel()
        print(f"\n📈 Profitability Funnel ({profitability_funnel.company_name}):")
        for level in profitability_funnel.levels:
            conversion_text = f" ({level.conversion_rate:.1f}%)" if level.conversion_rate else ""
            print(f"   {level.name}: ${level.value:,.0f}{conversion_text}")
            
            # Show children if available
            for child in level.children:
                child_conversion = f" ({child.conversion_rate:.1f}%)" if child.conversion_rate else ""
                print(f"     └─ {child.name}: ${child.value:,.0f}{child_conversion}")
        
        print(f"\n💡 Key Insights:")
        for insight in profitability_funnel.key_insights[:3]:
            print(f"   • {insight}")
        
        # Cash conversion funnel
        cash_funnel = funnel_analyzer.get_cash_conversion_funnel()
        print(f"\n💰 Cash Conversion Funnel:")
        for level in cash_funnel.levels:
            conversion_text = f" ({level.conversion_rate:.1f}%)" if level.conversion_rate else ""
            print(f"   {level.name}: ${level.value:,.0f}{conversion_text}")
        
        # Demonstrate Trend Analysis
        print(f"\n📈 TREND ANALYSIS")
        print("=" * 40)
        
        trend_analyzer = TrendAnalyzer(filing_data)
        
        # Revenue trend
        revenue_trend = trend_analyzer.analyze_revenue_trend()
        if revenue_trend and revenue_trend.data_points:
            print(f"\n📊 Revenue Trend Analysis:")
            print(f"   Periods analyzed: {len(revenue_trend.data_points)}")
            if revenue_trend.cagr:
                print(f"   CAGR: {revenue_trend.cagr:.2f}%")
            print(f"   Trend direction: {revenue_trend.trend_direction}")
            print(f"   Average growth: {revenue_trend.average_growth_rate:.2f}%" if revenue_trend.average_growth_rate else "   Average growth: N/A")
            
            print(f"\n   Period-by-period data:")
            for point in revenue_trend.data_points:
                print(f"     {point.period}: ${point.value:,.0f}")
        
        # Comprehensive trend report
        comprehensive_report = trend_analyzer.generate_comprehensive_report()
        print(f"\n📋 Comprehensive Trend Report:")
        print(f"   Overall growth score: {comprehensive_report.overall_growth_score:.1f}/100")
        print(f"   Growth quality score: {comprehensive_report.growth_quality_score:.1f}/100")
        
        if comprehensive_report.executive_summary:
            print(f"\n   Executive Summary:")
            for summary in comprehensive_report.executive_summary[:2]:
                print(f"     • {summary}")
        
        # Demonstrate Drill-Down Analysis
        print(f"\n🔍 DRILL-DOWN ANALYSIS")
        print("=" * 40)
        
        drill_down_engine = DrillDownEngine(filing_data)
        
        # Revenue breakdown
        revenue_breakdown = drill_down_engine.drill_down_revenue()
        print(f"\n💰 Revenue Breakdown:")
        print(f"   Total Revenue: ${revenue_breakdown.parent_value:,.0f}")
        print(f"   Breakdown items: {len(revenue_breakdown.items)}")
        print(f"   Concentration ratio: {revenue_breakdown.concentration_ratio:.1f}%")
        print(f"   Diversity score: {revenue_breakdown.diversity_score:.1f}/100")
        
        if revenue_breakdown.items:
            print(f"\n   Top revenue sources:")
            for item in revenue_breakdown.items[:5]:
                print(f"     {item.name}: ${item.value:,.0f} ({item.percentage_of_total:.1f}%)")
        
        # Expense breakdown
        expense_breakdown = drill_down_engine.drill_down_expenses()
        print(f"\n💸 Expense Breakdown:")
        print(f"   Total Expenses: ${expense_breakdown.parent_value:,.0f}")
        
        if expense_breakdown.items:
            print(f"\n   Top expense categories:")
            for item in expense_breakdown.items[:5]:
                print(f"     {item.name}: ${item.value:,.0f} ({item.percentage_of_total:.1f}%)")
        
        # Asset breakdown
        asset_breakdown = drill_down_engine.drill_down_assets()
        print(f"\n🏦 Asset Breakdown:")
        print(f"   Total Assets: ${asset_breakdown.parent_value:,.0f}")
        
        if asset_breakdown.items:
            print(f"\n   Top asset categories:")
            for item in asset_breakdown.items[:5]:
                print(f"     {item.name}: ${item.value:,.0f} ({item.percentage_of_total:.1f}%)")
        
        # Demonstrate Efficiency Analysis
        print(f"\n⚡ EFFICIENCY ANALYSIS")
        print("=" * 40)
        
        efficiency_calculator = EfficiencyCalculator(filing_data)
        
        # Conversion rates
        conversion_analysis = efficiency_calculator.calculate_conversion_rates()
        print(f"\n🔄 Business Conversion Funnel:")
        print(f"   Efficiency score: {conversion_analysis.efficiency_score:.1f}/100")
        print(f"   Total conversion rate: {conversion_analysis.total_conversion_rate:.2f}%")
        
        print(f"\n   Conversion stages:")
        for stage_name, value, conversion_rate in conversion_analysis.stages:
            print(f"     {stage_name}: ${value:,.0f} ({conversion_rate:.1f}%)")
        
        if conversion_analysis.bottlenecks:
            print(f"\n   🚨 Bottlenecks identified:")
            for bottleneck in conversion_analysis.bottlenecks[:2]:
                print(f"     • {bottleneck}")
        
        if conversion_analysis.improvement_opportunities:
            print(f"\n   💡 Improvement opportunities:")
            for opportunity in conversion_analysis.improvement_opportunities[:2]:
                print(f"     • {opportunity}")
        
        # Margin analysis
        margin_analysis = efficiency_calculator.calculate_margin_analysis()
        print(f"\n📊 Margin Analysis:")
        
        margins = [
            ("Gross Margin", margin_analysis.gross_margin),
            ("Operating Margin", margin_analysis.operating_margin),
            ("Net Margin", margin_analysis.net_margin),
            ("EBITDA Margin", margin_analysis.ebitda_margin),
            ("Cash Margin", margin_analysis.cash_margin)
        ]
        
        for margin_name, margin in margins:
            if margin:
                performance = f" ({margin.performance_rating})" if margin.performance_rating else ""
                benchmark = f" vs {margin.benchmark_value:.1f}% benchmark" if margin.benchmark_value else ""
                print(f"   {margin_name}: {margin.value:.1f}%{performance}{benchmark}")
        
        # Capital efficiency
        capital_efficiency = efficiency_calculator.calculate_capital_efficiency()
        print(f"\n🏛️ Capital Efficiency:")
        print(f"   Overall score: {capital_efficiency.capital_efficiency_score:.1f}/100")
        
        capital_metrics = [
            ("ROE", capital_efficiency.roe),
            ("ROA", capital_efficiency.roa),
            ("Asset Turnover", capital_efficiency.asset_turnover),
            ("Inventory Turnover", capital_efficiency.inventory_turnover),
            ("Receivables Turnover", capital_efficiency.receivables_turnover)
        ]
        
        for metric_name, metric in capital_metrics:
            if metric:
                performance = f" ({metric.performance_rating})" if metric.performance_rating else ""
                print(f"   {metric_name}: {metric.value:.1f}{metric.unit}{performance}")
        
        # Comprehensive efficiency report
        efficiency_report = efficiency_calculator.get_comprehensive_efficiency_report()
        print(f"\n📋 Efficiency Summary:")
        print(f"   Overall efficiency score: {efficiency_report['summary']['overall_efficiency_score']:.1f}/100")
        
        if efficiency_report['summary']['key_strengths']:
            print(f"\n   💪 Key Strengths:")
            for strength in efficiency_report['summary']['key_strengths']:
                print(f"     • {strength}")
        
        if efficiency_report['summary']['improvement_areas']:
            print(f"\n   🎯 Improvement Areas:")
            for area in efficiency_report['summary']['improvement_areas']:
                print(f"     • {area}")
        
        if efficiency_report['summary']['executive_summary']:
            print(f"\n   📝 Executive Summary:")
            for summary in efficiency_report['summary']['executive_summary']:
                print(f"     • {summary}")
        
        print(f"\n✅ Advanced financial analysis demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in advanced analysis demo: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = demo_advanced_analysis()
    sys.exit(0 if success else 1)