#!/usr/bin/env python3
"""
Test Unified Context ID Mapping

Verify that all analysis tools use consistent Context ID mapping
for data retrieval across different modules.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xbrl_financial_service.xbrl_parser import XBRLParser
from xbrl_financial_service.analysis.funnel_analyzer import FunnelAnalyzer
from xbrl_financial_service.analysis.trend_analyzer import TrendAnalyzer
from xbrl_financial_service.analysis.drill_down_engine import DrillDownEngine
from xbrl_financial_service.analysis.efficiency_calculator import EfficiencyCalculator
from xbrl_financial_service.analysis.metrics_calculator import MetricsCalculator


def test_unified_context_mapping():
    """Test that all analysis tools use unified Context ID mapping"""
    
    print("🔧 Testing Unified Context ID Mapping")
    print("=" * 50)
    
    # Check if files exist
    required_files = [
        'aapl-20240928_htm.xml',
        'aapl-20240928.xsd',
        'aapl-20240928_cal.xml',
        'aapl-20240928_def.xml',
        'aapl-20240928_lab.xml',
        'aapl-20240928_pre.xml'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    try:
        # Parse XBRL files
        parser = XBRLParser()
        xbrl_files = {
            'instance': 'aapl-20240928_htm.xml',
            'schema': 'aapl-20240928.xsd',
            'calculation': 'aapl-20240928_cal.xml',
            'definition': 'aapl-20240928_def.xml',
            'label': 'aapl-20240928_lab.xml',
            'presentation': 'aapl-20240928_pre.xml'
        }
        
        print("📁 Parsing XBRL files...")
        filing_data = parser.parse_filing(xbrl_files)
        print(f"✅ Parsed {len(filing_data.all_facts)} facts")
        
        # Test fiscal year
        test_year = 2024
        
        # Initialize all analyzers
        print(f"\n🔍 Initializing analyzers for FY{test_year}...")
        funnel_analyzer = FunnelAnalyzer(filing_data)
        trend_analyzer = TrendAnalyzer(filing_data)
        drill_down_engine = DrillDownEngine(filing_data)
        efficiency_calculator = EfficiencyCalculator(filing_data)
        metrics_calculator = MetricsCalculator(filing_data)
        
        print("✅ All analyzers initialized successfully")
        
        # Test 1: Revenue consistency across all tools
        print(f"\n💰 Testing Revenue Consistency for FY{test_year}:")
        
        # Get revenue from different analyzers
        revenue_funnel = funnel_analyzer.get_value_for_fiscal_year_by_context('RevenueFromContractWithCustomerExcludingAssessedTax', test_year)
        revenue_drill_down = drill_down_engine.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', test_year)
        revenue_efficiency = efficiency_calculator.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', test_year)
        revenue_metrics = metrics_calculator.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', test_year)
        
        revenues = {
            'FunnelAnalyzer': revenue_funnel,
            'DrillDownEngine': revenue_drill_down,
            'EfficiencyCalculator': revenue_efficiency,
            'MetricsCalculator': revenue_metrics
        }
        
        print(f"   Revenue values from different analyzers:")
        for analyzer, revenue in revenues.items():
            if revenue:
                print(f"      {analyzer}: ${revenue:,.0f}")
            else:
                print(f"      {analyzer}: Not found")
        
        # Check consistency
        non_null_revenues = [r for r in revenues.values() if r is not None]
        if len(set(non_null_revenues)) <= 1:
            print(f"   ✅ Revenue values are consistent across all analyzers")
        else:
            print(f"   ❌ Revenue values are inconsistent!")
            return False
        
        # Test 2: Context ID usage verification
        print(f"\n📋 Testing Context ID Usage:")
        
        # Check that all analyzers have context_mapper
        analyzers_with_context = []
        for name, analyzer in [
            ('FunnelAnalyzer', funnel_analyzer),
            ('TrendAnalyzer', trend_analyzer),
            ('DrillDownEngine', drill_down_engine),
            ('EfficiencyCalculator', efficiency_calculator),
            ('MetricsCalculator', metrics_calculator)
        ]:
            if hasattr(analyzer, 'context_mapper'):
                analyzers_with_context.append(name)
                print(f"   ✅ {name} has context_mapper")
            else:
                print(f"   ❌ {name} missing context_mapper")
        
        if len(analyzers_with_context) == 5:
            print(f"   ✅ All analyzers have Context ID mapping capability")
        else:
            print(f"   ❌ Some analyzers missing Context ID mapping")
            return False
        
        # Test 3: Fiscal year-specific methods
        print(f"\n📅 Testing Fiscal Year-Specific Methods:")
        
        # Test FunnelAnalyzer
        try:
            funnel_2024 = funnel_analyzer.get_profitability_funnel_by_year(test_year)
            print(f"   ✅ FunnelAnalyzer.get_profitability_funnel_by_year({test_year}) works")
            print(f"      Revenue: ${funnel_2024.levels[0].value:,.0f}" if funnel_2024.levels else "      No levels found")
        except Exception as e:
            print(f"   ❌ FunnelAnalyzer fiscal year method failed: {e}")
        
        # Test DrillDownEngine
        try:
            revenue_breakdown = drill_down_engine.drill_down_revenue_by_year(test_year)
            print(f"   ✅ DrillDownEngine.drill_down_revenue_by_year({test_year}) works")
            print(f"      Total Revenue: ${revenue_breakdown.parent_value:,.0f}")
        except Exception as e:
            print(f"   ❌ DrillDownEngine fiscal year method failed: {e}")
        
        # Test EfficiencyCalculator
        try:
            conversion_analysis = efficiency_calculator.calculate_conversion_rates_by_year(test_year)
            print(f"   ✅ EfficiencyCalculator.calculate_conversion_rates_by_year({test_year}) works")
            print(f"      Efficiency Score: {conversion_analysis.efficiency_score:.1f}/100")
        except Exception as e:
            print(f"   ❌ EfficiencyCalculator fiscal year method failed: {e}")
        
        # Test MetricsCalculator
        try:
            metrics_summary = metrics_calculator.get_metrics_summary_by_year(test_year)
            print(f"   ✅ MetricsCalculator.get_metrics_summary_by_year({test_year}) works")
            print(f"      Total Metrics: {metrics_summary['data_quality']['total_metrics']}")
        except Exception as e:
            print(f"   ❌ MetricsCalculator fiscal year method failed: {e}")
        
        # Test 4: Cross-analyzer data consistency
        print(f"\n🔄 Testing Cross-Analyzer Data Consistency:")
        
        # Test Operating Income consistency
        operating_income_values = {}
        
        try:
            operating_income_values['Funnel'] = funnel_analyzer.get_value_for_fiscal_year_by_context('OperatingIncomeLoss', test_year)
        except:
            pass
        
        try:
            operating_income_values['Efficiency'] = efficiency_calculator.get_value_for_fiscal_year('OperatingIncomeLoss', test_year)
        except:
            pass
        
        try:
            operating_income_values['Metrics'] = metrics_calculator.get_value_for_fiscal_year('OperatingIncomeLoss', test_year)
        except:
            pass
        
        print(f"   Operating Income values:")
        for analyzer, value in operating_income_values.items():
            if value:
                print(f"      {analyzer}: ${value:,.0f}")
            else:
                print(f"      {analyzer}: Not found")
        
        # Check consistency
        non_null_operating = [v for v in operating_income_values.values() if v is not None]
        if len(set(non_null_operating)) <= 1:
            print(f"   ✅ Operating Income values are consistent")
        else:
            print(f"   ❌ Operating Income values are inconsistent!")
        
        # Test 5: Context ID verification
        print(f"\n🆔 Verifying Context ID Usage:")
        
        # Get context mapping from one analyzer
        context_summary = funnel_analyzer.context_mapper.get_context_summary()
        
        if test_year in context_summary['fiscal_years']:
            revenue_context = context_summary['context_details'][test_year]['revenue_context']
            bs_context = context_summary['context_details'][test_year]['balance_sheet_context']
            
            print(f"   FY{test_year} Revenue Context: {revenue_context}")
            print(f"   FY{test_year} Balance Sheet Context: {bs_context}")
            
            # Verify all analyzers use the same context mapping
            context_mappers = [
                funnel_analyzer.context_mapper,
                trend_analyzer.context_mapper,
                drill_down_engine.context_mapper,
                efficiency_calculator.context_mapper,
                metrics_calculator.context_mapper
            ]
            
            consistent_contexts = True
            for mapper in context_mappers[1:]:
                mapper_summary = mapper.get_context_summary()
                if (mapper_summary['context_details'][test_year]['revenue_context'] != revenue_context or
                    mapper_summary['context_details'][test_year]['balance_sheet_context'] != bs_context):
                    consistent_contexts = False
                    break
            
            if consistent_contexts:
                print(f"   ✅ All analyzers use consistent Context ID mapping")
            else:
                print(f"   ❌ Context ID mapping inconsistent across analyzers")
                return False
        
        print(f"\n✅ All unified Context ID mapping tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_unified_context_mapping()
    if success:
        print(f"\n🎉 Unified Context ID mapping verification successful!")
    else:
        print(f"\n💥 Unified Context ID mapping verification failed!")
        sys.exit(1)