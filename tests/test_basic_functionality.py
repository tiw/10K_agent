"""
Basic functionality tests for XBRL Financial Service
"""

import pytest
from datetime import date
from pathlib import Path

from xbrl_financial_service.models import (
    FinancialFact, FinancialStatement, CompanyInfo, FilingData,
    StatementType, PeriodType, FinancialRatios
)
from xbrl_financial_service.financial_service import FinancialService
from xbrl_financial_service.config import Config


class TestDataModels:
    """Test data model functionality"""
    
    def test_financial_fact_creation(self):
        """Test FinancialFact creation and methods"""
        fact = FinancialFact(
            concept="us-gaap:Revenue",
            label="Revenue",
            value=1000000,
            unit="USD",
            period="2024-09-28",
            decimals=-3  # Thousands
        )
        
        assert fact.concept == "us-gaap:Revenue"
        assert fact.label == "Revenue"
        assert fact.value == 1000000
        assert fact.get_scaled_value() == 1000000000  # Scaled by decimals
    
    def test_financial_fact_to_dict(self):
        """Test FinancialFact serialization"""
        fact = FinancialFact(
            concept="us-gaap:Assets",
            label="Total Assets",
            value=500000,
            unit="USD"
        )
        
        fact_dict = fact.to_dict()
        assert fact_dict["concept"] == "us-gaap:Assets"
        assert fact_dict["label"] == "Total Assets"
        assert fact_dict["value"] == 500000
    
    def test_company_info_creation(self):
        """Test CompanyInfo creation"""
        company = CompanyInfo(
            name="Apple Inc.",
            cik="0000320193",
            ticker="AAPL"
        )
        
        assert company.name == "Apple Inc."
        assert company.cik == "0000320193"
        assert company.ticker == "AAPL"
    
    def test_financial_statement_creation(self):
        """Test FinancialStatement creation"""
        facts = [
            FinancialFact(
                concept="us-gaap:Revenue",
                label="Revenue",
                value=100000,
                unit="USD"
            ),
            FinancialFact(
                concept="us-gaap:NetIncomeLoss",
                label="Net Income",
                value=25000,
                unit="USD"
            )
        ]
        
        statement = FinancialStatement(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test Company",
            period_end=date(2024, 9, 28),
            facts=facts
        )
        
        assert statement.statement_type == StatementType.INCOME_STATEMENT
        assert len(statement.facts) == 2
        
        # Test fact lookup
        revenue_fact = statement.get_fact_by_concept("Revenue")
        assert revenue_fact is not None
        assert revenue_fact.value == 100000


class TestFinancialService:
    """Test FinancialService functionality"""
    
    def test_financial_service_creation(self):
        """Test FinancialService creation"""
        service = FinancialService()
        assert service.config is not None
        assert service.db_manager is not None
    
    def test_financial_service_with_config(self):
        """Test FinancialService with custom config"""
        config = Config()
        config.cache_ttl = 7200
        
        service = FinancialService(config=config)
        assert service.config.cache_ttl == 7200
    
    def test_search_facts_no_data(self):
        """Test search_facts with no data loaded"""
        service = FinancialService()
        
        with pytest.raises(Exception):  # Should raise QueryError
            service.search_facts("revenue")
    
    def test_get_company_info_no_data(self):
        """Test get_company_info with no data"""
        service = FinancialService()
        company_info = service.get_company_info()
        assert company_info is None


class TestConfig:
    """Test configuration functionality"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.database_path == "financial_data.db"
        assert config.cache_ttl == 3600
        assert config.mcp_port == 8000
        assert config.log_level == "INFO"
        assert "us-gaap" in config.supported_taxonomies
    
    def test_config_modification(self):
        """Test configuration modification"""
        config = Config()
        config.mcp_port = 9000
        config.log_level = "DEBUG"
        
        assert config.mcp_port == 9000
        assert config.log_level == "DEBUG"


class TestFinancialRatios:
    """Test financial ratios functionality"""
    
    def test_financial_ratios_creation(self):
        """Test FinancialRatios creation"""
        ratios = FinancialRatios()
        
        # Test default values
        assert ratios.net_profit_margin is None
        assert ratios.current_ratio is None
        assert ratios.debt_to_equity is None
    
    def test_financial_ratios_with_values(self):
        """Test FinancialRatios with calculated values"""
        ratios = FinancialRatios(
            net_profit_margin=0.25,
            current_ratio=2.5,
            debt_to_equity=0.3
        )
        
        assert ratios.net_profit_margin == 0.25
        assert ratios.current_ratio == 2.5
        assert ratios.debt_to_equity == 0.3
    
    def test_financial_ratios_to_dict(self):
        """Test FinancialRatios serialization"""
        ratios = FinancialRatios(
            net_profit_margin=0.15,
            return_on_assets=0.08
        )
        
        ratios_dict = ratios.to_dict()
        assert ratios_dict["profitability"]["net_profit_margin"] == 0.15
        assert ratios_dict["profitability"]["return_on_assets"] == 0.08
        assert ratios_dict["liquidity"]["current_ratio"] is None


if __name__ == "__main__":
    pytest.main([__file__])