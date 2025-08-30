"""
Tests for Financial Statement Builders
"""

import pytest
from datetime import date
from decimal import Decimal

from xbrl_financial_service.statement_builders import (
    IncomeStatementBuilder, BalanceSheetBuilder, CashFlowStatementBuilder,
    StatementBuilderFactory, StatementLineItem
)
from xbrl_financial_service.models import (
    FinancialFact, StatementType, PresentationRelationship, 
    CalculationRelationship, PeriodType
)


class TestIncomeStatementBuilder:
    """Test income statement builder"""
    
    def test_build_income_statement(self):
        """Test building income statement with proper ordering"""
        # Create sample facts
        facts = [
            FinancialFact(
                concept="us-gaap:Revenues",
                label="Total Revenues",
                value=1000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:CostOfRevenue",
                label="Cost of Revenue",
                value=600000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:GrossProfit",
                label="Gross Profit",
                value=400000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:OperatingExpenses",
                label="Operating Expenses",
                value=200000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:OperatingIncomeLoss",
                label="Operating Income",
                value=200000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:NetIncomeLoss",
                label="Net Income",
                value=150000,
                unit="USD",
                decimals=-3
            )
        ]
        
        # Create builder
        builder = IncomeStatementBuilder(facts, [], [])
        
        # Build statement
        statement = builder.build_statement("Test Company", date(2023, 12, 31))
        
        # Verify statement properties
        assert statement.statement_type == StatementType.INCOME_STATEMENT
        assert statement.company_name == "Test Company"
        assert statement.period_end == date(2023, 12, 31)
        assert len(statement.facts) > 0
        
        # Verify facts are filtered correctly
        fact_concepts = [fact.concept for fact in statement.facts]
        assert "us-gaap:Revenues" in fact_concepts
        assert "us-gaap:NetIncomeLoss" in fact_concepts
    
    def test_filter_income_statement_facts(self):
        """Test filtering facts relevant to income statement"""
        facts = [
            FinancialFact(concept="us-gaap:Revenues", label="Revenue", value=1000),
            FinancialFact(concept="us-gaap:Assets", label="Total Assets", value=5000),
            FinancialFact(concept="us-gaap:NetIncomeLoss", label="Net Income", value=100),
            FinancialFact(concept="us-gaap:Cash", label="Cash", value=500)
        ]
        
        builder = IncomeStatementBuilder(facts, [], [])
        income_facts = builder._filter_income_statement_facts()
        
        # Should include revenue and net income, exclude assets and cash
        concepts = [fact.concept for fact in income_facts]
        assert "us-gaap:Revenues" in concepts
        assert "us-gaap:NetIncomeLoss" in concepts
        assert "us-gaap:Assets" not in concepts
        assert "us-gaap:Cash" not in concepts
    
    def test_find_concepts_by_pattern(self):
        """Test finding concepts by pattern matching"""
        facts = [
            FinancialFact(concept="us-gaap:Revenues", label="Revenue", value=1000),
            FinancialFact(concept="us-gaap:RevenueFromServices", label="Service Revenue", value=500),
            FinancialFact(concept="us-gaap:CostOfRevenue", label="Cost of Revenue", value=600),
            FinancialFact(concept="us-gaap:Assets", label="Assets", value=5000)
        ]
        
        builder = IncomeStatementBuilder(facts, [], [])
        revenue_concepts = builder._find_concepts_by_pattern(['revenue'])
        
        assert len(revenue_concepts) == 3  # All revenue-related concepts
        assert "us-gaap:Revenues" in revenue_concepts
        assert "us-gaap:RevenueFromServices" in revenue_concepts
        assert "us-gaap:CostOfRevenue" in revenue_concepts
        assert "us-gaap:Assets" not in revenue_concepts


class TestBalanceSheetBuilder:
    """Test balance sheet builder"""
    
    def test_build_balance_sheet(self):
        """Test building balance sheet with proper structure"""
        # Create sample facts
        facts = [
            FinancialFact(
                concept="us-gaap:AssetsCurrent",
                label="Current Assets",
                value=2000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:Assets",
                label="Total Assets",
                value=5000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:LiabilitiesCurrent",
                label="Current Liabilities",
                value=1000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:Liabilities",
                label="Total Liabilities",
                value=3000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:StockholdersEquity",
                label="Stockholders Equity",
                value=2000000,
                unit="USD",
                decimals=-3
            )
        ]
        
        # Create builder
        builder = BalanceSheetBuilder(facts, [], [])
        
        # Build statement
        statement = builder.build_statement("Test Company", date(2023, 12, 31))
        
        # Verify statement properties
        assert statement.statement_type == StatementType.BALANCE_SHEET
        assert statement.company_name == "Test Company"
        assert statement.period_end == date(2023, 12, 31)
        assert len(statement.facts) > 0
        
        # Verify facts are filtered correctly
        fact_concepts = [fact.concept for fact in statement.facts]
        assert "us-gaap:Assets" in fact_concepts
        assert "us-gaap:StockholdersEquity" in fact_concepts
    
    def test_filter_balance_sheet_facts(self):
        """Test filtering facts relevant to balance sheet"""
        facts = [
            FinancialFact(concept="us-gaap:Assets", label="Assets", value=5000),
            FinancialFact(concept="us-gaap:Revenues", label="Revenue", value=1000),
            FinancialFact(concept="us-gaap:Liabilities", label="Liabilities", value=3000),
            FinancialFact(concept="us-gaap:NetIncomeLoss", label="Net Income", value=100)
        ]
        
        builder = BalanceSheetBuilder(facts, [], [])
        balance_facts = builder._filter_balance_sheet_facts()
        
        # Should include assets and liabilities, exclude revenue and net income
        concepts = [fact.concept for fact in balance_facts]
        assert "us-gaap:Assets" in concepts
        assert "us-gaap:Liabilities" in concepts
        assert "us-gaap:Revenues" not in concepts
        assert "us-gaap:NetIncomeLoss" not in concepts


class TestCashFlowStatementBuilder:
    """Test cash flow statement builder"""
    
    def test_build_cash_flow_statement(self):
        """Test building cash flow statement with proper sections"""
        # Create sample facts
        facts = [
            FinancialFact(
                concept="us-gaap:NetIncomeLoss",
                label="Net Income",
                value=150000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:DepreciationDepletionAndAmortization",
                label="Depreciation and Amortization",
                value=50000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:NetCashProvidedByUsedInOperatingActivities",
                label="Net Cash from Operating Activities",
                value=200000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                label="Capital Expenditures",
                value=-100000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:NetCashProvidedByUsedInInvestingActivities",
                label="Net Cash from Investing Activities",
                value=-100000,
                unit="USD",
                decimals=-3
            )
        ]
        
        # Create builder
        builder = CashFlowStatementBuilder(facts, [], [])
        
        # Build statement
        statement = builder.build_statement("Test Company", date(2023, 12, 31))
        
        # Verify statement properties
        assert statement.statement_type == StatementType.CASH_FLOW_STATEMENT
        assert statement.company_name == "Test Company"
        assert statement.period_end == date(2023, 12, 31)
        assert len(statement.facts) > 0
        
        # Verify facts are filtered correctly
        fact_concepts = [fact.concept for fact in statement.facts]
        assert "us-gaap:NetIncomeLoss" in fact_concepts
        assert "us-gaap:DepreciationDepletionAndAmortization" in fact_concepts
    
    def test_filter_cash_flow_facts(self):
        """Test filtering facts relevant to cash flow statement"""
        facts = [
            FinancialFact(concept="us-gaap:NetIncomeLoss", label="Net Income", value=100),
            FinancialFact(concept="us-gaap:DepreciationDepletionAndAmortization", label="Depreciation", value=50),
            FinancialFact(concept="us-gaap:Assets", label="Assets", value=5000),
            FinancialFact(concept="us-gaap:Revenues", label="Revenue", value=1000)
        ]
        
        builder = CashFlowStatementBuilder(facts, [], [])
        cash_flow_facts = builder._filter_cash_flow_facts()
        
        # Should include cash flow related items
        concepts = [fact.concept for fact in cash_flow_facts]
        assert "us-gaap:DepreciationDepletionAndAmortization" in concepts
        # Net income might be included as it's part of operating activities
        # Assets and revenue should not be included
        assert "us-gaap:Assets" not in concepts
        assert "us-gaap:Revenues" not in concepts


class TestStatementBuilderFactory:
    """Test statement builder factory"""
    
    def test_create_income_statement_builder(self):
        """Test creating income statement builder"""
        builder = StatementBuilderFactory.create_builder(
            StatementType.INCOME_STATEMENT, [], [], []
        )
        assert isinstance(builder, IncomeStatementBuilder)
    
    def test_create_balance_sheet_builder(self):
        """Test creating balance sheet builder"""
        builder = StatementBuilderFactory.create_builder(
            StatementType.BALANCE_SHEET, [], [], []
        )
        assert isinstance(builder, BalanceSheetBuilder)
    
    def test_create_cash_flow_builder(self):
        """Test creating cash flow statement builder"""
        builder = StatementBuilderFactory.create_builder(
            StatementType.CASH_FLOW_STATEMENT, [], [], []
        )
        assert isinstance(builder, CashFlowStatementBuilder)
    
    def test_unsupported_statement_type(self):
        """Test error for unsupported statement type"""
        with pytest.raises(ValueError, match="Unsupported statement type"):
            StatementBuilderFactory.create_builder(
                StatementType.COMPREHENSIVE_INCOME, [], [], []
            )


class TestStatementLineItem:
    """Test StatementLineItem dataclass"""
    
    def test_create_line_item(self):
        """Test creating a statement line item"""
        item = StatementLineItem(
            concept="us-gaap:Revenues",
            label="Total Revenues",
            value=1000000.0,
            order=1,
            level=0,
            is_total=False
        )
        
        assert item.concept == "us-gaap:Revenues"
        assert item.label == "Total Revenues"
        assert item.value == 1000000.0
        assert item.order == 1
        assert item.level == 0
        assert item.is_total is False
        assert item.parent is None
    
    def test_line_item_with_parent(self):
        """Test creating line item with parent"""
        item = StatementLineItem(
            concept="us-gaap:RevenueFromServices",
            label="Service Revenue",
            value=500000.0,
            order=2,
            level=1,
            parent="us-gaap:Revenues"
        )
        
        assert item.parent == "us-gaap:Revenues"
        assert item.level == 1


class TestBaseStatementBuilder:
    """Test base statement builder functionality"""
    
    def test_get_fact_value(self):
        """Test getting fact values with scaling"""
        facts = [
            FinancialFact(
                concept="us-gaap:Revenues",
                label="Revenue",
                value=1000,
                decimals=-3  # Thousands - value * 10^(-(-3)) = 1000 * 1000 = 1000000
            ),
            FinancialFact(
                concept="us-gaap:Assets",
                label="Assets",
                value=5000,
                decimals=None  # No scaling
            )
        ]
        
        builder = IncomeStatementBuilder(facts, [], [])
        
        # Test scaled value - decimals=-3 means 1000 * 10^3 = 1000000
        revenue_value = builder._get_fact_value("us-gaap:Revenues")
        assert revenue_value == 1000000.0  # 1000 * 10^3
        
        # Test unscaled value
        assets_value = builder._get_fact_value("us-gaap:Assets")
        assert assets_value == 5000.0
        
        # Test non-existent concept
        missing_value = builder._get_fact_value("us-gaap:NonExistent")
        assert missing_value is None
    
    def test_get_fact_label(self):
        """Test getting fact labels"""
        facts = [
            FinancialFact(
                concept="us-gaap:Revenues",
                label="Total Revenues",
                value=1000
            )
        ]
        
        builder = IncomeStatementBuilder(facts, [], [])
        
        # Test existing concept
        label = builder._get_fact_label("us-gaap:Revenues")
        assert label == "Total Revenues"
        
        # Test non-existent concept (should return concept name without prefix)
        missing_label = builder._get_fact_label("us-gaap:NonExistent")
        assert missing_label == "NonExistent"
    
    def test_is_total_concept(self):
        """Test identifying total/subtotal concepts"""
        builder = IncomeStatementBuilder([], [], [])
        
        # Test total concepts
        assert builder._is_total_concept("us-gaap:TotalRevenues") is True
        assert builder._is_total_concept("us-gaap:GrossProfit") is True
        assert builder._is_total_concept("us-gaap:NetIncomeLoss") is True
        assert builder._is_total_concept("us-gaap:TotalAssets") is True
        
        # Test non-total concepts
        assert builder._is_total_concept("us-gaap:CashAndCashEquivalents") is False
        assert builder._is_total_concept("us-gaap:AccountsReceivable") is False


if __name__ == "__main__":
    pytest.main([__file__])