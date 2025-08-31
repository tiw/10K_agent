#!/usr/bin/env python3
"""
Demo: Context ID Mapping for Revenue Data

This script demonstrates how to use Context ID mapping to correctly
identify and retrieve Revenue data from specific XBRL contexts.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xbrl_financial_service.xbrl_parser import XBRLParser
from xbrl_financial_service.utils.context_mapper import ContextMapper
from xbrl_financial_service.analysis.funnel_analyzer import FunnelAnalyzer


def demo_context_id_mapping():
    """Demonstrate Context ID mapping for accurate revenue retrieval"""
    
    print("🆔 XBRL Context ID Mapping Demo")
    print("=" * 50)
    
    # Initialize parser
    parser = XBRLParser()
    
    # Parse Apple XBRL files (files are in current directory)
    xbrl_files = {
        'instance': 'aapl-20240928_htm.xml',
        'schema': 'aapl-20240928.xsd',
        'calculation': 'aapl-20240928_cal.xml',
        'definition': 'aapl-20240928_def.xml',
        'label': 'aapl-20240928_lab.xml',
        'presentation': 'aapl-20240928_pre.xml'
    }
    
    try:
        print("📁 Parsing XBRL files...")
        filing_data = parser.parse_filing(xbrl_files)
        print(f"✅ Successfully parsed {len(filing_data.all_facts)} facts")
        
        # Initialize context mapper
        print("\n🔍 Analyzing Context IDs...")
        context_mapper = ContextMapper(filing_data.all_facts)
        
        # Print detailed context analysis
        context_mapper.print_context_analysis()
        
        # Show specific context examples
        print(f"\n📋 Context ID Examples:")
        summary = context_mapper.get_context_summary()
        
        for fiscal_year in summary['fiscal_years']:
            year_info = summary['context_details'][fiscal_year]
            
            print(f"\n📅 Fiscal Year {fiscal_year}:")
            
            if year_info['revenue_context']:
                print(f"   💰 Revenue Context: {year_info['revenue_context']}")
                rev_info = year_info['revenue_context_info']
                print(f"      📊 Period: {rev_info['period_start']} to {rev_info['period_end']}")
                print(f"      🔄 Type: {rev_info['period_type']}")
                print(f"      📈 Facts: {rev_info['fact_count']}")
                
                # Get actual revenue value
                revenue = context_mapper.get_revenue_for_year(fiscal_year)
                if revenue:
                    print(f"      💵 Revenue: ${revenue:,.0f}")
            
            if year_info['balance_sheet_context']:
                print(f"   📊 Balance Sheet Context: {year_info['balance_sheet_context']}")
                bs_info = year_info['balance_sheet_context_info']
                print(f"      📅 Date: {bs_info['period_end']}")
                print(f"      🔄 Type: {bs_info['period_type']}")
                print(f"      📈 Facts: {bs_info['fact_count']}")
        
        # Demonstrate specific context usage
        print(f"\n🎯 Demonstrating Context-Specific Data Retrieval:")
        
        # Get the latest fiscal year
        latest_year = max(summary['fiscal_years']) if summary['fiscal_years'] else None
        
        if latest_year:
            print(f"\n📊 Analyzing FY{latest_year} using Context IDs:")
            
            # Get revenue context
            revenue_context = context_mapper.get_revenue_context_for_year(latest_year)
            print(f"   Revenue Context: {revenue_context}")
            
            # Get balance sheet context  
            bs_context = context_mapper.get_balance_sheet_context_for_year(latest_year)
            print(f"   Balance Sheet Context: {bs_context}")
            
            # Compare different approaches
            print(f"\n🔍 Comparing Data Retrieval Methods:")
            
            # Method 1: Using context mapper (recommended)
            revenue_context_method = context_mapper.get_revenue_for_year(latest_year)
            print(f"   Context Mapper Revenue: ${revenue_context_method:,.0f}" if revenue_context_method else "   Context Mapper Revenue: Not found")
            
            # Method 2: Direct context ID lookup
            if revenue_context:
                funnel_analyzer = FunnelAnalyzer(filing_data)
                revenue_direct = funnel_analyzer.get_value_by_context_id(
                    'RevenueFromContractWithCustomerExcludingAssessedTax', 
                    revenue_context
                )
                print(f"   Direct Context Lookup: ${revenue_direct:,.0f}" if revenue_direct else "   Direct Context Lookup: Not found")
            
            # Show facts in revenue context
            if revenue_context:
                print(f"\n📋 Facts in Revenue Context {revenue_context}:")
                context_facts = context_mapper.get_facts_by_context_id(revenue_context)
                
                # Show revenue-related facts
                revenue_facts = [f for f in context_facts 
                               if any(term in f.concept.lower() for term in ['revenue', 'sales', 'income'])]
                
                for fact in revenue_facts[:5]:  # Show first 5
                    scaled_value = fact.get_scaled_value()
                    if isinstance(scaled_value, (int, float)):
                        print(f"      {fact.concept}: ${scaled_value:,.0f}")
                    else:
                        print(f"      {fact.concept}: {scaled_value}")
        
        # Demonstrate funnel analysis with context awareness
        print(f"\n🔄 Context-Aware Funnel Analysis:")
        
        if latest_year:
            funnel_analyzer = FunnelAnalyzer(filing_data)
            funnel = funnel_analyzer.get_profitability_funnel_by_year(latest_year)
            
            print(f"\n📊 Profitability Funnel for FY{latest_year}:")
            for level in funnel.levels:
                print(f"   {level.name}")
                print(f"      Value: ${level.value:,.0f}")
                if level.conversion_rate:
                    print(f"      Margin: {level.conversion_rate:.1f}%")
            
            print(f"\n💡 Insights:")
            for insight in funnel.key_insights:
                print(f"   • {insight}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = demo_context_id_mapping()
    if success:
        print(f"\n✅ Context ID mapping demo completed successfully!")
    else:
        print(f"\n❌ Context ID mapping demo failed!")
        sys.exit(1)