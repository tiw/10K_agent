"""
Command Line Interface for XBRL Financial Service
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict, Optional

from .xbrl_parser import XBRLParser
from .financial_service import FinancialService
from .mcp_server import FinancialMCPServer
from .config import load_config
from .utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def parse_xbrl_command(args):
    """Handle parse-xbrl command"""
    config = load_config()
    parser = XBRLParser(config)
    
    # Build file paths dictionary
    file_paths = {}
    
    if args.schema:
        file_paths['schema'] = args.schema
    if args.calculation:
        file_paths['calculation'] = args.calculation
    if args.definition:
        file_paths['definition'] = args.definition
    if args.label:
        file_paths['label'] = args.label
    if args.presentation:
        file_paths['presentation'] = args.presentation
    if args.instance:
        file_paths['instance'] = args.instance
    elif args.directory:
        # Auto-detect files in directory
        return parse_directory_command(args)
    else:
        print("Error: Either --instance or --directory must be specified")
        return 1
    
    try:
        print("Parsing XBRL filing...")
        filing_data = parser.parse_filing(file_paths)
        
        print(f"\n✅ Successfully parsed XBRL filing!")
        print(f"Company: {filing_data.company_info.name}")
        print(f"CIK: {filing_data.company_info.cik}")
        print(f"Period End: {filing_data.period_end_date}")
        print(f"Total Facts: {len(filing_data.all_facts)}")
        
        # Show financial statements
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
        
        # Calculate ratios if requested
        if args.ratios:
            print(f"\nCalculating financial ratios...")
            service = FinancialService()
            service.load_filing_data(filing_data)
            ratios = service.get_financial_ratios()
            
            print(f"Financial Ratios:")
            ratios_dict = ratios.to_dict()
            for category, category_ratios in ratios_dict.items():
                print(f"  {category.title()}:")
                for ratio_name, value in category_ratios.items():
                    if value is not None:
                        print(f"    {ratio_name}: {value:.4f}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error parsing XBRL filing: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def parse_directory_command(args):
    """Handle directory parsing"""
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory not found: {args.directory}")
        return 1
    
    config = load_config()
    parser = XBRLParser(config)
    
    try:
        print(f"Parsing XBRL files in directory: {args.directory}")
        filing_data = parser.parse_filing_from_directory(str(directory))
        
        print(f"\n✅ Successfully parsed XBRL filing!")
        print(f"Company: {filing_data.company_info.name}")
        print(f"Period End: {filing_data.period_end_date}")
        print(f"Total Facts: {len(filing_data.all_facts)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error parsing directory: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


async def serve_mcp_command(args):
    """Handle serve-mcp command"""
    config = load_config()
    
    # Override port if specified
    if args.port:
        config.mcp_port = args.port
    
    server = FinancialMCPServer(config)
    
    print(f"Starting XBRL Financial MCP Server on port {config.mcp_port}")
    print("Available tools:")
    for tool_name, tool_info in server.tools.items():
        print(f"  - {tool_name}: {tool_info['description']}")
    
    print(f"\nServer ready. Press Ctrl+C to stop.")
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="XBRL Financial Service CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse XBRL files from directory
  xbrl-service parse-xbrl --directory ./apple-10k-files/
  
  # Parse specific XBRL files
  xbrl-service parse-xbrl --instance aapl-20240928_htm.xml --schema aapl-20240928.xsd
  
  # Start MCP server
  xbrl-service serve-mcp --port 8000
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Parse XBRL command
    parse_parser = subparsers.add_parser("parse-xbrl", help="Parse XBRL filing")
    parse_parser.add_argument("--directory", "-d", help="Directory containing XBRL files")
    parse_parser.add_argument("--instance", "-i", help="Path to instance document")
    parse_parser.add_argument("--schema", "-s", help="Path to schema file")
    parse_parser.add_argument("--calculation", "-c", help="Path to calculation linkbase")
    parse_parser.add_argument("--definition", help="Path to definition linkbase")
    parse_parser.add_argument("--label", "-l", help="Path to label linkbase")
    parse_parser.add_argument("--presentation", "-p", help="Path to presentation linkbase")
    parse_parser.add_argument("--ratios", "-r", action="store_true", help="Calculate financial ratios")
    
    # Serve MCP command
    serve_parser = subparsers.add_parser("serve-mcp", help="Start MCP server")
    serve_parser.add_argument("--port", type=int, help="Port to serve on")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "parse-xbrl":
            return parse_xbrl_command(args)
        elif args.command == "serve-mcp":
            return asyncio.run(serve_mcp_command(args))
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())