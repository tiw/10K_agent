"""
Financial Statement Builders

Constructs properly structured financial statements from raw XBRL facts.
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import date
from dataclasses import dataclass

from .models import (
    FinancialStatement, FinancialFact, StatementType, 
    PresentationRelationship, CalculationRelationship
)
from .utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StatementLineItem:
    """Represents a line item in a financial statement"""
    concept: str
    label: str
    value: Optional[float]
    order: int
    level: int = 0  # Indentation level
    is_total: bool = False
    parent: Optional[str] = None


class BaseStatementBuilder:
    """Base class for financial statement builders"""
    
    def __init__(self, facts: List[FinancialFact], 
                 presentation_relationships: List[PresentationRelationship],
                 calculation_relationships: List[CalculationRelationship]):
        self.facts = facts
        self.presentation_relationships = presentation_relationships
        self.calculation_relationships = calculation_relationships
        self.facts_by_concept = {fact.concept: fact for fact in facts}
    
    def _get_fact_value(self, concept: str) -> Optional[float]:
        """Get numeric value for a concept"""
        fact = self.facts_by_concept.get(concept)
        if not fact:
            return None
        
        if isinstance(fact.value, (int, float)):
            # Apply scaling if decimals are specified
            # Use the same scaling logic as FinancialFact.get_scaled_value()
            if fact.decimals is not None:
                return float(fact.value) * (10 ** (-fact.decimals))
            return float(fact.value)
        
        return None
    
    def _get_fact_label(self, concept: str) -> str:
        """Get label for a concept"""
        fact = self.facts_by_concept.get(concept)
        return fact.label if fact else concept.split(':')[-1]
    
    def _build_hierarchy(self, root_concepts: List[str], role: Optional[str] = None) -> List[StatementLineItem]:
        """Build hierarchical structure from presentation relationships"""
        line_items = []
        processed = set()
        
        for root_concept in root_concepts:
            if root_concept in processed:
                continue
            self._add_concept_hierarchy(root_concept, line_items, processed, 0, role)
        
        return sorted(line_items, key=lambda x: x.order)
    
    def _add_concept_hierarchy(self, concept: str, line_items: List[StatementLineItem], 
                              processed: Set[str], level: int, role: Optional[str] = None):
        """Recursively add concept and its children to line items"""
        if concept in processed:
            return
        
        processed.add(concept)
        
        # Find children of this concept
        children = []
        for rel in self.presentation_relationships:
            if (rel.parent == concept and 
                (role is None or rel.role == role)):
                children.append((rel.child, rel.order))
        
        # Sort children by order
        children.sort(key=lambda x: x[1])
        
        # Add current concept
        value = self._get_fact_value(concept)
        label = self._get_fact_label(concept)
        
        # Determine if this is a total/subtotal
        is_total = self._is_total_concept(concept)
        
        line_item = StatementLineItem(
            concept=concept,
            label=label,
            value=value,
            order=len(line_items),
            level=level,
            is_total=is_total
        )
        line_items.append(line_item)
        
        # Add children
        for child_concept, _ in children:
            self._add_concept_hierarchy(child_concept, line_items, processed, level + 1, role)
    
    def _is_total_concept(self, concept: str) -> bool:
        """Determine if a concept represents a total or subtotal"""
        total_indicators = [
            'total', 'gross', 'net', 'income', 'loss', 'comprehensive',
            'assets', 'liabilities', 'equity', 'stockholders'
        ]
        concept_lower = concept.lower()
        return any(indicator in concept_lower for indicator in total_indicators)


class IncomeStatementBuilder(BaseStatementBuilder):
    """Builder for income statements with proper line item ordering"""
    
    # Standard income statement concepts in order
    INCOME_STATEMENT_CONCEPTS = [
        'us-gaap:Revenues',
        'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
        'us-gaap:CostOfRevenue',
        'us-gaap:CostOfGoodsAndServicesSold',
        'us-gaap:GrossProfit',
        'us-gaap:OperatingExpenses',
        'us-gaap:ResearchAndDevelopmentExpense',
        'us-gaap:SellingGeneralAndAdministrativeExpense',
        'us-gaap:OperatingIncomeLoss',
        'us-gaap:InterestExpense',
        'us-gaap:InterestIncome',
        'us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
        'us-gaap:IncomeTaxExpenseBenefit',
        'us-gaap:NetIncomeLoss',
        'us-gaap:EarningsPerShareBasic',
        'us-gaap:EarningsPerShareDiluted'
    ]
    
    def build_statement(self, company_name: str, period_end: date) -> FinancialStatement:
        """Build income statement with proper ordering"""
        logger.info("Building income statement")
        
        # Find relevant facts for income statement
        income_facts = self._filter_income_statement_facts()
        
        # Build line items with proper hierarchy
        line_items = self._build_income_statement_structure()
        
        # Create financial statement
        statement = FinancialStatement(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name=company_name,
            period_end=period_end,
            facts=income_facts,
            presentation_order=self._create_presentation_order(line_items)
        )
        
        logger.info(f"Built income statement with {len(income_facts)} facts")
        return statement
    
    def _filter_income_statement_facts(self) -> List[FinancialFact]:
        """Filter facts relevant to income statement"""
        income_keywords = [
            'revenue', 'income', 'expense', 'cost', 'profit', 'loss',
            'earnings', 'tax', 'interest', 'operating', 'gross', 'net'
        ]
        
        income_facts = []
        for fact in self.facts:
            concept_lower = fact.concept.lower()
            label_lower = fact.label.lower()
            
            if any(keyword in concept_lower or keyword in label_lower 
                   for keyword in income_keywords):
                income_facts.append(fact)
        
        return income_facts
    
    def _build_income_statement_structure(self) -> List[StatementLineItem]:
        """Build income statement structure with standard ordering"""
        line_items = []
        order = 0
        
        # Revenue section
        revenue_concepts = self._find_concepts_by_pattern(['revenue', 'sales'])
        for concept in revenue_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0
                ))
                order += 1
        
        # Cost of revenue
        cost_concepts = self._find_concepts_by_pattern(['cost', 'cogs'])
        for concept in cost_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0
                ))
                order += 1
        
        # Gross profit
        gross_profit_concepts = self._find_concepts_by_pattern(['grossprofit'])
        for concept in gross_profit_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
        
        # Operating expenses
        expense_concepts = self._find_concepts_by_pattern(['expense', 'operating'])
        for concept in expense_concepts:
            if 'interest' not in concept.lower():  # Exclude interest expense
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=1
                    ))
                    order += 1
        
        # Operating income
        operating_income_concepts = self._find_concepts_by_pattern(['operatingincome'])
        for concept in operating_income_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
        
        # Interest and other income/expense
        interest_concepts = self._find_concepts_by_pattern(['interest'])
        for concept in interest_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=1
                ))
                order += 1
        
        # Income before taxes
        pretax_concepts = self._find_concepts_by_pattern(['incomebeforetax', 'pretax'])
        for concept in pretax_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
        
        # Tax expense
        tax_concepts = self._find_concepts_by_pattern(['tax', 'incometax'])
        for concept in tax_concepts:
            if 'expense' in concept.lower() or 'benefit' in concept.lower():
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=1
                    ))
                    order += 1
        
        # Net income
        net_income_concepts = self._find_concepts_by_pattern(['netincome', 'netloss'])
        for concept in net_income_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
        
        # Earnings per share
        eps_concepts = self._find_concepts_by_pattern(['earningspershare'])
        for concept in eps_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=1
                ))
                order += 1
        
        return line_items
    
    def _find_concepts_by_pattern(self, patterns: List[str]) -> List[str]:
        """Find concepts matching patterns"""
        matching_concepts = []
        for fact in self.facts:
            concept_lower = fact.concept.lower()
            if any(pattern in concept_lower for pattern in patterns):
                matching_concepts.append(fact.concept)
        return list(set(matching_concepts))  # Remove duplicates
    
    def _create_presentation_order(self, line_items: List[StatementLineItem]) -> List[PresentationRelationship]:
        """Create presentation relationships from line items"""
        relationships = []
        for i, item in enumerate(line_items):
            # Find parent (previous item with lower level)
            parent = None
            for j in range(i - 1, -1, -1):
                if line_items[j].level < item.level:
                    parent = line_items[j].concept
                    break
            
            if parent:
                relationships.append(PresentationRelationship(
                    parent=parent,
                    child=item.concept,
                    order=item.order
                ))
        
        return relationships


class BalanceSheetBuilder(BaseStatementBuilder):
    """Builder for balance sheets with asset/liability/equity structure"""
    
    def build_statement(self, company_name: str, period_end: date) -> FinancialStatement:
        """Build balance sheet with proper structure"""
        logger.info("Building balance sheet")
        
        # Find relevant facts for balance sheet
        balance_sheet_facts = self._filter_balance_sheet_facts()
        
        # Build line items with proper hierarchy
        line_items = self._build_balance_sheet_structure()
        
        # Create financial statement
        statement = FinancialStatement(
            statement_type=StatementType.BALANCE_SHEET,
            company_name=company_name,
            period_end=period_end,
            facts=balance_sheet_facts,
            presentation_order=self._create_presentation_order(line_items)
        )
        
        logger.info(f"Built balance sheet with {len(balance_sheet_facts)} facts")
        return statement
    
    def _filter_balance_sheet_facts(self) -> List[FinancialFact]:
        """Filter facts relevant to balance sheet"""
        balance_sheet_keywords = [
            'assets', 'liabilities', 'equity', 'cash', 'receivables',
            'inventory', 'property', 'debt', 'payable', 'stockholders'
        ]
        
        balance_sheet_facts = []
        for fact in self.facts:
            concept_lower = fact.concept.lower()
            label_lower = fact.label.lower()
            
            if any(keyword in concept_lower or keyword in label_lower 
                   for keyword in balance_sheet_keywords):
                balance_sheet_facts.append(fact)
        
        return balance_sheet_facts
    
    def _build_balance_sheet_structure(self) -> List[StatementLineItem]:
        """Build balance sheet structure with assets, liabilities, and equity"""
        line_items = []
        order = 0
        
        # ASSETS SECTION
        line_items.append(StatementLineItem(
            concept="ASSETS_HEADER",
            label="ASSETS",
            value=None,
            order=order,
            level=0,
            is_total=True
        ))
        order += 1
        
        # Current assets
        current_asset_concepts = self._find_concepts_by_pattern(['currentassets', 'cash', 'receivables', 'inventory'])
        for concept in current_asset_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                level = 2 if 'current' not in concept.lower() else 1
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=level
                ))
                order += 1
        
        # Non-current assets
        noncurrent_asset_concepts = self._find_concepts_by_pattern(['property', 'equipment', 'intangible', 'goodwill'])
        for concept in noncurrent_asset_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=1
                ))
                order += 1
        
        # Total assets
        total_assets_concepts = self._find_concepts_by_pattern(['totalassets', 'assets'])
        for concept in total_assets_concepts:
            if 'current' not in concept.lower():
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=0,
                        is_total=True
                    ))
                    order += 1
                    break
        
        # LIABILITIES SECTION
        line_items.append(StatementLineItem(
            concept="LIABILITIES_HEADER",
            label="LIABILITIES AND STOCKHOLDERS' EQUITY",
            value=None,
            order=order,
            level=0,
            is_total=True
        ))
        order += 1
        
        # Current liabilities
        current_liability_concepts = self._find_concepts_by_pattern(['currentliabilities', 'payable', 'accrued'])
        for concept in current_liability_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                level = 2 if 'current' not in concept.lower() else 1
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=level
                ))
                order += 1
        
        # Non-current liabilities
        noncurrent_liability_concepts = self._find_concepts_by_pattern(['longtermdebt', 'noncurrent'])
        for concept in noncurrent_liability_concepts:
            if 'liability' in concept.lower() or 'debt' in concept.lower():
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=1
                    ))
                    order += 1
        
        # Total liabilities
        total_liabilities_concepts = self._find_concepts_by_pattern(['totalliabilities', 'liabilities'])
        for concept in total_liabilities_concepts:
            if 'current' not in concept.lower():
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=0,
                        is_total=True
                    ))
                    order += 1
                    break
        
        # EQUITY SECTION
        equity_concepts = self._find_concepts_by_pattern(['stockholdersequity', 'equity', 'retainedearnings', 'commonstock'])
        for concept in equity_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                level = 0 if 'total' in concept.lower() or 'stockholders' in concept.lower() else 1
                is_total = 'total' in concept.lower() or 'stockholders' in concept.lower()
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=level,
                    is_total=is_total
                ))
                order += 1
        
        return line_items
    
    def _find_concepts_by_pattern(self, patterns: List[str]) -> List[str]:
        """Find concepts matching patterns"""
        matching_concepts = []
        for fact in self.facts:
            concept_lower = fact.concept.lower()
            if any(pattern in concept_lower for pattern in patterns):
                matching_concepts.append(fact.concept)
        return list(set(matching_concepts))  # Remove duplicates
    
    def _create_presentation_order(self, line_items: List[StatementLineItem]) -> List[PresentationRelationship]:
        """Create presentation relationships from line items"""
        relationships = []
        for i, item in enumerate(line_items):
            # Find parent (previous item with lower level)
            parent = None
            for j in range(i - 1, -1, -1):
                if line_items[j].level < item.level:
                    parent = line_items[j].concept
                    break
            
            if parent and not parent.endswith("_HEADER"):
                relationships.append(PresentationRelationship(
                    parent=parent,
                    child=item.concept,
                    order=item.order
                ))
        
        return relationships


class CashFlowStatementBuilder(BaseStatementBuilder):
    """Builder for cash flow statements with operating/investing/financing sections"""
    
    def build_statement(self, company_name: str, period_end: date) -> FinancialStatement:
        """Build cash flow statement with proper sections"""
        logger.info("Building cash flow statement")
        
        # Find relevant facts for cash flow statement
        cash_flow_facts = self._filter_cash_flow_facts()
        
        # Build line items with proper hierarchy
        line_items = self._build_cash_flow_structure()
        
        # Create financial statement
        statement = FinancialStatement(
            statement_type=StatementType.CASH_FLOW_STATEMENT,
            company_name=company_name,
            period_end=period_end,
            facts=cash_flow_facts,
            presentation_order=self._create_presentation_order(line_items)
        )
        
        logger.info(f"Built cash flow statement with {len(cash_flow_facts)} facts")
        return statement
    
    def _filter_cash_flow_facts(self) -> List[FinancialFact]:
        """Filter facts relevant to cash flow statement"""
        cash_flow_keywords = [
            'cash', 'operating', 'investing', 'financing', 'depreciation',
            'amortization', 'receivables', 'inventory', 'payables', 'capex',
            'netincome', 'netloss'  # Include net income as starting point
        ]
        
        cash_flow_facts = []
        for fact in self.facts:
            concept_lower = fact.concept.lower()
            label_lower = fact.label.lower()
            
            if any(keyword in concept_lower or keyword in label_lower 
                   for keyword in cash_flow_keywords):
                cash_flow_facts.append(fact)
        
        return cash_flow_facts
    
    def _build_cash_flow_structure(self) -> List[StatementLineItem]:
        """Build cash flow statement structure with three main sections"""
        line_items = []
        order = 0
        
        # OPERATING ACTIVITIES SECTION
        line_items.append(StatementLineItem(
            concept="OPERATING_HEADER",
            label="CASH FLOWS FROM OPERATING ACTIVITIES",
            value=None,
            order=order,
            level=0,
            is_total=True
        ))
        order += 1
        
        # Net income (starting point)
        net_income_concepts = self._find_concepts_by_pattern(['netincome', 'netloss'])
        for concept in net_income_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=1
                ))
                order += 1
                break
        
        # Adjustments to reconcile net income
        adjustment_concepts = self._find_concepts_by_pattern(['depreciation', 'amortization'])
        for concept in adjustment_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=1
                ))
                order += 1
        
        # Changes in working capital
        working_capital_concepts = self._find_concepts_by_pattern(['receivables', 'inventory', 'payables'])
        for concept in working_capital_concepts:
            if 'change' in concept.lower() or 'increase' in concept.lower() or 'decrease' in concept.lower():
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=1
                    ))
                    order += 1
        
        # Net cash from operating activities
        operating_cash_concepts = self._find_concepts_by_pattern(['netcashprovidedbyoperating', 'operatingactivities'])
        for concept in operating_cash_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
                break
        
        # INVESTING ACTIVITIES SECTION
        line_items.append(StatementLineItem(
            concept="INVESTING_HEADER",
            label="CASH FLOWS FROM INVESTING ACTIVITIES",
            value=None,
            order=order,
            level=0,
            is_total=True
        ))
        order += 1
        
        # Capital expenditures and investments
        investing_concepts = self._find_concepts_by_pattern(['capitalexpenditure', 'investment', 'acquisition', 'disposal'])
        for concept in investing_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=1
                ))
                order += 1
        
        # Net cash from investing activities
        investing_cash_concepts = self._find_concepts_by_pattern(['netcashprovidedbyinvesting', 'investingactivities'])
        for concept in investing_cash_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
                break
        
        # FINANCING ACTIVITIES SECTION
        line_items.append(StatementLineItem(
            concept="FINANCING_HEADER",
            label="CASH FLOWS FROM FINANCING ACTIVITIES",
            value=None,
            order=order,
            level=0,
            is_total=True
        ))
        order += 1
        
        # Debt and equity transactions
        financing_concepts = self._find_concepts_by_pattern(['debt', 'borrowing', 'repayment', 'dividend', 'stock'])
        for concept in financing_concepts:
            if any(term in concept.lower() for term in ['proceeds', 'repayment', 'issuance', 'payment']):
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=1
                    ))
                    order += 1
        
        # Net cash from financing activities
        financing_cash_concepts = self._find_concepts_by_pattern(['netcashprovidedbyfinancing', 'financingactivities'])
        for concept in financing_cash_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
                break
        
        # Net change in cash
        cash_change_concepts = self._find_concepts_by_pattern(['netchangeincash', 'cashchange'])
        for concept in cash_change_concepts:
            value = self._get_fact_value(concept)
            if value is not None:
                line_items.append(StatementLineItem(
                    concept=concept,
                    label=self._get_fact_label(concept),
                    value=value,
                    order=order,
                    level=0,
                    is_total=True
                ))
                order += 1
                break
        
        # Cash at beginning and end of period
        cash_balance_concepts = self._find_concepts_by_pattern(['cashandcashequivalents'])
        for concept in cash_balance_concepts:
            if 'beginning' in concept.lower() or 'end' in concept.lower():
                value = self._get_fact_value(concept)
                if value is not None:
                    line_items.append(StatementLineItem(
                        concept=concept,
                        label=self._get_fact_label(concept),
                        value=value,
                        order=order,
                        level=1
                    ))
                    order += 1
        
        return line_items
    
    def _find_concepts_by_pattern(self, patterns: List[str]) -> List[str]:
        """Find concepts matching patterns"""
        matching_concepts = []
        for fact in self.facts:
            concept_lower = fact.concept.lower()
            if any(pattern in concept_lower for pattern in patterns):
                matching_concepts.append(fact.concept)
        return list(set(matching_concepts))  # Remove duplicates
    
    def _create_presentation_order(self, line_items: List[StatementLineItem]) -> List[PresentationRelationship]:
        """Create presentation relationships from line items"""
        relationships = []
        for i, item in enumerate(line_items):
            # Find parent (previous item with lower level)
            parent = None
            for j in range(i - 1, -1, -1):
                if line_items[j].level < item.level:
                    parent = line_items[j].concept
                    break
            
            if parent and not parent.endswith("_HEADER"):
                relationships.append(PresentationRelationship(
                    parent=parent,
                    child=item.concept,
                    order=item.order
                ))
        
        return relationships


class StatementBuilderFactory:
    """Factory for creating statement builders"""
    
    @staticmethod
    def create_builder(statement_type: StatementType, 
                      facts: List[FinancialFact],
                      presentation_relationships: List[PresentationRelationship],
                      calculation_relationships: List[CalculationRelationship]) -> BaseStatementBuilder:
        """Create appropriate builder for statement type"""
        
        if statement_type == StatementType.INCOME_STATEMENT:
            return IncomeStatementBuilder(facts, presentation_relationships, calculation_relationships)
        elif statement_type == StatementType.BALANCE_SHEET:
            return BalanceSheetBuilder(facts, presentation_relationships, calculation_relationships)
        elif statement_type == StatementType.CASH_FLOW_STATEMENT:
            return CashFlowStatementBuilder(facts, presentation_relationships, calculation_relationships)
        else:
            raise ValueError(f"Unsupported statement type: {statement_type}")