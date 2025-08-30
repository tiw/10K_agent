"""
MCP Server for XBRL Financial Service

Exposes financial data through Model Context Protocol for LLM agents.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

# Note: This is a simplified MCP implementation
# In a real implementation, you would use the official MCP Python library
from .financial_service import FinancialService
from .xbrl_parser import XBRLParser
from .config import Config, load_config
from .utils.logging import setup_logging, get_logger
from .utils.exceptions import MCPError, QueryError, XBRLParsingError

logger = get_logger(__name__)


class FinancialMCPServer:
    """
    MCP Server for financial data tools
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.financial_service = FinancialService(config=self.config)
        self.xbrl_parser = XBRLParser(self.config)
        
        # Available tools
        self.tools = {
            "load_xbrl_filing": {
                "name": "load_xbrl_filing",
                "description": "Load XBRL filing data from file paths",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_paths": {
                            "type": "object",
                            "description": "Dictionary mapping file types to paths",
                            "properties": {
                                "schema": {"type": "string", "description": "Path to .xsd schema file"},
                                "calculation": {"type": "string", "description": "Path to _cal.xml calculation linkbase"},
                                "definition": {"type": "string", "description": "Path to _def.xml definition linkbase"},
                                "label": {"type": "string", "description": "Path to _lab.xml label linkbase"},
                                "presentation": {"type": "string", "description": "Path to _pre.xml presentation linkbase"},
                                "instance": {"type": "string", "description": "Path to instance document", "required": True}
                            }
                        }
                    },
                    "required": ["file_paths"]
                }
            },
            "get_income_statement": {
                "name": "get_income_statement",
                "description": "Get income statement data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "description": "Optional period filter"}
                    }
                }
            },
            "get_balance_sheet": {
                "name": "get_balance_sheet", 
                "description": "Get balance sheet data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "description": "Optional period filter"}
                    }
                }
            },
            "get_cash_flow": {
                "name": "get_cash_flow",
                "description": "Get cash flow statement data", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "description": "Optional period filter"}
                    }
                }
            },
            "calculate_ratios": {
                "name": "calculate_ratios",
                "description": "Calculate financial ratios",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "search_financial_data": {
                "name": "search_financial_data",
                "description": "Search for specific financial information",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "query": {"type": "string", "description": "Search query for concept names or labels"},
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 50}
                    },
                    "required": ["query"]
                }
            },
            "get_company_info": {
                "name": "get_company_info",
                "description": "Get basic company information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "get_summary": {
                "name": "get_summary",
                "description": "Get summary of loaded financial data",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    async def handle_list_tools(self) -> Dict[str, Any]:
        """Handle list_tools request"""
        return {
            "tools": list(self.tools.values())
        }
    
    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call_tool request"""
        try:
            if name == "load_xbrl_filing":
                return await self._load_xbrl_filing(arguments)
            elif name == "get_income_statement":
                return await self._get_income_statement(arguments)
            elif name == "get_balance_sheet":
                return await self._get_balance_sheet(arguments)
            elif name == "get_cash_flow":
                return await self._get_cash_flow(arguments)
            elif name == "calculate_ratios":
                return await self._calculate_ratios(arguments)
            elif name == "search_financial_data":
                return await self._search_financial_data(arguments)
            elif name == "get_company_info":
                return await self._get_company_info(arguments)
            elif name == "get_summary":
                return await self._get_summary(arguments)
            else:
                raise MCPError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _load_xbrl_filing(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Load XBRL filing data"""
        file_paths = arguments.get("file_paths", {})
        
        if not file_paths:
            raise MCPError("file_paths parameter is required")
        
        if "instance" not in file_paths:
            raise MCPError("instance file path is required")
        
        try:
            # Parse the filing
            filing_data = self.xbrl_parser.parse_filing(file_paths)
            
            # Load into financial service
            self.financial_service.load_filing_data(filing_data)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully loaded XBRL filing for {filing_data.company_info.name}\n"
                               f"Period: {filing_data.period_end_date}\n"
                               f"Total Facts: {len(filing_data.all_facts)}"
                    }
                ]
            }
            
        except XBRLParsingError as e:
            raise MCPError(f"Failed to parse XBRL filing: {str(e)}")
    
    async def _get_income_statement(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get income statement data"""
        period = arguments.get("period")
        
        try:
            statement = self.financial_service.get_income_statement(period)
            
            if not statement:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Income statement not available"
                        }
                    ]
                }
            
            # Format statement data
            statement_data = statement.to_dict()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Income Statement for {statement.company_name}\n"
                               f"Period End: {statement.period_end}\n"
                               f"Number of Facts: {len(statement.facts)}"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(statement_data, indent=2, default=str)
                    }
                ]
            }
            
        except QueryError as e:
            raise MCPError(str(e))
    
    async def _get_balance_sheet(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get balance sheet data"""
        period = arguments.get("period")
        
        try:
            statement = self.financial_service.get_balance_sheet(period)
            
            if not statement:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Balance sheet not available"
                        }
                    ]
                }
            
            statement_data = statement.to_dict()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Balance Sheet for {statement.company_name}\n"
                               f"Period End: {statement.period_end}\n"
                               f"Number of Facts: {len(statement.facts)}"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(statement_data, indent=2, default=str)
                    }
                ]
            }
            
        except QueryError as e:
            raise MCPError(str(e))
    
    async def _get_cash_flow(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get cash flow statement data"""
        period = arguments.get("period")
        
        try:
            statement = self.financial_service.get_cash_flow_statement(period)
            
            if not statement:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Cash flow statement not available"
                        }
                    ]
                }
            
            statement_data = statement.to_dict()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Cash Flow Statement for {statement.company_name}\n"
                               f"Period End: {statement.period_end}\n"
                               f"Number of Facts: {len(statement.facts)}"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(statement_data, indent=2, default=str)
                    }
                ]
            }
            
        except QueryError as e:
            raise MCPError(str(e))
    
    async def _calculate_ratios(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate financial ratios"""
        try:
            ratios = self.financial_service.get_financial_ratios()
            ratios_data = ratios.to_dict()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Financial Ratios Analysis"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(ratios_data, indent=2, default=str)
                    }
                ]
            }
            
        except QueryError as e:
            raise MCPError(str(e))
    
    async def _search_financial_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search financial data"""
        query = arguments.get("query")
        limit = arguments.get("limit", 50)
        
        if not query:
            raise MCPError("query parameter is required")
        
        try:
            facts = self.financial_service.search_facts(query, limit)
            
            if not facts:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"No facts found matching query: {query}"
                        }
                    ]
                }
            
            # Format results
            results = []
            for fact in facts:
                results.append({
                    "concept": fact.concept,
                    "label": fact.label,
                    "value": fact.value,
                    "unit": fact.unit,
                    "period": fact.period
                })
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {len(facts)} facts matching '{query}'"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(results, indent=2, default=str)
                    }
                ]
            }
            
        except QueryError as e:
            raise MCPError(str(e))
    
    async def _get_company_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get company information"""
        try:
            company_info = self.financial_service.get_company_info()
            
            if not company_info:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Company information not available"
                        }
                    ]
                }
            
            company_data = company_info.to_dict()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Company Information"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(company_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(str(e))
    
    async def _get_summary(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of loaded data"""
        try:
            summary = self.financial_service.get_summary_data()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Financial Data Summary"
                    },
                    {
                        "type": "text",
                        "text": json.dumps(summary, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(str(e))


async def main():
    """Main entry point for MCP server"""
    # Setup logging
    setup_logging(level="INFO")
    
    # Load configuration
    config = load_config()
    
    # Create server
    server = FinancialMCPServer(config)
    
    logger.info(f"Starting XBRL Financial MCP Server on port {config.mcp_port}")
    
    # This is a simplified example - in a real implementation,
    # you would use the official MCP Python library to handle
    # the protocol communication
    
    print("XBRL Financial MCP Server")
    print("Available tools:")
    for tool_name, tool_info in server.tools.items():
        print(f"  - {tool_name}: {tool_info['description']}")
    
    print(f"\nServer ready on port {config.mcp_port}")
    print("Note: This is a simplified implementation.")
    print("In production, use the official MCP Python library.")
    
    # Keep server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")


if __name__ == "__main__":
    asyncio.run(main())