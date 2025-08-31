"""
Core data models for XBRL Financial Service
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Union, Any
import json
from decimal import Decimal


class StatementType(Enum):
    """Types of financial statements"""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW_STATEMENT = "cash_flow_statement"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    COMPREHENSIVE_INCOME = "comprehensive_income"


class PeriodType(Enum):
    """Types of reporting periods"""
    INSTANT = "instant"
    DURATION = "duration"


class UnitType(Enum):
    """Types of measurement units"""
    USD = "USD"
    SHARES = "shares"
    PERCENT = "percent"
    PURE = "pure"
    OTHER = "other"


@dataclass
class FinancialFact:
    """
    Represents a single financial fact from XBRL data
    """
    concept: str                           # XBRL concept name (e.g., "us-gaap:Revenue")
    label: str                            # Human-readable label
    value: Union[float, str, int, Decimal] # Actual value
    unit: Optional[str] = None            # Currency or unit (e.g., "USD", "shares")
    period: str = ""                      # Time period identifier
    period_type: PeriodType = PeriodType.DURATION  # instant or duration
    context_id: str = ""                  # XBRL context reference
    decimals: Optional[int] = None        # Decimal precision (-3 means thousands)
    dimensions: Dict[str, str] = field(default_factory=dict)  # Additional dimensions
    
    # Metadata
    filing_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        # Convert string values to appropriate types
        if isinstance(self.value, str) and self.value.replace('.', '').replace('-', '').isdigit():
            self.value = float(self.value)
        
        # Normalize concept name
        if ':' not in self.concept:
            self.concept = f"us-gaap:{self.concept}"
    
    def get_scaled_value(self) -> Union[float, str, int]:
        """Get value scaled according to decimals attribute"""
        if isinstance(self.value, (int, float, Decimal)) and self.decimals is not None:
            # For XBRL, decimals=-6 means the value should be divided by 10^6 to get the actual value
            # The stored value is already scaled up, so we need to scale it down
            # For Apple: decimals=-6 means value is stored as actual_value * 10^6
            # So to get actual value: stored_value / 10^6
            return float(self.value) / (10 ** abs(self.decimals))
        return self.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "concept": self.concept,
            "label": self.label,
            "value": float(self.value) if isinstance(self.value, (int, float, Decimal)) else self.value,
            "scaled_value": self.get_scaled_value(),
            "unit": self.unit,
            "period": self.period,
            "period_type": self.period_type.value,
            "context_id": self.context_id,
            "decimals": self.decimals,
            "dimensions": self.dimensions,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


@dataclass
class CalculationRelationship:
    """
    Represents a calculation relationship between financial concepts
    """
    parent: str                    # Parent concept
    child: str                    # Child concept  
    weight: float                 # Calculation weight (usually 1.0 or -1.0)
    order: int                    # Presentation order
    role: Optional[str] = None    # XBRL role URI
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "parent": self.parent,
            "child": self.child,
            "weight": self.weight,
            "order": self.order,
            "role": self.role
        }


@dataclass
class PresentationRelationship:
    """
    Represents presentation hierarchy relationships
    """
    parent: str                    # Parent concept
    child: str                    # Child concept
    order: int                    # Presentation order
    preferred_label: Optional[str] = None  # Preferred label role
    role: Optional[str] = None    # XBRL role URI
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "parent": self.parent,
            "child": self.child,
            "order": self.order,
            "preferred_label": self.preferred_label,
            "role": self.role
        }


@dataclass
class TaxonomyElement:
    """
    Represents an XBRL taxonomy element definition
    """
    name: str                     # Element name
    type: str                     # Data type
    substitution_group: str       # Substitution group
    period_type: PeriodType       # instant or duration
    balance: Optional[str] = None # debit or credit
    abstract: bool = False        # Whether element is abstract
    nillable: bool = True        # Whether element can be nil
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "type": self.type,
            "substitution_group": self.substitution_group,
            "period_type": self.period_type.value,
            "balance": self.balance,
            "abstract": self.abstract,
            "nillable": self.nillable
        }


@dataclass
class FinancialStatement:
    """
    Represents a complete financial statement
    """
    statement_type: StatementType
    company_name: str
    period_end: date
    facts: List[FinancialFact] = field(default_factory=list)
    calculations: List[CalculationRelationship] = field(default_factory=list)
    presentation_order: List[PresentationRelationship] = field(default_factory=list)
    
    def get_fact_by_concept(self, concept: str) -> Optional[FinancialFact]:
        """Get a fact by its concept name"""
        for fact in self.facts:
            if fact.concept == concept or fact.concept.endswith(f":{concept}"):
                return fact
        return None
    
    def get_facts_by_pattern(self, pattern: str) -> List[FinancialFact]:
        """Get facts matching a pattern in concept name or label"""
        pattern_lower = pattern.lower()
        matching_facts = []
        
        for fact in self.facts:
            if (pattern_lower in fact.concept.lower() or 
                pattern_lower in fact.label.lower()):
                matching_facts.append(fact)
        
        return matching_facts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "statement_type": self.statement_type.value,
            "company_name": self.company_name,
            "period_end": self.period_end.isoformat(),
            "facts": [fact.to_dict() for fact in self.facts],
            "calculations": [calc.to_dict() for calc in self.calculations],
            "presentation_order": [pres.to_dict() for pres in self.presentation_order]
        }


@dataclass
class CompanyInfo:
    """
    Basic company information from XBRL filing
    """
    name: str
    cik: str                      # Central Index Key
    ticker: Optional[str] = None
    sic: Optional[str] = None     # Standard Industrial Classification
    fiscal_year_end: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "cik": self.cik,
            "ticker": self.ticker,
            "sic": self.sic,
            "fiscal_year_end": self.fiscal_year_end,
            "address": self.address,
            "phone": self.phone
        }


@dataclass
class FilingData:
    """
    Complete XBRL filing data
    """
    company_info: CompanyInfo
    filing_date: date
    period_end_date: date
    form_type: str                # e.g., "10-K", "10-Q"
    
    # Financial statements
    income_statement: Optional[FinancialStatement] = None
    balance_sheet: Optional[FinancialStatement] = None
    cash_flow_statement: Optional[FinancialStatement] = None
    shareholders_equity: Optional[FinancialStatement] = None
    comprehensive_income: Optional[FinancialStatement] = None
    
    # Raw data
    all_facts: List[FinancialFact] = field(default_factory=list)
    taxonomy_elements: List[TaxonomyElement] = field(default_factory=list)
    
    # Validation reports (added by validation system)
    quality_report: Optional[Dict[str, Any]] = None
    calculation_report: Optional[Dict[str, Any]] = None
    
    def get_statement(self, statement_type: StatementType) -> Optional[FinancialStatement]:
        """Get a specific financial statement"""
        statement_map = {
            StatementType.INCOME_STATEMENT: self.income_statement,
            StatementType.BALANCE_SHEET: self.balance_sheet,
            StatementType.CASH_FLOW_STATEMENT: self.cash_flow_statement,
            StatementType.SHAREHOLDERS_EQUITY: self.shareholders_equity,
            StatementType.COMPREHENSIVE_INCOME: self.comprehensive_income
        }
        return statement_map.get(statement_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "company_info": self.company_info.to_dict(),
            "filing_date": self.filing_date.isoformat(),
            "period_end_date": self.period_end_date.isoformat(),
            "form_type": self.form_type,
            "income_statement": self.income_statement.to_dict() if self.income_statement else None,
            "balance_sheet": self.balance_sheet.to_dict() if self.balance_sheet else None,
            "cash_flow_statement": self.cash_flow_statement.to_dict() if self.cash_flow_statement else None,
            "shareholders_equity": self.shareholders_equity.to_dict() if self.shareholders_equity else None,
            "comprehensive_income": self.comprehensive_income.to_dict() if self.comprehensive_income else None,
            "total_facts": len(self.all_facts),
            "total_elements": len(self.taxonomy_elements)
        }


@dataclass
class FinancialRatios:
    """
    Collection of calculated financial ratios
    """
    # Profitability ratios
    gross_profit_margin: Optional[float] = None
    operating_profit_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    
    # Liquidity ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    
    # Leverage ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Efficiency ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    
    # Market ratios (if applicable)
    earnings_per_share: Optional[float] = None
    book_value_per_share: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "profitability": {
                "gross_profit_margin": self.gross_profit_margin,
                "operating_profit_margin": self.operating_profit_margin,
                "net_profit_margin": self.net_profit_margin,
                "return_on_assets": self.return_on_assets,
                "return_on_equity": self.return_on_equity
            },
            "liquidity": {
                "current_ratio": self.current_ratio,
                "quick_ratio": self.quick_ratio,
                "cash_ratio": self.cash_ratio
            },
            "leverage": {
                "debt_to_equity": self.debt_to_equity,
                "debt_to_assets": self.debt_to_assets,
                "interest_coverage": self.interest_coverage
            },
            "efficiency": {
                "asset_turnover": self.asset_turnover,
                "inventory_turnover": self.inventory_turnover,
                "receivables_turnover": self.receivables_turnover
            },
            "market": {
                "earnings_per_share": self.earnings_per_share,
                "book_value_per_share": self.book_value_per_share
            }
        }