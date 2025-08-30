"""
Integration tests for statement builders with financial service
"""

import pytest
from datetime import date

from xbrl_financial_service.financial_service import FinancialService
from xbrl_financial_service.models import (
    FilingData, CompanyInfo, FinancialFact, StatementType
)


class TestStatementIntegration:
    """Test integration of statement builders with financial service"""
    
    def test_build_income_statement_integration(self):
        """Test building income statement through financial service"""
        # Create sample filing data
        company_info = CompanyInfo(
            name="Test Company Inc.",
            cik="0001234567"
        )
        
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
                concept="us-gaap:NetIncomeLoss",
                label="Net Income",
                value=150000,
                unit="USD",
                decimals=-3
            )
        ]
        
        filing_data = FilingData(
            company_info=company_info,
            filing_date=date(2024, 1, 15),
            period_end_date=date(2023, 12, 31),
            form_type="10-K",
            all_facts=facts
        )
        
        # Create financial service and load data
        service = FinancialService()
        service.load_filing_data(filing_data)
        
        # Build income statement
        income_statement = service.build_financial_statement(StatementType.INCOME_STATEMENT)
        
        # Verify statement was built
        assert income_statement is not None
        assert income_statement.statement_type == StatementType.INCOME_STATEMENT
        assert income_statement.company_name == "Test Company Inc."
        assert income_statement.period_end == date(2023, 12, 31)
        assert len(income_statement.facts) > 0
        
        # Verify facts are included
        fact_concepts = [fact.concept for fact in income_statement.facts]
        assert "us-gaap:Revenues" in fact_concepts
        assert "us-gaap:NetIncomeLoss" in fact_concepts
    
    def test_build_balance_sheet_integration(self):
        """Test building balance sheet through financial service"""
        # Create sample filing data
        company_info = CompanyInfo(
            name="Test Company Inc.",
            cik="0001234567"
        )
        
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
                concept="us-gaap:StockholdersEquity",
                label="Stockholders Equity",
                value=2000000,
                unit="USD",
                decimals=-3
            )
        ]
        
        filing_data = FilingData(
            company_info=company_info,
            filing_date=date(2024, 1, 15),
            period_end_date=date(2023, 12, 31),
            form_type="10-K",
            all_facts=facts
        )
        
        # Create financial service and load data
        service = FinancialService()
        service.load_filing_data(filing_data)
        
        # Build balance sheet
        balance_sheet = service.build_financial_statement(StatementType.BALANCE_SHEET)
        
        # Verify statement was built
        assert balance_sheet is not None
        assert balance_sheet.statement_type == StatementType.BALANCE_SHEET
        assert balance_sheet.company_name == "Test Company Inc."
        assert balance_sheet.period_end == date(2023, 12, 31)
        assert len(balance_sheet.facts) > 0
        
        # Verify facts are included
        fact_concepts = [fact.concept for fact in balance_sheet.facts]
        assert "us-gaap:Assets" in fact_concepts
        assert "us-gaap:StockholdersEquity" in fact_concepts
    
    def test_rebuild_all_statements(self):
        """Test rebuilding all statements"""
        # Create sample filing data with mixed facts
        company_info = CompanyInfo(
            name="Test Company Inc.",
            cik="0001234567"
        )
        
        facts = [
            # Income statement facts
            FinancialFact(
                concept="us-gaap:Revenues",
                label="Total Revenues",
                value=1000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:NetIncomeLoss",
                label="Net Income",
                value=150000,
                unit="USD",
                decimals=-3
            ),
            # Balance sheet facts
            FinancialFact(
                concept="us-gaap:Assets",
                label="Total Assets",
                value=5000000,
                unit="USD",
                decimals=-3
            ),
            FinancialFact(
                concept="us-gaap:StockholdersEquity",
                label="Stockholders Equity",
                value=2000000,
                unit="USD",
                decimals=-3
            ),
            # Cash flow facts
            FinancialFact(
                concept="us-gaap:NetCashProvidedByUsedInOperatingActivities",
                label="Net Cash from Operating Activities",
                value=200000,
                unit="USD",
                decimals=-3
            )
        ]
        
        filing_data = FilingData(
            company_info=company_info,
            filing_date=date(2024, 1, 15),
            period_end_date=date(2023, 12, 31),
            form_type="10-K",
            all_facts=facts
        )
        
        # Create financial service and load data
        service = FinancialService()
        service.load_filing_data(filing_data)
        
        # Rebuild all statements
        service.rebuild_all_statements()
        
        # Verify all statements were built
        assert service.filing_data.income_statement is not None
        assert service.filing_data.balance_sheet is not None
        assert service.filing_data.cash_flow_statement is not None
        
        # Verify statement types
        assert service.filing_data.income_statement.statement_type == StatementType.INCOME_STATEMENT
        assert service.filing_data.balance_sheet.statement_type == StatementType.BALANCE_SHEET
        assert service.filing_data.cash_flow_statement.statement_type == StatementType.CASH_FLOW_STATEMENT
    
    def test_build_statement_no_data(self):
        """Test building statement with no filing data"""
        service = FinancialService()
        
        with pytest.raises(Exception):  # Should raise QueryError
            service.build_financial_statement(StatementType.INCOME_STATEMENT)
    
    def test_build_statement_empty_facts(self):
        """Test building statement with empty facts"""
        company_info = CompanyInfo(
            name="Test Company Inc.",
            cik="0001234567"
        )
        
        filing_data = FilingData(
            company_info=company_info,
            filing_date=date(2024, 1, 15),
            period_end_date=date(2023, 12, 31),
            form_type="10-K",
            all_facts=[]  # No facts
        )
        
        service = FinancialService()
        service.load_filing_data(filing_data)
        
        # Should still build statement but with no facts
        income_statement = service.build_financial_statement(StatementType.INCOME_STATEMENT)
        
        assert income_statement is not None
        assert len(income_statement.facts) == 0


if __name__ == "__main__":
    pytest.main([__file__])