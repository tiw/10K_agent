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
from .analysis.funnel_analyzer import FunnelAnalyzer
from .analysis.trend_analyzer import TrendAnalyzer
from .analysis.drill_down_engine import DrillDownEngine
from .analysis.efficiency_calculator import EfficiencyCalculator
from .error_handler import error_handler, handle_errors, error_context

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
                "description": "Get cash flow statement data with section breakdown", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "description": "Optional period filter"},
                        "section": {"type": "string", "description": "Optional section filter: operating, investing, financing", "enum": ["operating", "investing", "financing"]}
                    }
                }
            },
            "calculate_ratios": {
                "name": "calculate_ratios",
                "description": "Calculate financial ratios with ratio selection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "categories": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["profitability", "liquidity", "leverage", "efficiency"]},
                            "description": "Optional ratio categories to include"
                        },
                        "ratios": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Optional specific ratio names to include"
                        }
                    }
                }
            },
            "search_financial_data": {
                "name": "search_financial_data",
                "description": "Search for specific financial information with flexible queries",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "query": {"type": "string", "description": "Search query for concept names or labels"},
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 50},
                        "statement_type": {"type": "string", "enum": ["income_statement", "balance_sheet", "cash_flow_statement"], "description": "Filter by statement type"},
                        "include_fuzzy": {"type": "boolean", "description": "Include fuzzy matching results", "default": True},
                        "include_suggestions": {"type": "boolean", "description": "Include search suggestions", "default": False}
                    },
                    "required": ["query"]
                }
            },
            "get_company_info": {
                "name": "get_company_info",
                "description": "Get comprehensive company information and entity details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_filing_details": {"type": "boolean", "description": "Include filing metadata", "default": True},
                        "include_business_description": {"type": "boolean", "description": "Include business description if available", "default": False}
                    }
                }
            },
            "get_summary": {
                "name": "get_summary",
                "description": "Get summary of loaded financial data",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "analyze_financial_funnel": {
                "name": "analyze_financial_funnel",
                "description": "Analyze financial funnel for vertical efficiency analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "funnel_type": {
                            "type": "string",
                            "enum": ["profitability", "cash_conversion", "capital_efficiency"],
                            "description": "Type of funnel analysis to perform"
                        },
                        "period": {"type": "string", "description": "Optional period filter"}
                    },
                    "required": ["funnel_type"]
                }
            },
            "analyze_growth_trends": {
                "name": "analyze_growth_trends",
                "description": "Analyze growth trends for horizontal trend analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["revenue", "profit", "cash_flow", "margins", "returns"]},
                            "description": "Metrics to analyze for trends"
                        },
                        "comprehensive": {"type": "boolean", "description": "Generate comprehensive trend report", "default": False}
                    }
                }
            },
            "get_drill_down_analysis": {
                "name": "get_drill_down_analysis",
                "description": "Get detailed segment breakdowns for drill-down analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "breakdown_type": {
                            "type": "string",
                            "enum": ["revenue", "expenses", "assets", "comprehensive"],
                            "description": "Type of breakdown analysis to perform"
                        },
                        "period": {"type": "string", "description": "Optional period filter"}
                    },
                    "required": ["breakdown_type"]
                }
            },
            "financial_efficiency_report": {
                "name": "financial_efficiency_report",
                "description": "Generate comprehensive financial efficiency report combining funnel and trend analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "description": "Optional period filter"},
                        "include_benchmarks": {"type": "boolean", "description": "Include industry benchmarks", "default": True}
                    }
                }
            },
            "validate_financial_data": {
                "name": "validate_financial_data",
                "description": "Validate financial data quality and consistency",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "validation_type": {
                            "type": "string",
                            "enum": ["comprehensive", "calculations", "completeness", "consistency"],
                            "description": "Type of validation to perform",
                            "default": "comprehensive"
                        },
                        "include_warnings": {"type": "boolean", "description": "Include warning-level issues", "default": True}
                    }
                }
            },
            "get_data_quality_report": {
                "name": "get_data_quality_report",
                "description": "Generate comprehensive data quality assessment report",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_recommendations": {"type": "boolean", "description": "Include improvement recommendations", "default": True},
                        "detailed_analysis": {"type": "boolean", "description": "Include detailed analysis by category", "default": False}
                    }
                }
            },
            "get_available_concepts": {
                "name": "get_available_concepts",
                "description": "Get list of available financial concepts and their usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Pattern to filter concepts"},
                        "limit": {"type": "integer", "description": "Maximum results to return", "default": 100},
                        "include_usage_stats": {"type": "boolean", "description": "Include usage statistics", "default": False}
                    }
                }
            },
            "get_available_periods": {
                "name": "get_available_periods",
                "description": "Get list of available reporting periods",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_details": {"type": "boolean", "description": "Include period details and fact counts", "default": False}
                    }
                }
            }
        }
    
    async def handle_list_tools(self) -> Dict[str, Any]:
        """Handle list_tools request"""
        return {
            "tools": list(self.tools.values())
        }
    
    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call_tool request with comprehensive error handling"""
        with error_context({'operation': 'mcp_tool_call', 'tool_name': name, 'arguments': arguments}):
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
                elif name == "analyze_financial_funnel":
                    return await self._analyze_financial_funnel(arguments)
                elif name == "analyze_growth_trends":
                    return await self._analyze_growth_trends(arguments)
                elif name == "get_drill_down_analysis":
                    return await self._get_drill_down_analysis(arguments)
                elif name == "financial_efficiency_report":
                    return await self._financial_efficiency_report(arguments)
                elif name == "validate_financial_data":
                    return await self._validate_financial_data(arguments)
                elif name == "get_data_quality_report":
                    return await self._get_data_quality_report(arguments)
                elif name == "get_available_concepts":
                    return await self._get_available_concepts(arguments)
                elif name == "get_available_periods":
                    return await self._get_available_periods(arguments)
                elif name == "get_error_statistics":
                    return await self._get_error_statistics(arguments)
                else:
                    raise MCPError(
                        f"Unknown tool: {name}",
                        mcp_operation="tool_call",
                        details={"available_tools": list(self.tools.keys())},
                        suggestions=[
                            "Check tool name spelling",
                            "Use list_tools to see available tools",
                            "Refer to tool documentation"
                        ]
                    )
                    
            except Exception as e:
                # Use error handler for structured error response
                error_response = error_handler.handle_error(
                    e, 
                    context={'tool_name': name, 'arguments': arguments},
                    user_friendly=True
                )
                
                # Convert to MCP error format
                return {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(error_response, indent=2)
                        }
                    ]
                }
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
        """Get income statement data with period filtering"""
        period = arguments.get("period")
        
        try:
            statement = self.financial_service.get_income_statement(period)
            
            if not statement:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Income statement not available. Please load XBRL filing data first."
                        }
                    ]
                }
            
            # Format statement data with key metrics highlighted
            statement_data = statement.to_dict()
            
            # Extract key income statement metrics
            key_metrics = {}
            for fact in statement.facts:
                concept = fact.concept.lower()
                if 'revenue' in concept or 'sales' in concept:
                    key_metrics['Revenue'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'grossprofit' in concept:
                    key_metrics['Gross Profit'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'operatingincome' in concept:
                    key_metrics['Operating Income'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'netincome' in concept and 'loss' not in concept:
                    key_metrics['Net Income'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
            
            summary_text = f"Income Statement for {statement.company_name}\n"
            summary_text += f"Period End: {statement.period_end}\n"
            summary_text += f"Number of Facts: {len(statement.facts)}\n\n"
            
            if key_metrics:
                summary_text += "Key Metrics:\n"
                for metric, value in key_metrics.items():
                    summary_text += f"  {metric}: {value}\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
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
        """Get balance sheet data with date selection"""
        period = arguments.get("period")
        
        try:
            statement = self.financial_service.get_balance_sheet(period)
            
            if not statement:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Balance sheet not available. Please load XBRL filing data first."
                        }
                    ]
                }
            
            statement_data = statement.to_dict()
            
            # Extract key balance sheet metrics
            key_metrics = {}
            for fact in statement.facts:
                concept = fact.concept.lower()
                if 'assets' in concept and concept.endswith('assets'):
                    key_metrics['Total Assets'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'liabilities' in concept and concept.endswith('liabilities'):
                    key_metrics['Total Liabilities'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'stockholdersequity' in concept or 'shareholdersequity' in concept:
                    key_metrics['Stockholders Equity'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'assetscurrent' in concept:
                    key_metrics['Current Assets'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'liabilitiescurrent' in concept:
                    key_metrics['Current Liabilities'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
            
            summary_text = f"Balance Sheet for {statement.company_name}\n"
            summary_text += f"Period End: {statement.period_end}\n"
            summary_text += f"Number of Facts: {len(statement.facts)}\n\n"
            
            if key_metrics:
                summary_text += "Key Metrics:\n"
                for metric, value in key_metrics.items():
                    summary_text += f"  {metric}: {value}\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
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
        """Get cash flow statement data with section breakdown"""
        period = arguments.get("period")
        section = arguments.get("section")  # operating, investing, financing, or all
        
        try:
            statement = self.financial_service.get_cash_flow_statement(period)
            
            if not statement:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Cash flow statement not available. Please load XBRL filing data first."
                        }
                    ]
                }
            
            statement_data = statement.to_dict()
            
            # Categorize cash flow facts by section
            sections = {
                'operating': [],
                'investing': [],
                'financing': []
            }
            
            key_metrics = {}
            
            for fact in statement.facts:
                concept = fact.concept.lower()
                
                # Categorize by section
                if 'operating' in concept:
                    sections['operating'].append(fact)
                    if 'netcashprovidedbyusedinoperatingactivities' in concept:
                        key_metrics['Operating Cash Flow'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'investing' in concept:
                    sections['investing'].append(fact)
                    if 'netcashprovidedbyusedininvestingactivities' in concept:
                        key_metrics['Investing Cash Flow'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
                elif 'financing' in concept:
                    sections['financing'].append(fact)
                    if 'netcashprovidedbyusedinfinancingactivities' in concept:
                        key_metrics['Financing Cash Flow'] = f"{fact.value:,.0f}" if isinstance(fact.value, (int, float)) else str(fact.value)
            
            summary_text = f"Cash Flow Statement for {statement.company_name}\n"
            summary_text += f"Period End: {statement.period_end}\n"
            summary_text += f"Number of Facts: {len(statement.facts)}\n\n"
            
            if key_metrics:
                summary_text += "Key Cash Flow Metrics:\n"
                for metric, value in key_metrics.items():
                    summary_text += f"  {metric}: {value}\n"
            
            # Add section breakdown
            summary_text += f"\nSection Breakdown:\n"
            summary_text += f"  Operating Activities: {len(sections['operating'])} facts\n"
            summary_text += f"  Investing Activities: {len(sections['investing'])} facts\n"
            summary_text += f"  Financing Activities: {len(sections['financing'])} facts\n"
            
            # Filter by section if requested
            if section and section.lower() in sections:
                filtered_facts = [fact.to_dict() for fact in sections[section.lower()]]
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"{summary_text}\n\nShowing {section.title()} Activities Only:"
                        },
                        {
                            "type": "text",
                            "text": json.dumps(filtered_facts, indent=2, default=str)
                        }
                    ]
                }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
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
        """Calculate financial ratios with ratio selection"""
        ratio_categories = arguments.get("categories", [])  # profitability, liquidity, leverage, efficiency
        specific_ratios = arguments.get("ratios", [])  # specific ratio names
        
        try:
            # Get all financial ratios
            ratios = self.financial_service.get_financial_ratios()
            ratios_data = ratios.to_dict()
            
            # If specific categories or ratios requested, filter results
            if ratio_categories or specific_ratios:
                filtered_ratios = {}
                
                # Category mapping
                category_mapping = {
                    'profitability': ['net_profit_margin', 'gross_profit_margin', 'operating_margin', 'return_on_assets', 'return_on_equity'],
                    'liquidity': ['current_ratio', 'quick_ratio', 'cash_ratio'],
                    'leverage': ['debt_to_equity', 'debt_to_assets', 'equity_ratio', 'debt_ratio'],
                    'efficiency': ['asset_turnover', 'inventory_turnover', 'receivables_turnover']
                }
                
                # Add ratios by category
                for category in ratio_categories:
                    if category.lower() in category_mapping:
                        for ratio_name in category_mapping[category.lower()]:
                            if ratio_name in ratios_data:
                                filtered_ratios[ratio_name] = ratios_data[ratio_name]
                
                # Add specific ratios
                for ratio_name in specific_ratios:
                    if ratio_name in ratios_data:
                        filtered_ratios[ratio_name] = ratios_data[ratio_name]
                
                ratios_data = filtered_ratios if filtered_ratios else ratios_data
            
            # Create summary text with key insights
            summary_text = "Financial Ratios Analysis\n\n"
            
            # Highlight key ratios with interpretation
            key_insights = []
            if 'net_profit_margin' in ratios_data and ratios_data['net_profit_margin']:
                margin = ratios_data['net_profit_margin'] * 100
                key_insights.append(f"Net Profit Margin: {margin:.2f}%")
            
            if 'return_on_equity' in ratios_data and ratios_data['return_on_equity']:
                roe = ratios_data['return_on_equity'] * 100
                key_insights.append(f"Return on Equity: {roe:.2f}%")
            
            if 'current_ratio' in ratios_data and ratios_data['current_ratio']:
                cr = ratios_data['current_ratio']
                key_insights.append(f"Current Ratio: {cr:.2f}")
            
            if 'debt_to_equity' in ratios_data and ratios_data['debt_to_equity']:
                dte = ratios_data['debt_to_equity']
                key_insights.append(f"Debt-to-Equity: {dte:.2f}")
            
            if key_insights:
                summary_text += "Key Ratios:\n"
                for insight in key_insights:
                    summary_text += f"  {insight}\n"
                summary_text += "\n"
            
            # Add filtering info if applied
            if ratio_categories or specific_ratios:
                summary_text += f"Filtered by: "
                if ratio_categories:
                    summary_text += f"Categories: {', '.join(ratio_categories)} "
                if specific_ratios:
                    summary_text += f"Ratios: {', '.join(specific_ratios)}"
                summary_text += "\n\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
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
        """Search financial data with flexible queries"""
        query = arguments.get("query")
        limit = arguments.get("limit", 50)
        statement_type = arguments.get("statement_type")
        include_fuzzy = arguments.get("include_fuzzy", True)
        include_suggestions = arguments.get("include_suggestions", False)
        
        if not query:
            raise MCPError("query parameter is required")
        
        try:
            # Use advanced search if available
            if hasattr(self.financial_service, 'advanced_search'):
                from .models import StatementType
                stmt_type = None
                if statement_type:
                    stmt_type = StatementType(statement_type)
                
                search_response = self.financial_service.advanced_search(
                    query=query,
                    statement_type=stmt_type,
                    include_suggestions=include_suggestions
                )
                
                facts = [result.fact for result in search_response.results[:limit]]
                suggestions = search_response.suggestions if include_suggestions else []
            else:
                # Fallback to basic search
                facts = self.financial_service.search_facts(query, limit)
                suggestions = []
            
            if not facts and not suggestions:
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
                result_item = {
                    "concept": fact.concept,
                    "label": fact.label,
                    "value": fact.value,
                    "unit": fact.unit,
                    "period": fact.period
                }
                
                # Add additional metadata if available
                if hasattr(fact, 'period_type'):
                    result_item["period_type"] = fact.period_type
                if hasattr(fact, 'dimensions') and fact.dimensions:
                    result_item["dimensions"] = fact.dimensions
                
                results.append(result_item)
            
            # Create summary text
            summary_text = f"Search Results for '{query}'\n"
            summary_text += f"Found {len(facts)} facts"
            if statement_type:
                summary_text += f" in {statement_type}"
            summary_text += "\n\n"
            
            # Add top results summary
            if results:
                summary_text += "Top Results:\n"
                for i, result in enumerate(results[:5], 1):
                    value_str = f"{result['value']:,.0f}" if isinstance(result['value'], (int, float)) else str(result['value'])
                    summary_text += f"  {i}. {result['label'] or result['concept']}: {value_str} {result['unit'] or ''}\n"
            
            # Add suggestions if available
            if suggestions:
                summary_text += f"\nSuggestions ({len(suggestions)}):\n"
                for suggestion in suggestions[:3]:
                    summary_text += f"  • {suggestion}\n"
            
            response_data = {
                "query": query,
                "total_results": len(facts),
                "results": results
            }
            
            if suggestions:
                response_data["suggestions"] = suggestions
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(response_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error searching financial data: {str(e)}")
    
    async def _get_company_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive company information and entity details"""
        include_filing_details = arguments.get("include_filing_details", True)
        include_business_description = arguments.get("include_business_description", False)
        
        try:
            company_info = self.financial_service.get_company_info()
            
            if not company_info:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Company information not available. Please load XBRL filing data first."
                        }
                    ]
                }
            
            # Create comprehensive company data
            company_data = company_info.to_dict()
            
            # Add filing details if requested and available
            if include_filing_details and self.financial_service.filing_data:
                filing_data = self.financial_service.filing_data
                company_data["filing_details"] = {
                    "filing_date": filing_data.filing_date.isoformat() if filing_data.filing_date else None,
                    "period_end_date": filing_data.period_end_date.isoformat() if filing_data.period_end_date else None,
                    "form_type": filing_data.form_type,
                    "total_facts": len(filing_data.all_facts),
                    "statements_available": {
                        "income_statement": filing_data.income_statement is not None,
                        "balance_sheet": filing_data.balance_sheet is not None,
                        "cash_flow_statement": filing_data.cash_flow_statement is not None,
                        "shareholders_equity": filing_data.shareholders_equity is not None,
                        "comprehensive_income": filing_data.comprehensive_income is not None
                    }
                }
            
            # Add business description if requested (would need to be extracted from facts)
            if include_business_description:
                # Look for business description facts
                business_facts = []
                if self.financial_service.filing_data:
                    for fact in self.financial_service.filing_data.all_facts:
                        if any(keyword in fact.concept.lower() for keyword in ['business', 'description', 'overview', 'operations']):
                            if isinstance(fact.value, str) and len(fact.value) > 50:
                                business_facts.append({
                                    "concept": fact.concept,
                                    "description": fact.value[:500] + "..." if len(fact.value) > 500 else fact.value
                                })
                
                if business_facts:
                    company_data["business_description"] = business_facts[:3]  # Top 3 descriptions
            
            # Create summary text
            summary_text = f"Company Information: {company_info.name}\n"
            if company_info.cik:
                summary_text += f"CIK: {company_info.cik}\n"
            if company_info.ticker:
                summary_text += f"Ticker: {company_info.ticker}\n"
            if hasattr(company_info, 'sic') and company_info.sic:
                summary_text += f"SIC: {company_info.sic}\n"
            if hasattr(company_info, 'fiscal_year_end') and company_info.fiscal_year_end:
                summary_text += f"Fiscal Year End: {company_info.fiscal_year_end}\n"
            if hasattr(company_info, 'address') and company_info.address:
                summary_text += f"Address: {company_info.address}\n"
            if hasattr(company_info, 'phone') and company_info.phone:
                summary_text += f"Phone: {company_info.phone}\n"
            
            if include_filing_details and "filing_details" in company_data:
                filing_details = company_data["filing_details"]
                summary_text += f"\nFiling Details:\n"
                summary_text += f"  Form Type: {filing_details['form_type']}\n"
                summary_text += f"  Period End: {filing_details['period_end_date']}\n"
                summary_text += f"  Total Facts: {filing_details['total_facts']}\n"
                
                available_statements = [k for k, v in filing_details['statements_available'].items() if v]
                summary_text += f"  Available Statements: {', '.join(available_statements)}\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(company_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error getting company information: {str(e)}")
    
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
    
    async def _analyze_financial_funnel(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial funnel for vertical efficiency analysis"""
        funnel_type = arguments.get("funnel_type")
        period = arguments.get("period")
        
        if not self.financial_service.filing_data:
            raise MCPError("No filing data loaded. Please load XBRL filing data first.")
        
        try:
            # Create funnel analyzer
            funnel_analyzer = FunnelAnalyzer(self.financial_service.filing_data)
            
            # Perform the requested funnel analysis
            if funnel_type == "profitability":
                funnel = funnel_analyzer.get_profitability_funnel(period)
            elif funnel_type == "cash_conversion":
                funnel = funnel_analyzer.get_cash_conversion_funnel(period)
            elif funnel_type == "capital_efficiency":
                funnel = funnel_analyzer.get_capital_efficiency_funnel(period)
            else:
                raise MCPError(f"Unknown funnel type: {funnel_type}")
            
            # Format the response
            summary_text = f"Financial Funnel Analysis - {funnel.funnel_type.title()}\n"
            summary_text += f"Company: {funnel.company_name}\n"
            summary_text += f"Period: {funnel.period}\n"
            summary_text += f"Total Conversion Rate: {funnel.total_conversion_rate:.2f}%\n\n"
            
            # Add funnel levels
            summary_text += "Funnel Levels:\n"
            for level in funnel.levels:
                summary_text += f"  {level.name}: {level.value:,.0f} {level.unit}"
                if level.conversion_rate is not None:
                    summary_text += f" ({level.conversion_rate:.1f}%)"
                summary_text += "\n"
                
                # Add children if available
                for child in level.children:
                    summary_text += f"    └─ {child.name}: {child.value:,.0f} {child.unit}"
                    if child.conversion_rate is not None:
                        summary_text += f" ({child.conversion_rate:.1f}%)"
                    summary_text += "\n"
            
            # Add insights
            if funnel.key_insights:
                summary_text += "\nKey Insights:\n"
                for insight in funnel.key_insights:
                    summary_text += f"  • {insight}\n"
            
            # Convert funnel to dict for JSON response
            funnel_data = {
                "company_name": funnel.company_name,
                "period": funnel.period,
                "funnel_type": funnel.funnel_type,
                "total_conversion_rate": funnel.total_conversion_rate,
                "levels": [
                    {
                        "name": level.name,
                        "value": level.value,
                        "unit": level.unit,
                        "conversion_rate": level.conversion_rate,
                        "efficiency_ratio": level.efficiency_ratio,
                        "children": [
                            {
                                "name": child.name,
                                "value": child.value,
                                "unit": child.unit,
                                "conversion_rate": child.conversion_rate
                            } for child in level.children
                        ]
                    } for level in funnel.levels
                ],
                "key_insights": funnel.key_insights
            }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(funnel_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error analyzing financial funnel: {str(e)}")
    
    async def _analyze_growth_trends(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth trends for horizontal trend analysis"""
        metrics = arguments.get("metrics", ["revenue", "profit", "cash_flow"])
        comprehensive = arguments.get("comprehensive", False)
        
        if not self.financial_service.filing_data:
            raise MCPError("No filing data loaded. Please load XBRL filing data first.")
        
        try:
            # Create trend analyzer
            trend_analyzer = TrendAnalyzer(self.financial_service.filing_data)
            
            if comprehensive:
                # Generate comprehensive report
                report = trend_analyzer.generate_comprehensive_report()
                
                summary_text = f"Comprehensive Growth Trend Analysis\n"
                summary_text += f"Company: {report.company_name}\n"
                summary_text += f"Analysis Period: {report.analysis_period}\n"
                summary_text += f"Overall Growth Score: {report.overall_growth_score:.1f}/100\n"
                summary_text += f"Growth Quality Score: {report.growth_quality_score:.1f}/100\n\n"
                
                # Add executive summary
                if report.executive_summary:
                    summary_text += "Executive Summary:\n"
                    for summary_point in report.executive_summary:
                        summary_text += f"  • {summary_point}\n"
                    summary_text += "\n"
                
                # Add trend summaries
                if report.revenue_trend:
                    summary_text += f"Revenue Trend: CAGR {report.revenue_trend.cagr:.1f}% ({report.revenue_trend.trend_direction})\n"
                if report.profit_trend:
                    summary_text += f"Profit Trend: CAGR {report.profit_trend.cagr:.1f}% ({report.profit_trend.trend_direction})\n"
                if report.cash_flow_trend:
                    summary_text += f"Cash Flow Trend: CAGR {report.cash_flow_trend.cagr:.1f}% ({report.cash_flow_trend.trend_direction})\n"
                
                # Convert to dict for JSON
                report_data = {
                    "company_name": report.company_name,
                    "analysis_period": report.analysis_period,
                    "overall_growth_score": report.overall_growth_score,
                    "growth_quality_score": report.growth_quality_score,
                    "executive_summary": report.executive_summary,
                    "revenue_trend": self._trend_to_dict(report.revenue_trend) if report.revenue_trend else None,
                    "profit_trend": self._trend_to_dict(report.profit_trend) if report.profit_trend else None,
                    "cash_flow_trend": self._trend_to_dict(report.cash_flow_trend) if report.cash_flow_trend else None,
                    "margin_trends": {k: self._trend_to_dict(v) for k, v in report.margin_trends.items()},
                    "return_trends": {k: self._trend_to_dict(v) for k, v in report.return_trends.items()}
                }
                
            else:
                # Analyze specific metrics
                trends = {}
                summary_text = f"Growth Trend Analysis\n"
                summary_text += f"Company: {self.financial_service.filing_data.company_info.name}\n\n"
                
                for metric in metrics:
                    if metric == "revenue":
                        trend = trend_analyzer.analyze_revenue_trend()
                        if trend:
                            trends["revenue"] = trend
                            summary_text += f"Revenue Trend: CAGR {trend.cagr:.1f}% ({trend.trend_direction})\n"
                    elif metric == "profit":
                        trend = trend_analyzer.analyze_profit_trend()
                        if trend:
                            trends["profit"] = trend
                            summary_text += f"Profit Trend: CAGR {trend.cagr:.1f}% ({trend.trend_direction})\n"
                    elif metric == "cash_flow":
                        trend = trend_analyzer.analyze_cash_flow_trend()
                        if trend:
                            trends["cash_flow"] = trend
                            summary_text += f"Cash Flow Trend: CAGR {trend.cagr:.1f}% ({trend.trend_direction})\n"
                    elif metric == "margins":
                        margin_trends = trend_analyzer.analyze_margin_trends()
                        trends["margins"] = margin_trends
                        summary_text += f"Margin Trends: {len(margin_trends)} metrics analyzed\n"
                    elif metric == "returns":
                        return_trends = trend_analyzer.analyze_return_trends()
                        trends["returns"] = return_trends
                        summary_text += f"Return Trends: {len(return_trends)} metrics analyzed\n"
                
                # Convert trends to dict
                report_data = {}
                for key, trend in trends.items():
                    if isinstance(trend, dict):
                        report_data[key] = {k: self._trend_to_dict(v) for k, v in trend.items()}
                    else:
                        report_data[key] = self._trend_to_dict(trend)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(report_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error analyzing growth trends: {str(e)}")
    
    async def _get_drill_down_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed segment breakdowns for drill-down analysis"""
        breakdown_type = arguments.get("breakdown_type")
        period = arguments.get("period")
        
        if not self.financial_service.filing_data:
            raise MCPError("No filing data loaded. Please load XBRL filing data first.")
        
        try:
            # Create drill-down engine
            drill_down_engine = DrillDownEngine(self.financial_service.filing_data)
            
            if breakdown_type == "comprehensive":
                # Get comprehensive breakdown
                breakdowns = drill_down_engine.get_comprehensive_breakdown(period)
                
                summary_text = f"Comprehensive Drill-Down Analysis\n"
                summary_text += f"Company: {self.financial_service.filing_data.company_info.name}\n"
                summary_text += f"Period: {period or 'Latest'}\n\n"
                
                breakdown_data = {}
                for category, analysis in breakdowns.items():
                    summary_text += f"{category.title()} Breakdown:\n"
                    summary_text += f"  Total: {analysis.parent_value:,.0f}\n"
                    summary_text += f"  Items: {len(analysis.items)}\n"
                    summary_text += f"  Concentration Ratio: {analysis.concentration_ratio:.1f}%\n"
                    
                    if analysis.key_insights:
                        summary_text += "  Key Insights:\n"
                        for insight in analysis.key_insights[:2]:  # Show top 2 insights
                            summary_text += f"    • {insight}\n"
                    summary_text += "\n"
                    
                    breakdown_data[category] = self._drill_down_to_dict(analysis)
                
            else:
                # Get specific breakdown
                if breakdown_type == "revenue":
                    analysis = drill_down_engine.drill_down_revenue(period)
                elif breakdown_type == "expenses":
                    analysis = drill_down_engine.drill_down_expenses(period)
                elif breakdown_type == "assets":
                    analysis = drill_down_engine.drill_down_assets(period)
                else:
                    raise MCPError(f"Unknown breakdown type: {breakdown_type}")
                
                summary_text = f"{breakdown_type.title()} Drill-Down Analysis\n"
                summary_text += f"Company: {self.financial_service.filing_data.company_info.name}\n"
                summary_text += f"Period: {analysis.period}\n"
                summary_text += f"Total {analysis.parent_metric}: {analysis.parent_value:,.0f}\n"
                summary_text += f"Concentration Ratio: {analysis.concentration_ratio:.1f}%\n"
                summary_text += f"Diversity Score: {analysis.diversity_score:.1f}/100\n\n"
                
                # Add breakdown items
                summary_text += "Breakdown Items:\n"
                for item in analysis.items[:10]:  # Show top 10 items
                    summary_text += f"  {item.name}: {item.value:,.0f} ({item.percentage_of_total:.1f}%)\n"
                
                # Add insights
                if analysis.key_insights:
                    summary_text += "\nKey Insights:\n"
                    for insight in analysis.key_insights:
                        summary_text += f"  • {insight}\n"
                
                breakdown_data = self._drill_down_to_dict(analysis)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(breakdown_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error performing drill-down analysis: {str(e)}")
    
    async def _financial_efficiency_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive financial efficiency report combining funnel and trend analysis"""
        period = arguments.get("period")
        include_benchmarks = arguments.get("include_benchmarks", True)
        
        if not self.financial_service.filing_data:
            raise MCPError("No filing data loaded. Please load XBRL filing data first.")
        
        try:
            # Create efficiency calculator
            efficiency_calculator = EfficiencyCalculator(self.financial_service.filing_data)
            
            # Get comprehensive efficiency report
            efficiency_report = efficiency_calculator.get_comprehensive_efficiency_report(period)
            
            # Create summary
            summary_text = f"Comprehensive Financial Efficiency Report\n"
            summary_text += f"Company: {self.financial_service.filing_data.company_info.name}\n"
            summary_text += f"Period: {period or 'Latest'}\n\n"
            
            # Conversion Analysis Summary
            conversion = efficiency_report['conversion_analysis']
            summary_text += f"Conversion Efficiency Score: {conversion.efficiency_score:.1f}/100\n"
            summary_text += f"Total Conversion Rate: {conversion.total_conversion_rate:.2f}%\n"
            
            if conversion.bottlenecks:
                summary_text += "Bottlenecks:\n"
                for bottleneck in conversion.bottlenecks[:3]:
                    summary_text += f"  • {bottleneck}\n"
            
            # Margin Analysis Summary
            margin = efficiency_report['margin_analysis']
            summary_text += "\nMargin Analysis:\n"
            if margin.gross_margin:
                summary_text += f"  Gross Margin: {margin.gross_margin.value:.1f}% ({margin.gross_margin.performance_rating})\n"
            if margin.operating_margin:
                summary_text += f"  Operating Margin: {margin.operating_margin.value:.1f}% ({margin.operating_margin.performance_rating})\n"
            if margin.net_margin:
                summary_text += f"  Net Margin: {margin.net_margin.value:.1f}% ({margin.net_margin.performance_rating})\n"
            
            # Capital Efficiency Summary
            capital = efficiency_report['capital_efficiency']
            summary_text += f"\nCapital Efficiency Score: {capital.capital_efficiency_score:.1f}/100\n"
            if capital.roe:
                summary_text += f"  ROE: {capital.roe.value:.1f}% ({capital.roe.performance_rating})\n"
            if capital.roa:
                summary_text += f"  ROA: {capital.roa.value:.1f}% ({capital.roa.performance_rating})\n"
            
            # Overall Summary
            summary_info = efficiency_report['summary']
            summary_text += f"\nOverall Efficiency Score: {summary_info['overall_efficiency_score']:.1f}/100\n"
            
            if summary_info['key_strengths']:
                summary_text += "\nKey Strengths:\n"
                for strength in summary_info['key_strengths']:
                    summary_text += f"  • {strength}\n"
            
            if summary_info['improvement_areas']:
                summary_text += "\nImprovement Areas:\n"
                for area in summary_info['improvement_areas']:
                    summary_text += f"  • {area}\n"
            
            # Convert to serializable format
            report_data = {
                "conversion_analysis": {
                    "efficiency_score": conversion.efficiency_score,
                    "total_conversion_rate": conversion.total_conversion_rate,
                    "stages": conversion.stages,
                    "bottlenecks": conversion.bottlenecks,
                    "improvement_opportunities": conversion.improvement_opportunities
                },
                "margin_analysis": self._margin_analysis_to_dict(margin),
                "capital_efficiency": self._capital_efficiency_to_dict(capital),
                "summary": summary_info
            }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(report_data, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error generating efficiency report: {str(e)}")
    
    def _trend_to_dict(self, trend) -> Dict[str, Any]:
        """Convert TrendAnalysis to dictionary"""
        if not trend:
            return None
        
        return {
            "metric_name": trend.metric_name,
            "unit": trend.unit,
            "data_points": [
                {
                    "period": point.period,
                    "value": point.value,
                    "period_start": point.period_start.isoformat() if point.period_start else None,
                    "period_end": point.period_end.isoformat() if point.period_end else None
                } for point in trend.data_points
            ],
            "total_growth_rate": trend.total_growth_rate,
            "cagr": trend.cagr,
            "average_growth_rate": trend.average_growth_rate,
            "trend_direction": trend.trend_direction,
            "volatility": trend.volatility,
            "insights": trend.insights
        }
    
    def _drill_down_to_dict(self, analysis) -> Dict[str, Any]:
        """Convert DrillDownAnalysis to dictionary"""
        return {
            "breakdown_type": analysis.breakdown_type.value,
            "parent_metric": analysis.parent_metric,
            "parent_value": analysis.parent_value,
            "period": analysis.period,
            "items": [
                {
                    "name": item.name,
                    "value": item.value,
                    "unit": item.unit,
                    "percentage_of_total": item.percentage_of_total,
                    "period": item.period,
                    "description": item.description,
                    "growth_rate": item.growth_rate,
                    "trend_direction": item.trend_direction
                } for item in analysis.items
            ],
            "concentration_ratio": analysis.concentration_ratio,
            "diversity_score": analysis.diversity_score,
            "key_insights": analysis.key_insights
        }
    
    def _margin_analysis_to_dict(self, margin) -> Dict[str, Any]:
        """Convert MarginAnalysis to dictionary"""
        return {
            "period": margin.period,
            "gross_margin": self._efficiency_metric_to_dict(margin.gross_margin),
            "operating_margin": self._efficiency_metric_to_dict(margin.operating_margin),
            "net_margin": self._efficiency_metric_to_dict(margin.net_margin),
            "ebitda_margin": self._efficiency_metric_to_dict(margin.ebitda_margin),
            "cash_margin": self._efficiency_metric_to_dict(margin.cash_margin),
            "margin_stability": margin.margin_stability,
            "margin_improvement": margin.margin_improvement,
            "key_insights": margin.key_insights
        }
    
    def _capital_efficiency_to_dict(self, capital) -> Dict[str, Any]:
        """Convert CapitalEfficiencyAnalysis to dictionary"""
        return {
            "period": capital.period,
            "roe": self._efficiency_metric_to_dict(capital.roe),
            "roa": self._efficiency_metric_to_dict(capital.roa),
            "roic": self._efficiency_metric_to_dict(capital.roic),
            "asset_turnover": self._efficiency_metric_to_dict(capital.asset_turnover),
            "inventory_turnover": self._efficiency_metric_to_dict(capital.inventory_turnover),
            "receivables_turnover": self._efficiency_metric_to_dict(capital.receivables_turnover),
            "working_capital_efficiency": self._efficiency_metric_to_dict(capital.working_capital_efficiency),
            "capital_allocation_efficiency": self._efficiency_metric_to_dict(capital.capital_allocation_efficiency),
            "capital_efficiency_score": capital.capital_efficiency_score,
            "key_insights": capital.key_insights
        }
    
    def _efficiency_metric_to_dict(self, metric) -> Optional[Dict[str, Any]]:
        """Convert EfficiencyMetric to dictionary"""
        if not metric:
            return None
        
        return {
            "name": metric.name,
            "value": metric.value,
            "unit": metric.unit,
            "period": metric.period,
            "benchmark_value": metric.benchmark_value,
            "performance_rating": metric.performance_rating,
            "description": metric.description,
            "interpretation": metric.interpretation
        }
    
    async def _validate_financial_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial data quality and consistency"""
        validation_type = arguments.get("validation_type", "comprehensive")
        include_warnings = arguments.get("include_warnings", True)
        
        if not self.financial_service.filing_data:
            raise MCPError("No filing data loaded. Please load XBRL filing data first.")
        
        try:
            validation_results = {
                "validation_type": validation_type,
                "timestamp": "2024-10-18",  # Current timestamp
                "issues": [],
                "warnings": [],
                "summary": {}
            }
            
            filing_data = self.financial_service.filing_data
            
            # Comprehensive validation
            if validation_type in ["comprehensive", "completeness"]:
                # Check data completeness
                completeness_issues = self._validate_data_completeness(filing_data)
                validation_results["issues"].extend(completeness_issues)
            
            if validation_type in ["comprehensive", "calculations"]:
                # Check calculation consistency
                calculation_issues = self._validate_calculations(filing_data)
                validation_results["issues"].extend(calculation_issues)
            
            if validation_type in ["comprehensive", "consistency"]:
                # Check data consistency
                consistency_issues = self._validate_data_consistency(filing_data)
                validation_results["issues"].extend(consistency_issues)
            
            # Generate summary
            total_issues = len(validation_results["issues"])
            total_warnings = len(validation_results["warnings"])
            
            validation_results["summary"] = {
                "total_issues": total_issues,
                "total_warnings": total_warnings,
                "data_quality_score": max(0, 100 - (total_issues * 10) - (total_warnings * 2)),
                "validation_status": "PASS" if total_issues == 0 else "FAIL" if total_issues > 5 else "WARNING"
            }
            
            # Create summary text
            summary_text = f"Financial Data Validation Report\n"
            summary_text += f"Validation Type: {validation_type.title()}\n"
            summary_text += f"Company: {filing_data.company_info.name}\n"
            summary_text += f"Status: {validation_results['summary']['validation_status']}\n"
            summary_text += f"Data Quality Score: {validation_results['summary']['data_quality_score']}/100\n\n"
            
            if total_issues > 0:
                summary_text += f"Issues Found ({total_issues}):\n"
                for i, issue in enumerate(validation_results["issues"][:5], 1):
                    summary_text += f"  {i}. {issue['severity']}: {issue['message']}\n"
                if total_issues > 5:
                    summary_text += f"  ... and {total_issues - 5} more issues\n"
            else:
                summary_text += "✓ No critical issues found\n"
            
            if include_warnings and total_warnings > 0:
                summary_text += f"\nWarnings ({total_warnings}):\n"
                for i, warning in enumerate(validation_results["warnings"][:3], 1):
                    summary_text += f"  {i}. {warning['message']}\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(validation_results, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error validating financial data: {str(e)}")
    
    async def _get_data_quality_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive data quality assessment report"""
        include_recommendations = arguments.get("include_recommendations", True)
        detailed_analysis = arguments.get("detailed_analysis", False)
        
        if not self.financial_service.filing_data:
            raise MCPError("No filing data loaded. Please load XBRL filing data first.")
        
        try:
            filing_data = self.financial_service.filing_data
            
            # Generate quality metrics
            quality_report = {
                "company": filing_data.company_info.name,
                "period": filing_data.period_end_date.isoformat() if filing_data.period_end_date else None,
                "assessment_date": "2024-10-18",
                "metrics": {},
                "recommendations": [],
                "detailed_analysis": {}
            }
            
            # Calculate quality metrics
            total_facts = len(filing_data.all_facts)
            numeric_facts = sum(1 for fact in filing_data.all_facts if isinstance(fact.value, (int, float)))
            facts_with_units = sum(1 for fact in filing_data.all_facts if fact.unit)
            facts_with_periods = sum(1 for fact in filing_data.all_facts if fact.period)
            
            quality_report["metrics"] = {
                "total_facts": total_facts,
                "numeric_facts": numeric_facts,
                "numeric_percentage": (numeric_facts / total_facts * 100) if total_facts > 0 else 0,
                "facts_with_units": facts_with_units,
                "unit_coverage": (facts_with_units / total_facts * 100) if total_facts > 0 else 0,
                "facts_with_periods": facts_with_periods,
                "period_coverage": (facts_with_periods / total_facts * 100) if total_facts > 0 else 0,
                "statement_completeness": {
                    "income_statement": filing_data.income_statement is not None,
                    "balance_sheet": filing_data.balance_sheet is not None,
                    "cash_flow_statement": filing_data.cash_flow_statement is not None
                }
            }
            
            # Calculate overall quality score
            completeness_score = (
                quality_report["metrics"]["numeric_percentage"] * 0.3 +
                quality_report["metrics"]["unit_coverage"] * 0.2 +
                quality_report["metrics"]["period_coverage"] * 0.2 +
                sum(quality_report["metrics"]["statement_completeness"].values()) / 3 * 100 * 0.3
            )
            
            quality_report["overall_quality_score"] = min(100, completeness_score)
            
            # Generate recommendations
            if include_recommendations:
                recommendations = []
                
                if quality_report["metrics"]["numeric_percentage"] < 70:
                    recommendations.append("Consider improving numeric data coverage - many facts appear to be non-numeric")
                
                if quality_report["metrics"]["unit_coverage"] < 80:
                    recommendations.append("Improve unit specification for financial facts to enhance data usability")
                
                if not all(quality_report["metrics"]["statement_completeness"].values()):
                    missing_statements = [k for k, v in quality_report["metrics"]["statement_completeness"].items() if not v]
                    recommendations.append(f"Missing financial statements: {', '.join(missing_statements)}")
                
                if quality_report["overall_quality_score"] < 80:
                    recommendations.append("Overall data quality could be improved - consider data validation and cleanup")
                
                quality_report["recommendations"] = recommendations
            
            # Detailed analysis by category
            if detailed_analysis:
                quality_report["detailed_analysis"] = {
                    "concept_distribution": self._analyze_concept_distribution(filing_data),
                    "period_analysis": self._analyze_period_distribution(filing_data),
                    "unit_analysis": self._analyze_unit_distribution(filing_data)
                }
            
            # Create summary text
            summary_text = f"Data Quality Assessment Report\n"
            summary_text += f"Company: {quality_report['company']}\n"
            summary_text += f"Period: {quality_report['period']}\n"
            summary_text += f"Overall Quality Score: {quality_report['overall_quality_score']:.1f}/100\n\n"
            
            summary_text += "Quality Metrics:\n"
            summary_text += f"  Total Facts: {quality_report['metrics']['total_facts']:,}\n"
            summary_text += f"  Numeric Facts: {quality_report['metrics']['numeric_percentage']:.1f}%\n"
            summary_text += f"  Unit Coverage: {quality_report['metrics']['unit_coverage']:.1f}%\n"
            summary_text += f"  Period Coverage: {quality_report['metrics']['period_coverage']:.1f}%\n"
            
            summary_text += "\nStatement Completeness:\n"
            for stmt, available in quality_report['metrics']['statement_completeness'].items():
                status = "✓" if available else "✗"
                summary_text += f"  {status} {stmt.replace('_', ' ').title()}\n"
            
            if include_recommendations and quality_report["recommendations"]:
                summary_text += "\nRecommendations:\n"
                for i, rec in enumerate(quality_report["recommendations"], 1):
                    summary_text += f"  {i}. {rec}\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps(quality_report, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error generating data quality report: {str(e)}")
    
    async def _get_available_concepts(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of available financial concepts and their usage"""
        pattern = arguments.get("pattern")
        limit = arguments.get("limit", 100)
        include_usage_stats = arguments.get("include_usage_stats", False)
        
        try:
            # Use financial service method if available
            if hasattr(self.financial_service, 'get_available_concepts'):
                concepts = self.financial_service.get_available_concepts(pattern, limit)
            else:
                # Fallback: extract from filing data
                if not self.financial_service.filing_data:
                    raise MCPError("No filing data loaded. Please load XBRL filing data first.")
                
                concept_map = {}
                for fact in self.financial_service.filing_data.all_facts:
                    concept = fact.concept
                    if pattern and pattern.lower() not in concept.lower():
                        continue
                    
                    if concept not in concept_map:
                        concept_map[concept] = {
                            "concept": concept,
                            "label": fact.label or concept.split(':')[-1],
                            "count": 0,
                            "sample_value": None,
                            "unit": fact.unit
                        }
                    
                    concept_map[concept]["count"] += 1
                    if concept_map[concept]["sample_value"] is None:
                        concept_map[concept]["sample_value"] = fact.value
                
                concepts = list(concept_map.values())[:limit]
            
            # Sort by usage if stats are included
            if include_usage_stats and concepts:
                concepts.sort(key=lambda x: x.get("count", 0), reverse=True)
            
            # Create summary
            summary_text = f"Available Financial Concepts\n"
            if pattern:
                summary_text += f"Filter: '{pattern}'\n"
            summary_text += f"Total Concepts: {len(concepts)}\n\n"
            
            summary_text += "Top Concepts:\n"
            for i, concept in enumerate(concepts[:10], 1):
                label = concept.get("label", concept["concept"])
                summary_text += f"  {i}. {label}"
                if include_usage_stats and "count" in concept:
                    summary_text += f" (used {concept['count']} times)"
                summary_text += "\n"
            
            if len(concepts) > 10:
                summary_text += f"  ... and {len(concepts) - 10} more concepts\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps({"concepts": concepts}, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error getting available concepts: {str(e)}")
    
    async def _get_available_periods(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of available reporting periods"""
        include_details = arguments.get("include_details", False)
        
        try:
            # Use financial service method if available
            if hasattr(self.financial_service, 'get_available_periods'):
                periods = self.financial_service.get_available_periods()
            else:
                # Fallback: extract from filing data
                if not self.financial_service.filing_data:
                    raise MCPError("No filing data loaded. Please load XBRL filing data first.")
                
                period_map = {}
                for fact in self.financial_service.filing_data.all_facts:
                    period = fact.period
                    if period not in period_map:
                        period_map[period] = {
                            "period": period,
                            "period_end": fact.period_end.isoformat() if fact.period_end else None,
                            "period_type": getattr(fact, 'period_type', 'unknown'),
                            "fact_count": 0
                        }
                    period_map[period]["fact_count"] += 1
                
                periods = list(period_map.values())
            
            # Sort periods by end date
            periods.sort(key=lambda x: x.get("period_end", ""), reverse=True)
            
            # Create summary
            summary_text = f"Available Reporting Periods\n"
            summary_text += f"Total Periods: {len(periods)}\n\n"
            
            summary_text += "Periods:\n"
            for i, period in enumerate(periods[:10], 1):
                summary_text += f"  {i}. {period['period']}"
                if include_details:
                    if period.get("period_end"):
                        summary_text += f" (ends: {period['period_end']})"
                    if period.get("fact_count"):
                        summary_text += f" - {period['fact_count']} facts"
                summary_text += "\n"
            
            if len(periods) > 10:
                summary_text += f"  ... and {len(periods) - 10} more periods\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary_text
                    },
                    {
                        "type": "text",
                        "text": json.dumps({"periods": periods}, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Error getting available periods: {str(e)}")
    
    def _validate_data_completeness(self, filing_data) -> List[Dict[str, Any]]:
        """Validate data completeness"""
        issues = []
        
        # Check for missing key statements
        if not filing_data.income_statement:
            issues.append({
                "severity": "HIGH",
                "category": "completeness",
                "message": "Income statement data is missing"
            })
        
        if not filing_data.balance_sheet:
            issues.append({
                "severity": "HIGH", 
                "category": "completeness",
                "message": "Balance sheet data is missing"
            })
        
        if not filing_data.cash_flow_statement:
            issues.append({
                "severity": "MEDIUM",
                "category": "completeness",
                "message": "Cash flow statement data is missing"
            })
        
        # Check for missing units in numeric facts
        numeric_facts_without_units = sum(1 for fact in filing_data.all_facts 
                                        if isinstance(fact.value, (int, float)) and not fact.unit)
        
        if numeric_facts_without_units > 0:
            issues.append({
                "severity": "MEDIUM",
                "category": "completeness",
                "message": f"{numeric_facts_without_units} numeric facts are missing units"
            })
        
        return issues
    
    def _validate_calculations(self, filing_data) -> List[Dict[str, Any]]:
        """Validate calculation relationships"""
        issues = []
        
        # This would typically validate against XBRL calculation linkbases
        # For now, we'll do basic validation
        
        # Check for negative values where they shouldn't be
        problematic_concepts = ['Assets', 'Revenue', 'StockholdersEquity']
        for fact in filing_data.all_facts:
            if any(concept in fact.concept for concept in problematic_concepts):
                if isinstance(fact.value, (int, float)) and fact.value < 0:
                    issues.append({
                        "severity": "HIGH",
                        "category": "calculation",
                        "message": f"Negative value found for {fact.concept}: {fact.value}"
                    })
        
        return issues
    
    def _validate_data_consistency(self, filing_data) -> List[Dict[str, Any]]:
        """Validate data consistency"""
        issues = []
        
        # Check for duplicate facts with different values
        fact_map = {}
        for fact in filing_data.all_facts:
            key = (fact.concept, fact.period)
            if key in fact_map:
                if fact_map[key].value != fact.value:
                    issues.append({
                        "severity": "HIGH",
                        "category": "consistency",
                        "message": f"Inconsistent values for {fact.concept} in period {fact.period}"
                    })
            else:
                fact_map[key] = fact
        
        return issues
    
    def _analyze_concept_distribution(self, filing_data) -> Dict[str, Any]:
        """Analyze distribution of concepts"""
        concept_counts = {}
        for fact in filing_data.all_facts:
            concept = fact.concept.split(':')[-1]  # Remove namespace
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        # Get top concepts
        top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_unique_concepts": len(concept_counts),
            "top_concepts": [{"concept": k, "count": v} for k, v in top_concepts]
        }
    
    def _analyze_period_distribution(self, filing_data) -> Dict[str, Any]:
        """Analyze distribution of periods"""
        period_counts = {}
        for fact in filing_data.all_facts:
            period_counts[fact.period] = period_counts.get(fact.period, 0) + 1
        
        return {
            "total_periods": len(period_counts),
            "period_counts": dict(sorted(period_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _analyze_unit_distribution(self, filing_data) -> Dict[str, Any]:
        """Analyze distribution of units"""
        unit_counts = {}
        for fact in filing_data.all_facts:
            unit = fact.unit or "No Unit"
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
        
        return {
            "total_units": len(unit_counts),
            "unit_distribution": dict(sorted(unit_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }


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
    asyncio.run(main())    asy
nc def _get_error_statistics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get error statistics and system health metrics"""
        try:
            stats = error_handler.get_error_statistics()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "error_statistics": stats,
                            "timestamp": stats.get("timestamp", "unknown")
                        }, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Failed to get error statistics: {str(e)}")
    
    async def _validate_financial_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial data quality"""
        try:
            if not self.financial_service.filing_data:
                raise QueryError("No filing data loaded")
            
            # Get validation report from filing data if available
            filing_data = self.financial_service.filing_data
            
            validation_results = {}
            
            # Check if quality report exists
            if hasattr(filing_data, 'quality_report') and filing_data.quality_report:
                validation_results['data_quality'] = filing_data.quality_report
            
            # Check if calculation report exists
            if hasattr(filing_data, 'calculation_report') and filing_data.calculation_report:
                validation_results['calculation_validation'] = filing_data.calculation_report
            
            # If no validation reports exist, generate them
            if not validation_results:
                from .validators import DataValidator, CalculationValidator
                
                data_validator = DataValidator()
                calc_validator = CalculationValidator()
                
                validation_results['data_quality'] = data_validator.generate_data_quality_report(filing_data)
                validation_results['calculation_validation'] = calc_validator.validate_calculations(filing_data)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(validation_results, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Failed to validate financial data: {str(e)}")
    
    async def _get_data_quality_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive data quality report"""
        try:
            if not self.financial_service.filing_data:
                raise QueryError("No filing data loaded")
            
            filing_data = self.financial_service.filing_data
            
            # Check if quality report already exists
            if hasattr(filing_data, 'quality_report') and filing_data.quality_report:
                quality_report = filing_data.quality_report
            else:
                # Generate new quality report
                from .validators import DataValidator
                data_validator = DataValidator()
                quality_report = data_validator.generate_data_quality_report(filing_data)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "data_quality_report": quality_report,
                            "recommendations": quality_report.get('quality', {}).get('recommendations', []),
                            "summary": quality_report.get('summary', {})
                        }, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            raise MCPError(f"Failed to get data quality report: {str(e)}")