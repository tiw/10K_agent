"""
Tests for the Financial Metrics Calculator
"""

import pytest
from datetime import date
from decimal import Decimal

from xbrl_financial_service.models import (
    FilingData, CompanyInfo, FinancialFact, PeriodType
)
from xbrl_financial_service.analysis.metrics_calculator import (
    MetricsCalculator, MetricDefinition, MetricResult, TrendMetric
)


@pytest.fixture
def sample_filing_data():
    """Create sample filing data for testing"""
    company_info = CompanyInfo(
        name="Test Company Inc.",
        cik="0001234567",
        ticker="TEST"
    )
    
    # Create sample financial facts
    facts = [
        # Revenue
        FinancialFact(
            concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            label="Revenue",
            value=1000000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.DURATION,
            period_end=date(2023, 12, 31),
            decimals=-3  # Value in thousands
        ),
        
        # Cost of Sales
        FinancialFact(
            concept="us-gaap:CostOfGoodsAndServicesSold",
            label="Cost of Sales",
            value=600000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.DURATION,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Operating Income
        FinancialFact(
            concept="us-gaap:OperatingIncomeLoss",
            label="Operating Income",
            value=250000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.DURATION,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Net Income
        FinancialFact(
            concept="us-gaap:NetIncomeLoss",
            label="Net Income",
            value=180000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.DURATION,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Total Assets
        FinancialFact(
            concept="us-gaap:Assets",
            label="Total Assets",
            value=2000000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Current Assets
        FinancialFact(
            concept="us-gaap:AssetsCurrent",
            label="Current Assets",
            value=800000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Current Liabilities
        FinancialFact(
            concept="us-gaap:LiabilitiesCurrent",
            label="Current Liabilities",
            value=400000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Shareholders' Equity
        FinancialFact(
            concept="us-gaap:StockholdersEquity",
            label="Shareholders' Equity",
            value=1200000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Long-term Debt
        FinancialFact(
            concept="us-gaap:LongTermDebtNoncurrent",
            label="Long-term Debt",
            value=400000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Cash
        FinancialFact(
            concept="us-gaap:CashAndCashEquivalentsAtCarryingValue",
            label="Cash and Cash Equivalents",
            value=200000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Interest Expense
        FinancialFact(
            concept="us-gaap:InterestExpense",
            label="Interest Expense",
            value=25000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.DURATION,
            period_end=date(2023, 12, 31),
            decimals=-3
        )
    ]
    
    return FilingData(
        company_info=company_info,
        filing_date=date(2024, 3, 15),
        period_end_date=date(2023, 12, 31),
        form_type="10-K",
        all_facts=facts
    )


def test_metrics_calculator_initialization(sample_filing_data):
    """Test metrics calculator initialization"""
    calculator = MetricsCalculator(sample_filing_data)
    
    assert calculator.filing_data == sample_filing_data
    assert len(calculator.custom_metrics) > 0  # Should have standard metrics
    assert 'gross_profit_margin' in calculator.custom_metrics
    assert 'return_on_equity' in calculator.custom_metrics


def test_calculate_profitability_metrics(sample_filing_data):
    """Test calculation of profitability metrics"""
    calculator = MetricsCalculator(sample_filing_data)
    
    # Test gross profit margin
    result = calculator.calculate_metric('gross_profit_margin')
    assert result.value is not None
    assert abs(result.value - 40.0) < 0.1  # (1000-600)/1000 * 100 = 40%
    assert result.unit == "percent"
    assert result.category == "profitability"
    
    # Test operating profit margin
    result = calculator.calculate_metric('operating_profit_margin')
    assert result.value is not None
    assert abs(result.value - 25.0) < 0.1  # 250/1000 * 100 = 25%
    
    # Test net profit margin
    result = calculator.calculate_metric('net_profit_margin')
    assert result.value is not None
    assert abs(result.value - 18.0) < 0.1  # 180/1000 * 100 = 18%
    
    # Test ROA
    result = calculator.calculate_metric('return_on_assets')
    assert result.value is not None
    assert abs(result.value - 9.0) < 0.1  # 180/2000 * 100 = 9%
    
    # Test ROE
    result = calculator.calculate_metric('return_on_equity')
    assert result.value is not None
    assert abs(result.value - 15.0) < 0.1  # 180/1200 * 100 = 15%


def test_calculate_liquidity_metrics(sample_filing_data):
    """Test calculation of liquidity metrics"""
    calculator = MetricsCalculator(sample_filing_data)
    
    # Test current ratio
    result = calculator.calculate_metric('current_ratio')
    assert result.value is not None
    assert abs(result.value - 2.0) < 0.1  # 800/400 = 2.0
    assert result.unit == "ratio"
    assert result.category == "liquidity"
    
    # Test cash ratio
    result = calculator.calculate_metric('cash_ratio')
    assert result.value is not None
    assert abs(result.value - 0.5) < 0.1  # 200/400 = 0.5


def test_calculate_leverage_metrics(sample_filing_data):
    """Test calculation of leverage metrics"""
    calculator = MetricsCalculator(sample_filing_data)
    
    # Test debt to equity
    result = calculator.calculate_metric('debt_to_equity')
    assert result.value is not None
    assert abs(result.value - 0.333) < 0.01  # 400/1200 = 0.333
    assert result.category == "leverage"
    
    # Test debt to assets
    result = calculator.calculate_metric('debt_to_assets')
    assert result.value is not None
    assert abs(result.value - 20.0) < 0.1  # 400/2000 * 100 = 20%
    
    # Test interest coverage
    result = calculator.calculate_metric('interest_coverage')
    assert result.value is not None
    assert abs(result.value - 10.0) < 0.1  # 250/25 = 10.0


def test_calculate_efficiency_metrics(sample_filing_data):
    """Test calculation of efficiency metrics"""
    calculator = MetricsCalculator(sample_filing_data)
    
    # Test asset turnover
    result = calculator.calculate_metric('asset_turnover')
    assert result.value is not None
    assert abs(result.value - 0.5) < 0.1  # 1000/2000 = 0.5
    assert result.category == "efficiency"


def test_calculate_all_metrics(sample_filing_data):
    """Test calculation of all metrics at once"""
    calculator = MetricsCalculator(sample_filing_data)
    
    results = calculator.calculate_all_metrics()
    
    assert len(results) > 10  # Should have many metrics
    assert 'gross_profit_margin' in results
    assert 'return_on_equity' in results
    assert 'current_ratio' in results
    
    # Check that results are MetricResult objects
    for result in results.values():
        assert isinstance(result, MetricResult)
        assert result.name is not None
        assert result.category in ['profitability', 'liquidity', 'leverage', 'efficiency', 'market']


def test_calculate_metrics_by_category(sample_filing_data):
    """Test calculation of metrics by category"""
    calculator = MetricsCalculator(sample_filing_data)
    
    # Test profitability metrics
    profitability_metrics = calculator.calculate_metrics_by_category('profitability')
    assert len(profitability_metrics) > 0
    assert all(result.category == 'profitability' for result in profitability_metrics.values())
    
    # Test liquidity metrics
    liquidity_metrics = calculator.calculate_metrics_by_category('liquidity')
    assert len(liquidity_metrics) > 0
    assert all(result.category == 'liquidity' for result in liquidity_metrics.values())


def test_get_financial_ratios(sample_filing_data):
    """Test getting financial ratios in standard format"""
    calculator = MetricsCalculator(sample_filing_data)
    
    ratios = calculator.get_financial_ratios()
    
    assert ratios.gross_profit_margin is not None
    assert ratios.net_profit_margin is not None
    assert ratios.return_on_assets is not None
    assert ratios.return_on_equity is not None
    assert ratios.current_ratio is not None
    assert ratios.debt_to_equity is not None


def test_custom_metric_definition():
    """Test adding custom metric definitions"""
    # Create a simple filing data
    company_info = CompanyInfo(name="Test", cik="123")
    filing_data = FilingData(
        company_info=company_info,
        filing_date=date.today(),
        period_end_date=date.today(),
        form_type="10-K",
        all_facts=[]
    )
    
    calculator = MetricsCalculator(filing_data)
    
    # Add custom metric
    custom_metric = MetricDefinition(
        name="test_ratio",
        formula="A / B",
        calculation_func=lambda data: data.get('a', 0) / data.get('b', 1),
        category="custom",
        unit="ratio",
        description="Test ratio"
    )
    
    calculator.add_custom_metric(custom_metric)
    
    assert 'test_ratio' in calculator.custom_metrics
    assert calculator.custom_metrics['test_ratio'].name == "test_ratio"


def test_trend_metrics():
    """Test trend metric calculation"""
    trend = TrendMetric(current_value=100.0, previous_value=80.0)
    
    assert trend.change_absolute == 20.0
    assert trend.change_percent == 25.0
    assert trend.trend_direction == "improving"
    
    # Test declining trend
    trend_declining = TrendMetric(current_value=70.0, previous_value=100.0)
    assert trend_declining.change_percent == -30.0
    assert trend_declining.trend_direction == "declining"
    
    # Test stable trend
    trend_stable = TrendMetric(current_value=100.0, previous_value=98.0)
    assert trend_stable.trend_direction == "stable"


def test_metrics_summary(sample_filing_data):
    """Test metrics summary generation"""
    calculator = MetricsCalculator(sample_filing_data)
    
    summary = calculator.get_metrics_summary()
    
    assert 'profitability' in summary
    assert 'liquidity' in summary
    assert 'leverage' in summary
    assert 'efficiency' in summary
    assert 'market' in summary
    assert 'data_quality' in summary
    
    # Check data quality summary
    data_quality = summary['data_quality']
    assert 'good' in data_quality
    assert 'estimated' in data_quality
    assert 'poor' in data_quality
    assert 'unavailable' in data_quality


def test_missing_data_handling():
    """Test handling of missing data"""
    # Create filing data with minimal facts
    company_info = CompanyInfo(name="Test", cik="123")
    facts = [
        FinancialFact(
            concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            label="Revenue",
            value=1000000,
            unit="USD",
            period="2023-12-31"
        )
    ]
    
    filing_data = FilingData(
        company_info=company_info,
        filing_date=date.today(),
        period_end_date=date.today(),
        form_type="10-K",
        all_facts=facts
    )
    
    calculator = MetricsCalculator(filing_data)
    
    # Try to calculate a metric that requires missing data
    result = calculator.calculate_metric('return_on_equity')
    
    assert result.value is None
    assert result.data_quality in ['poor', 'unavailable']
    assert len(result.missing_data) > 0


def test_decimal_scaling():
    """Test proper handling of decimal scaling"""
    company_info = CompanyInfo(name="Test", cik="123")
    
    # Create fact with decimals=-3 (value in thousands)
    fact = FinancialFact(
        concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        label="Revenue",
        value=1000,  # This represents 1,000,000 when scaled
        unit="USD",
        period="2023-12-31",
        decimals=-3
    )
    
    filing_data = FilingData(
        company_info=company_info,
        filing_date=date.today(),
        period_end_date=date.today(),
        form_type="10-K",
        all_facts=[fact]
    )
    
    calculator = MetricsCalculator(filing_data)
    
    # Test that the value is properly scaled
    extracted_data = calculator._extract_financial_data()
    assert extracted_data['revenue'] == 1000000.0  # Should be scaled up


if __name__ == "__main__":
    pytest.main([__file__])