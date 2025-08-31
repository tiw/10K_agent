#!/usr/bin/env python3
"""
Test script for enhanced MCP financial data tools
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append('.')

from xbrl_financial_service.mcp_server import FinancialMCPServer


async def test_enhanced_mcp_tools():
    """Test the enhanced MCP financial data tools"""
    
    print("Testing Enhanced MCP Financial Data Tools")
    print("=" * 50)
    
    # Create server
    server = FinancialMCPServer()
    
    # Test 1: List available tools
    print("\n1. Available Tools:")
    tools_response = await server.handle_list_tools()
    for tool in tools_response['tools']:
        print(f"   - {tool['name']}: {tool['description']}")
    
    # Test 2: Load XBRL filing data
    print("\n2. Loading Apple XBRL Filing Data...")
    file_paths = {
        "schema": "aapl-20240928.xsd",
        "calculation": "aapl-20240928_cal.xml", 
        "definition": "aapl-20240928_def.xml",
        "label": "aapl-20240928_lab.xml",
        "presentation": "aapl-20240928_pre.xml",
        "instance": "aapl-20240928_htm.xml"
    }
    
    # Check if files exist
    missing_files = []
    for file_type, file_path in file_paths.items():
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   Missing files: {missing_files}")
        print("   Skipping data loading tests...")
        return
    
    try:
        load_response = await server.handle_call_tool("load_xbrl_filing", {"file_paths": file_paths})
        if load_response.get("isError"):
            print(f"   Error loading data: {load_response['content'][0]['text']}")
            return
        else:
            print(f"   Success: {load_response['content'][0]['text']}")
    except Exception as e:
        print(f"   Error loading data: {str(e)}")
        return
    
    # Test 3: Enhanced Income Statement
    print("\n3. Testing Enhanced Income Statement Tool...")
    try:
        income_response = await server.handle_call_tool("get_income_statement", {})
        if not income_response.get("isError"):
            print("   ✓ Income statement retrieved successfully")
            print(f"   Summary: {income_response['content'][0]['text'].split('Key Metrics:')[0].strip()}")
        else:
            print(f"   Error: {income_response['content'][0]['text']}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # Test 4: Enhanced Balance Sheet
    print("\n4. Testing Enhanced Balance Sheet Tool...")
    try:
        balance_response = await server.handle_call_tool("get_balance_sheet", {})
        if not balance_response.get("isError"):
            print("   ✓ Balance sheet retrieved successfully")
            print(f"   Summary: {balance_response['content'][0]['text'].split('Key Metrics:')[0].strip()}")
        else:
            print(f"   Error: {balance_response['content'][0]['text']}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # Test 5: Enhanced Cash Flow with Section Breakdown
    print("\n5. Testing Enhanced Cash Flow Tool...")
    try:
        # Test all sections
        cash_flow_response = await server.handle_call_tool("get_cash_flow", {})
        if not cash_flow_response.get("isError"):
            print("   ✓ Cash flow statement retrieved successfully")
            print(f"   Summary: {cash_flow_response['content'][0]['text'].split('Section Breakdown:')[0].strip()}")
        else:
            print(f"   Error: {cash_flow_response['content'][0]['text']}")
        
        # Test specific section
        operating_response = await server.handle_call_tool("get_cash_flow", {"section": "operating"})
        if not operating_response.get("isError"):
            print("   ✓ Operating activities section retrieved successfully")
        else:
            print(f"   Error getting operating section: {operating_response['content'][0]['text']}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # Test 6: Enhanced Financial Ratios with Selection
    print("\n6. Testing Enhanced Financial Ratios Tool...")
    try:
        # Test all ratios
        ratios_response = await server.handle_call_tool("calculate_ratios", {})
        if not ratios_response.get("isError"):
            print("   ✓ All financial ratios calculated successfully")
            summary_text = ratios_response['content'][0]['text']
            if 'Key Ratios:' in summary_text:
                key_ratios_part = summary_text.split('Key Ratios:')[1].split('\n\n')[0]
                print(f"   Summary: {key_ratios_part}")
            else:
                print("   Summary: No key ratios found")
        else:
            print(f"   Error: {ratios_response['content'][0]['text']}")
        
        # Test specific categories
        profitability_response = await server.handle_call_tool("calculate_ratios", {"categories": ["profitability"]})
        if not profitability_response.get("isError"):
            print("   ✓ Profitability ratios calculated successfully")
        else:
            print(f"   Error getting profitability ratios: {profitability_response['content'][0]['text']}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # Test 7: Advanced Financial Analysis Tools
    print("\n7. Testing Advanced Financial Analysis Tools...")
    try:
        # Test financial funnel analysis
        funnel_response = await server.handle_call_tool("analyze_financial_funnel", {"funnel_type": "profitability"})
        if not funnel_response.get("isError"):
            print("   ✓ Financial funnel analysis completed successfully")
        else:
            print(f"   Error in funnel analysis: {funnel_response['content'][0]['text']}")
        
        # Test growth trends analysis
        trends_response = await server.handle_call_tool("analyze_growth_trends", {"metrics": ["revenue", "profit"]})
        if not trends_response.get("isError"):
            print("   ✓ Growth trends analysis completed successfully")
        else:
            print(f"   Error in trends analysis: {trends_response['content'][0]['text']}")
        
        # Test drill-down analysis
        drill_down_response = await server.handle_call_tool("get_drill_down_analysis", {"breakdown_type": "revenue"})
        if not drill_down_response.get("isError"):
            print("   ✓ Drill-down analysis completed successfully")
        else:
            print(f"   Error in drill-down analysis: {drill_down_response['content'][0]['text']}")
        
        # Test comprehensive efficiency report
        efficiency_response = await server.handle_call_tool("financial_efficiency_report", {})
        if not efficiency_response.get("isError"):
            print("   ✓ Financial efficiency report generated successfully")
        else:
            print(f"   Error in efficiency report: {efficiency_response['content'][0]['text']}")
            
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # Test 8: Supporting MCP Tools
    print("\n8. Testing Supporting MCP Tools...")
    try:
        # Test enhanced search
        search_response = await server.handle_call_tool("search_financial_data", {
            "query": "revenue", 
            "limit": 10,
            "include_suggestions": True
        })
        if not search_response.get("isError"):
            print("   ✓ Enhanced search completed successfully")
        else:
            print(f"   Error in search: {search_response['content'][0]['text']}")
        
        # Test enhanced company info
        company_response = await server.handle_call_tool("get_company_info", {"include_filing_details": True})
        if not company_response.get("isError"):
            print("   ✓ Enhanced company info retrieved successfully")
        else:
            print(f"   Error in company info: {company_response['content'][0]['text']}")
        
        # Test data validation
        validation_response = await server.handle_call_tool("validate_financial_data", {"validation_type": "comprehensive"})
        if not validation_response.get("isError"):
            print("   ✓ Data validation completed successfully")
        else:
            print(f"   Error in validation: {validation_response['content'][0]['text']}")
        
        # Test data quality report
        quality_response = await server.handle_call_tool("get_data_quality_report", {"include_recommendations": True})
        if not quality_response.get("isError"):
            print("   ✓ Data quality report generated successfully")
        else:
            print(f"   Error in quality report: {quality_response['content'][0]['text']}")
        
        # Test available concepts
        concepts_response = await server.handle_call_tool("get_available_concepts", {"limit": 20})
        if not concepts_response.get("isError"):
            print("   ✓ Available concepts retrieved successfully")
        else:
            print(f"   Error in concepts: {concepts_response['content'][0]['text']}")
        
        # Test available periods
        periods_response = await server.handle_call_tool("get_available_periods", {"include_details": True})
        if not periods_response.get("isError"):
            print("   ✓ Available periods retrieved successfully")
        else:
            print(f"   Error in periods: {periods_response['content'][0]['text']}")
            
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Enhanced MCP Tools Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp_tools())