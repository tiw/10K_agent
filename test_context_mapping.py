#!/usr/bin/env python3
"""
Test Context ID Mapping

Simple test script to verify Context ID mapping functionality
with Apple 2024 XBRL data.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xbrl_financial_service.xbrl_parser import XBRLParser
from xbrl_financial_service.utils.context_mapper import ContextMapper


def test_context_mapping():
    """Test Context ID mapping with Apple 2024 data"""
    
    print("🧪 Testing Context ID Mapping")
    print("=" * 40)
    
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
        print("Please ensure Apple XBRL files are in the current directory.")
        return False
    
    try:
        # Initialize parser
        parser = XBRLParser()
        
        # Parse all available XBRL files
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
        
        # Initialize context mapper
        print("\n🔍 Analyzing contexts...")
        context_mapper = ContextMapper(filing_data.all_facts)
        
        # Get summary
        summary = context_mapper.get_context_summary()
        
        print(f"\n📊 Context Summary:")
        print(f"   Total contexts: {summary['total_contexts']}")
        print(f"   Fiscal years: {summary['fiscal_years']}")
        
        # Show context mapping for each fiscal year
        for fiscal_year in summary['fiscal_years']:
            print(f"\n📅 Fiscal Year {fiscal_year}:")
            
            year_info = summary['context_details'][fiscal_year]
            
            # Revenue context
            if year_info['revenue_context']:
                print(f"   💰 Revenue Context: {year_info['revenue_context']}")
                rev_info = year_info['revenue_context_info']
                print(f"      Period: {rev_info['period_start']} to {rev_info['period_end']}")
                print(f"      Type: {rev_info['period_type']}")
                print(f"      Facts: {rev_info['fact_count']}")
                
                # Test revenue retrieval
                revenue = context_mapper.get_revenue_for_year(fiscal_year)
                if revenue:
                    print(f"      💵 Revenue: ${revenue:,.0f}")
                else:
                    print(f"      ❌ Revenue not found")
            
            # Balance sheet context
            if year_info['balance_sheet_context']:
                print(f"   📊 Balance Sheet Context: {year_info['balance_sheet_context']}")
                bs_info = year_info['balance_sheet_context_info']
                print(f"      Date: {bs_info['period_end']}")
                print(f"      Type: {bs_info['period_type']}")
                print(f"      Facts: {bs_info['fact_count']}")
        
        # Test specific context lookups
        print(f"\n🎯 Testing Specific Context Lookups:")
        
        # Look for 2024 data specifically
        if 2024 in summary['fiscal_years']:
            print(f"\n📋 FY2024 Context Details:")
            
            revenue_context_2024 = context_mapper.get_revenue_context_for_year(2024)
            bs_context_2024 = context_mapper.get_balance_sheet_context_for_year(2024)
            
            print(f"   Revenue Context ID: {revenue_context_2024}")
            print(f"   Balance Sheet Context ID: {bs_context_2024}")
            
            # Test revenue retrieval
            revenue_2024 = context_mapper.get_revenue_for_year(2024)
            if revenue_2024:
                print(f"   ✅ FY2024 Revenue: ${revenue_2024:,.0f}")
            else:
                print(f"   ❌ FY2024 Revenue not found")
            
            # Test other concepts
            test_concepts = [
                ('CostOfGoodsAndServicesSold', 'Cost of Sales'),
                ('OperatingIncomeLoss', 'Operating Income'),
                ('NetIncomeLoss', 'Net Income')
            ]
            
            print(f"\n   Other FY2024 Metrics:")
            for concept, label in test_concepts:
                value = context_mapper.get_concept_value_for_year(concept, 2024, prefer_duration=True)
                if value:
                    print(f"      {label}: ${value:,.0f}")
                else:
                    print(f"      {label}: Not found")
        
        # Show some context facts
        print(f"\n🔍 Sample Context Facts:")
        
        # Get facts from the first revenue context
        if summary['fiscal_years']:
            first_year = summary['fiscal_years'][0]
            revenue_context = context_mapper.get_revenue_context_for_year(first_year)
            
            if revenue_context:
                context_facts = context_mapper.get_facts_by_context_id(revenue_context)
                print(f"\n   Facts in context {revenue_context} (showing first 10):")
                
                for i, fact in enumerate(context_facts[:10], 1):
                    scaled_value = fact.get_scaled_value()
                    if isinstance(scaled_value, (int, float)):
                        print(f"      {i}. {fact.concept}: ${scaled_value:,.0f}")
                    else:
                        print(f"      {i}. {fact.concept}: {scaled_value}")
        
        print(f"\n✅ Context mapping test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_context_mapping()
    if success:
        print(f"\n🎉 All tests passed!")
    else:
        print(f"\n💥 Tests failed!")
        sys.exit(1)