"""
XBRL Financial Data Service

A comprehensive Python service for parsing XBRL financial documents
and providing structured financial data through MCP protocol.
"""

__version__ = "0.1.0"
__author__ = "XBRL Financial Service Team"

from .financial_service import FinancialService
from .models import FinancialFact, FinancialStatement, FilingData
from .xbrl_parser import XBRLParser
from .config import Config

__all__ = [
    "FinancialService",
    "FinancialFact", 
    "FinancialStatement",
    "FilingData",
    "XBRLParser",
    "Config"
]