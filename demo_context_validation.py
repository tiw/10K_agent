#!/usr/bin/env python3
"""
Demo: Context Validation for Revenue Data

This script demonstrates how to properly validate and filter XBRL facts
based on their context information to ensure we get the correct Revenue
data for specific periods.
"""

import sys
from pathlib import Path
from datetime import date

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xbrl_financial_service.xbrl_parser import XBRLParser
from xbrl_financial_service.utils.context_validator import ContextValidator, ContextFilter
from xbrl_financial_service.utils.context_mapper import ContextMapper
from xbrl_financial_service.analysis.funnel_analyzer import FunnelAnalyzer
from xbrl_financial_service.models import PeriodType


def demo_context_validation():
    """Demonstrate context validation for revenue data"""
    
    print("🔍 XBRL Context ID Mapping Demo")
    print("=" * 60)
    
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
        context_mapper = ContextMapper(filing_data.all_facts)
        
        # Print context analysis
        print("\n📋 Context ID Analysis:")
        context_mapper.print_context_analysis()
        
        # Get context summary
        print("\n📊 Context Summary:")
        context_summary = ContextValidator.get_context_summary(filing_data.all_facts)
        print(f"   Total Facts: {context_summary['total_facts']}")
        print(f"   Unique Contexts: {context_summary['unique_contexts']}")
        print(f"   Fiscal Years: {context_summary['fiscal_years']}")
        print(f"   Duration Facts: {context_summary['period_types']['duration']}")
        print(f"   Instant Facts: {context_summary['period_types']['instant']}")
        
        # Find revenue contexts
        print("\n💰 Revenue Context Analysis:")
        revenue_contexts = ContextValidator.find_revenue_contexts(filing_data.all_facts)
        
        if revenue_contexts:
            print(f"   Found {len(revenue_contexts)} revenue facts")
            
            for i, rev_context in enumerate(revenue_contexts[:5], 1):  # Show first 5
                print(f"\n   Revenue Fact #{i}:")
                print(f"     Context ID: {rev_context['context_id']}")
                print(f"     Concept: {rev_context['concept']}")
                print(f"     Value: ${rev_context['scaled_value']:,.0f}" if isinstance(rev_context['scaled_value'], (int, float)) else f"     Value: {rev_context['scaled_value']}")
                print(f"     Period Type: {rev_context['period_type']}")
                print(f"     Fiscal Year: {rev_context['fiscal_year']}")
                print(f"     Period: {rev_context['period_start']} to {rev_context['period_end']}")
                
                # Show validation results
                validation = rev_context['validation']
                if validation['warnings']:
                    print(f"     ⚠️  Warnings: {', '.join(validation['warnings'])}")
                else:
                    print(f"     ✅ Context validation passed")
        
        # Demonstrate proper revenue retrieval using Context ID mapping
        print(f"\n🎯 Retrieving Revenue using Context ID Mapping:")
        
        # Get available fiscal years
        summary = context_mapper.get_context_summary()
        fiscal_years = summary['fiscal_years']
        
        for fiscal_year in fiscal_years:
            print(f"\n📅 Fiscal Year {fiscal_year}:")
            
            # Get revenue using context mapper
            revenue_value = context_mapper.get_revenue_for_year(fiscal_year)
            if revenue_value:
                revenue_context = context_mapper.get_revenue_context_for_year(fiscal_year)
                print(f"   💰 Revenue: ${revenue_value:,.0f}")
                print(f"   📋 Context ID: {revenue_context}")
                
                # Show context details
                context_details = summary['context_details'][fiscal_year]
                if 'revenue_context_info' in context_details:
                    rev_info = context_details['revenue_context_info']
                    print(f"   📊 Period: {rev_info['period_start']} to {rev_info['period_end']}")
                    print(f"   🔄 Type: {rev_info['period_type']}")
                    print(f"   📈 Facts in context: {rev_info['fact_count']}")
            else:
                print(f"   ❌ No revenue found for fiscal year {fiscal_year}")
        
        # Demonstrate funnel analysis with correct context
        print(f"\n🔍 Funnel Analysis using Context ID:")
        funnel_analyzer = FunnelAnalyzer(filing_data)
        
        # Get the most recent fiscal year
        if fiscal_years:
            latest_year = max(fiscal_years)
            print(f"\n📊 Profitability Funnel for FY{latest_year}:")
            
            funnel = funnel_analyzer.get_profitability_funnel_by_year(latest_year)
            
            for level in funnel.levels:
                print(f"   {level.name}: ${level.value:,.0f}")
                if level.conversion_rate:
                    print(f"      Conversion Rate: {level.conversion_rate:.1f}%")
                
                # Show children if any
                for child in level.children:
                    print(f"      └─ {child.name}: ${abs(child.value):,.0f}")
            
            print(f"\n   💡 Key Insights:")
            for insight in funnel.key_insights:
                print(f"      • {insight}")
        
        # Show context patterns
        print(f"\n📋 Context ID Patterns (top 10):")
        sorted_contexts = sorted(
            context_summary['context_patterns'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for context_id, count in sorted_contexts[:10]:
            print(f"   {context_id}: {count} facts")
        
        # Demonstrate filtering by specific context pattern
        print(f"\n🔍 Filtering by Context Pattern:")
        
        # Look for contexts that might contain 2024 annual data
        annual_contexts = [ctx for ctx in sorted_contexts if 'c-1' in ctx[0] or 'annual' in ctx[0].lower()]
        
        if annual_contexts:
            target_context = annual_contexts[0][0]
            print(f"   Analyzing context: {target_context}")
            
            context_facts = [f for f in filing_data.all_facts if f.context_id == target_context]
            print(f"   Facts in this context: {len(context_facts)}")
            
            # Find revenue in this specific context
            revenue_in_context = [f for f in context_facts 
                                if any(rev_concept.lower() in f.concept.lower() 
                                      for rev_concept in ['revenue', 'revenues'])]
            
            if revenue_in_context:
                for rev_fact in revenue_in_context:
                    print(f"   📊 Revenue in {target_context}:")
                    print(f"      Concept: {rev_fact.concept}")
                    print(f"      Value: ${rev_fact.get_scaled_value():,.0f}")
                    print(f"      Period: {rev_fact.period}")
        
    except Exception as e:
        print(f"❌ Error during parsing: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    success = demo_context_validation()
    if success:
        print(f"\n✅ Context validation demo completed successfully!")
    else:
        print(f"\n❌ Context validation demo failed!")
        sys.exit(1)