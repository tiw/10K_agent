#!/usr/bin/env python3
"""
Test script for advanced financial analysis engine components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xbrl_financial_service.financial_service import FinancialService
from xbrl_financial_service.analysis import (
    FunnelAnalyzer, TrendAnalyzer, DrillDownEngine, EfficiencyCalculator
)

def test_advanced_analysis():
    """Test all advanced analysis components"""
    print("🔍 Testing Advanced Financial Analysis Engine")
    print("=" * 60)
    
    try:
        # Import required modules
        from xbrl_financial_service import XBRLParser, Config
        
        # Load Apple XBRL files
        apple_files = {
            'schema': 'aapl-20240928.xsd',
            'calculation': 'aapl-20240928_cal.xml',
            'definition': 'aapl-20240928_def.xml',
            'label': 'aapl-20240928_lab.xml',
            'presentation': 'aapl-20240928_pre.xml',
            'instance': 'aapl-20240928_htm.xml'
        }
        
        print("📊 Loading Apple XBRL data...")
        
        # Create parser and config
        config = Config()
        parser = XBRLParser(config)
        
        # Parse the filing
        filing_data = parser.parse_filing(apple_files)
        print(f"✅ Loaded {len(filing_data.all_facts)} financial facts")
        
        # Initialize financial service with parsed data
        service = FinancialService(filing_data, config)
        
        # Test FunnelAnalyzer
        print("\n🔄 Testing FunnelAnalyzer...")
        funnel_analyzer = FunnelAnalyzer(filing_data)
        
        profitability_funnel = funnel_analyzer.get_profitability_funnel()
        print(f"   Profitability funnel: {len(profitability_funnel.levels)} levels")
        print(f"   Total conversion rate: {profitability_funnel.total_conversion_rate:.2f}%")
        
        cash_funnel = funnel_analyzer.get_cash_conversion_funnel()
        print(f"   Cash conversion funnel: {len(cash_funnel.levels)} levels")
        print(f"   Total conversion rate: {cash_funnel.total_conversion_rate:.2f}%")
        
        capital_funnel = funnel_analyzer.get_capital_efficiency_funnel()
        print(f"   Capital efficiency funnel: {len(capital_funnel.levels)} levels")
        print(f"   Total conversion rate: {capital_funnel.total_conversion_rate:.2f}%")
        
        # Test TrendAnalyzer
        print("\n📈 Testing TrendAnalyzer...")
        trend_analyzer = TrendAnalyzer(filing_data)
        
        revenue_trend = trend_analyzer.analyze_revenue_trend()
        if revenue_trend:
            print(f"   Revenue trend: {len(revenue_trend.data_points)} periods")
            print(f"   CAGR: {revenue_trend.cagr:.2f}%" if revenue_trend.cagr else "   CAGR: N/A")
            print(f"   Trend direction: {revenue_trend.trend_direction}")
        
        comprehensive_report = trend_analyzer.generate_comprehensive_report()
        print(f"   Growth score: {comprehensive_report.overall_growth_score:.1f}")
        print(f"   Quality score: {comprehensive_report.growth_quality_score:.1f}")
        
        # Test DrillDownEngine
        print("\n🔍 Testing DrillDownEngine...")
        drill_down_engine = DrillDownEngine(filing_data)
        
        revenue_breakdown = drill_down_engine.drill_down_revenue()
        print(f"   Revenue breakdown: {len(revenue_breakdown.items)} items")
        print(f"   Concentration ratio: {revenue_breakdown.concentration_ratio:.1f}%")
        print(f"   Diversity score: {revenue_breakdown.diversity_score:.1f}")
        
        expense_breakdown = drill_down_engine.drill_down_expenses()
        print(f"   Expense breakdown: {len(expense_breakdown.items)} items")
        
        asset_breakdown = drill_down_engine.drill_down_assets()
        print(f"   Asset breakdown: {len(asset_breakdown.items)} items")
        
        # Test EfficiencyCalculator
        print("\n⚡ Testing EfficiencyCalculator...")
        efficiency_calculator = EfficiencyCalculator(filing_data)
        
        conversion_analysis = efficiency_calculator.calculate_conversion_rates()
        print(f"   Conversion stages: {len(conversion_analysis.stages)}")
        print(f"   Total conversion rate: {conversion_analysis.total_conversion_rate:.2f}%")
        print(f"   Efficiency score: {conversion_analysis.efficiency_score:.1f}")
        
        margin_analysis = efficiency_calculator.calculate_margin_analysis()
        if margin_analysis.gross_margin:
            print(f"   Gross margin: {margin_analysis.gross_margin.value:.1f}%")
        if margin_analysis.operating_margin:
            print(f"   Operating margin: {margin_analysis.operating_margin.value:.1f}%")
        if margin_analysis.net_margin:
            print(f"   Net margin: {margin_analysis.net_margin.value:.1f}%")
        
        capital_efficiency = efficiency_calculator.calculate_capital_efficiency()
        if capital_efficiency.roe:
            print(f"   ROE: {capital_efficiency.roe.value:.1f}%")
        if capital_efficiency.roa:
            print(f"   ROA: {capital_efficiency.roa.value:.1f}%")
        print(f"   Capital efficiency score: {capital_efficiency.capital_efficiency_score:.1f}")
        
        # Test comprehensive efficiency report
        print("\n📋 Testing Comprehensive Efficiency Report...")
        efficiency_report = efficiency_calculator.get_comprehensive_efficiency_report()
        print(f"   Overall efficiency score: {efficiency_report['summary']['overall_efficiency_score']:.1f}")
        print(f"   Key strengths: {len(efficiency_report['summary']['key_strengths'])}")
        print(f"   Improvement areas: {len(efficiency_report['summary']['improvement_areas'])}")
        
        # Display some insights
        print("\n💡 Sample Insights:")
        if profitability_funnel.key_insights:
            print(f"   Profitability: {profitability_funnel.key_insights[0]}")
        
        if revenue_breakdown.key_insights:
            print(f"   Revenue breakdown: {revenue_breakdown.key_insights[0]}")
        
        if conversion_analysis.bottlenecks:
            print(f"   Conversion bottleneck: {conversion_analysis.bottlenecks[0]}")
        
        if efficiency_report['summary']['executive_summary']:
            print(f"   Executive summary: {efficiency_report['summary']['executive_summary'][0]}")
        
        print("\n✅ All advanced analysis components tested successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing advanced analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_advanced_analysis()
    sys.exit(0 if success else 1)