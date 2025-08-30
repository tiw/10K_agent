#!/usr/bin/env python3
"""
XBRL Financial Service Demo

This script demonstrates how to use the XBRL Financial Service to parse
Apple's 10-K filing and extract financial information.
"""

import sys
import json
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from xbrl_financial_service import XBRLParser, FinancialService, Config
from xbrl_financial_service.utils.logging import setup_logging
from xbrl_financial_service.mcp_server import FinancialMCPServer


def demo_xbrl_parsing():
    """Demonstrate XBRL parsing capabilities"""
    print("🔍 XBRL Financial Service Demo")
    print("=" * 50)
    
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
            print(f"✅ Found {file_type}: {file_path}")
        else:
            missing_files.append(f"{file_type}: {file_path}")
            print(f"❌ Missing {file_type}: {file_path}")
    
    if missing_files:
        print(f"\n⚠️  Missing files:")
        for missing in missing_files:
            print(f"   - {missing}")
        print(f"\nThis demo requires Apple's XBRL files to be in the current directory.")
        print(f"You can download them from SEC EDGAR database.")
        return False
    
    try:
        print(f"\n🚀 Starting XBRL parsing...")
        
        # Parse the filing
        filing_data = parser.parse_filing(available_files)
        
        print(f"\n✅ Successfully parsed Apple's XBRL filing!")
        print(f"   Company: {filing_data.company_info.name}")
        print(f"   CIK: {filing_data.company_info.cik}")
        print(f"   Period End: {filing_data.period_end_date}")
        print(f"   Total Facts: {len(filing_data.all_facts)}")
        print(f"   Taxonomy Elements: {len(filing_data.taxonomy_elements)}")
        
        # Demonstrate financial service
        print(f"\n📊 Creating Financial Service...")
        service = FinancialService(filing_data, config)
        
        # Get company information
        company_info = service.get_company_info()
        if company_info:
            print(f"\n🏢 Company Information:")
            print(f"   Name: {company_info.name}")
            print(f"   CIK: {company_info.cik}")
            print(f"   Ticker: {company_info.ticker or 'N/A'}")
        
        # Show financial statements
        print(f"\n📈 Financial Statements:")
        statements = [
            ("Income Statement", service.get_income_statement()),
            ("Balance Sheet", service.get_balance_sheet()),
            ("Cash Flow", service.get_cash_flow_statement())
        ]
        
        for name, statement in statements:
            if statement:
                print(f"   ✅ {name}: {len(statement.facts)} facts")
            else:
                print(f"   ❌ {name}: Not available")
        
        # Calculate financial ratios
        print(f"\n💰 Financial Ratios:")
        try:
            ratios = service.get_financial_ratios()
            ratios_dict = ratios.to_dict()
            
            for category, category_ratios in ratios_dict.items():
                if any(v is not None for v in category_ratios.values()):
                    print(f"   {category.title()}:")
                    for ratio_name, value in category_ratios.items():
                        if value is not None:
                            print(f"     {ratio_name.replace('_', ' ').title()}: {value:.4f}")
        except Exception as e:
            print(f"   ⚠️  Could not calculate ratios: {str(e)}")
        
        # Search for specific facts
        print(f"\n🔍 Sample Fact Search (Revenue):")
        revenue_facts = service.search_facts("revenue", limit=5)
        for i, fact in enumerate(revenue_facts[:3], 1):
            print(f"   {i}. {fact.label}: {fact.value} {fact.unit or ''}")
        
        # Show summary
        print(f"\n📋 Data Summary:")
        summary = service.get_summary_data()
        print(f"   Total Facts: {summary.get('total_facts', 0)}")
        print(f"   Form Type: {summary.get('form_type', 'N/A')}")
        
        statements_available = summary.get('statements_available', {})
        available_count = sum(1 for available in statements_available.values() if available)
        print(f"   Statements Available: {available_count}/5")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during parsing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def demo_mcp_server():
    """Demonstrate MCP server capabilities"""
    print(f"\n🌐 MCP Server Demo")
    print("=" * 30)
    
    config = Config()
    server = FinancialMCPServer(config)
    
    print(f"MCP Server Tools Available:")
    for tool_name, tool_info in server.tools.items():
        print(f"   📋 {tool_name}")
        print(f"      {tool_info['description']}")
    
    print(f"\n💡 To start the MCP server, run:")
    print(f"   python -m xbrl_financial_service.mcp_server")
    print(f"   or")
    print(f"   xbrl-service serve-mcp")


def demo_cli_usage():
    """Show CLI usage examples"""
    print(f"\n⚡ CLI Usage Examples")
    print("=" * 30)
    
    examples = [
        ("Parse XBRL files from directory", "xbrl-service parse-xbrl --directory ./apple-files/"),
        ("Parse specific files", "xbrl-service parse-xbrl --instance data.xml --schema schema.xsd"),
        ("Parse with ratios", "xbrl-service parse-xbrl --directory ./files/ --ratios"),
        ("Start MCP server", "xbrl-service serve-mcp --port 8000"),
        ("Verbose parsing", "xbrl-service parse-xbrl --directory ./files/ --verbose")
    ]
    
    for description, command in examples:
        print(f"   📝 {description}:")
        print(f"      {command}")
        print()


def main():
    """Main demo function"""
    print("🎯 XBRL Financial Service - Complete Demo")
    print("=" * 60)
    
    # Run parsing demo
    parsing_success = demo_xbrl_parsing()
    
    # Show MCP server capabilities
    demo_mcp_server()
    
    # Show CLI usage
    demo_cli_usage()
    
    print(f"\n🎉 Demo completed!")
    
    if not parsing_success:
        print(f"\n📥 To run the full demo:")
        print(f"   1. Download Apple's XBRL files from SEC EDGAR")
        print(f"   2. Place them in the current directory")
        print(f"   3. Run this demo again")
        print(f"\n🔗 SEC EDGAR: https://www.sec.gov/edgar/searchedgar/companysearch.html")
        print(f"   Search for 'Apple Inc' and download the latest 10-K XBRL files")
    
    print(f"\n📚 For more information, see README.md")


if __name__ == "__main__":
    main()