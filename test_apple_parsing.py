#!/usr/bin/env python3
"""
Test script to verify XBRL parsing with Apple's 10-K files
"""

import sys
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from xbrl_financial_service import XBRLParser, Config
from xbrl_financial_service.utils.logging import setup_logging

def test_apple_parsing():
    """Test parsing Apple's XBRL files"""
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Create parser with config
    config = Config()
    config.enable_parallel_processing = False  # Disable for testing
    parser = XBRLParser(config)
    
    # Define file paths (assuming files are in current directory)
    file_paths = {
        'schema': 'aapl-20240928.xsd',
        'calculation': 'aapl-20240928_cal.xml',
        'definition': 'aapl-20240928_def.xml',
        'instance': 'aapl-20240928_htm.xml'  # This would be the actual instance file
    }
    
    # Check if files exist
    missing_files = []
    for file_type, file_path in file_paths.items():
        if not Path(file_path).exists():
            missing_files.append(f"{file_type}: {file_path}")
    
    if missing_files:
        print("Missing files:")
        for missing in missing_files:
            print(f"  - {missing}")
        print("\nNote: This test requires Apple's XBRL files to be in the current directory.")
        print("The actual instance document file name may be different.")
        return
    
    try:
        print("Starting XBRL parsing test...")
        
        # Parse the filing
        filing_data = parser.parse_filing(file_paths)
        
        print(f"\n✅ Successfully parsed Apple's XBRL filing!")
        print(f"Company: {filing_data.company_info.name}")
        print(f"CIK: {filing_data.company_info.cik}")
        print(f"Period End: {filing_data.period_end_date}")
        print(f"Total Facts: {len(filing_data.all_facts)}")
        print(f"Taxonomy Elements: {len(filing_data.taxonomy_elements)}")
        
        # Show some sample facts
        print(f"\nSample Facts:")
        for i, fact in enumerate(filing_data.all_facts[:5]):
            print(f"  {i+1}. {fact.concept}: {fact.value} {fact.unit or ''}")
        
        # Check financial statements
        statements = [
            ("Income Statement", filing_data.income_statement),
            ("Balance Sheet", filing_data.balance_sheet),
            ("Cash Flow", filing_data.cash_flow_statement)
        ]
        
        print(f"\nFinancial Statements:")
        for name, statement in statements:
            if statement:
                print(f"  ✅ {name}: {len(statement.facts)} facts")
            else:
                print(f"  ❌ {name}: Not found")
        
        print(f"\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_apple_parsing()