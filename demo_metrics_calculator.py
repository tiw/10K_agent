#!/usr/bin/env python3
"""
Demo script for the Financial Metrics Calculator

This script demonstrates the comprehensive financial metrics calculation
capabilities including standard ratios, custom metrics, and trend analysis.
"""

import sys
import json
from datetime import date
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from xbrl_financial_service.models import (
    FilingData, CompanyInfo, FinancialFact, PeriodType
)
from xbrl_financial_service.analysis.metrics_calculator import (
    MetricsCalculator, MetricDefinition
)
from xbrl_financial_service.financial_service import FinancialService


def create_sample_data():
    """Create comprehensive sample financial data for demonstration"""
    company_info = CompanyInfo(
        name="TechCorp Industries Inc.",
        cik="0001234567",
        ticker="TECH",
        sic="3571",
        fiscal_year_end="12-31"
    )
    
    # Create comprehensive financial facts for 2023
    facts_2023 = [
        # Income Statement
        FinancialFact(
            concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            label="Total Revenue",
            value=5000000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:CostOfGoodsAndServicesSold",
            label="Cost of Revenue",
            value=2800000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:ResearchAndDevelopmentExpense",
            label="Research and Development",
            value=800000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:SellingGeneralAndAdministrativeExpense",
            label="Sales, General & Administrative",
            value=900000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:OperatingIncomeLoss",
            label="Operating Income",
            value=500000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:InterestExpense",
            label="Interest Expense",
            value=50000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:IncomeTaxExpenseBenefit",
            label="Income Tax Expense",
            value=90000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:NetIncomeLoss",
            label="Net Income",
            value=360000,
            unit="USD",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        
        # Balance Sheet
        FinancialFact(
            concept="us-gaap:CashAndCashEquivalentsAtCarryingValue",
            label="Cash and Cash Equivalents",
            value=800000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:AccountsReceivableNetCurrent",
            label="Accounts Receivable, Net",
            value=600000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:InventoryNet",
            label="Inventory",
            value=400000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:AssetsCurrent",
            label="Total Current Assets",
            value=1800000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:PropertyPlantAndEquipmentNet",
            label="Property, Plant & Equipment, Net",
            value=2200000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:Assets",
            label="Total Assets",
            value=4500000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:AccountsPayableCurrent",
            label="Accounts Payable",
            value=300000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:AccruedLiabilitiesCurrent",
            label="Accrued Liabilities",
            value=200000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:LiabilitiesCurrent",
            label="Total Current Liabilities",
            value=600000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:LongTermDebtNoncurrent",
            label="Long-term Debt",
            value=1200000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:StockholdersEquity",
            label="Total Shareholders' Equity",
            value=2700000,
            unit="USD",
            period="2023-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2023, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
            label="Weighted Average Shares Outstanding",
            value=1000000,
            unit="shares",
            period="2023-01-01_to_2023-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31)
        )
    ]
    
    # Create similar facts for 2022 (for trend analysis)
    facts_2022 = [
        FinancialFact(
            concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            label="Total Revenue",
            value=4200000,
            unit="USD",
            period="2022-01-01_to_2022-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2022, 1, 1),
            period_end=date(2022, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:NetIncomeLoss",
            label="Net Income",
            value=280000,
            unit="USD",
            period="2022-01-01_to_2022-12-31",
            period_type=PeriodType.DURATION,
            period_start=date(2022, 1, 1),
            period_end=date(2022, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:Assets",
            label="Total Assets",
            value=3800000,
            unit="USD",
            period="2022-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2022, 12, 31),
            decimals=-3
        ),
        FinancialFact(
            concept="us-gaap:StockholdersEquity",
            label="Total Shareholders' Equity",
            value=2200000,
            unit="USD",
            period="2022-12-31",
            period_type=PeriodType.INSTANT,
            period_end=date(2022, 12, 31),
            decimals=-3
        )
    ]
    
    all_facts = facts_2023 + facts_2022
    
    return FilingData(
        company_info=company_info,
        filing_date=date(2024, 3, 15),
        period_end_date=date(2023, 12, 31),
        form_type="10-K",
        all_facts=all_facts
    )


def demonstrate_basic_metrics():
    """Demonstrate basic metrics calculation"""
    print("=" * 60)
    print("FINANCIAL METRICS CALCULATOR DEMONSTRATION")
    print("=" * 60)
    
    # Create sample data
    filing_data = create_sample_data()
    
    # Initialize financial service with metrics calculator
    service = FinancialService(filing_data)
    
    print(f"\nCompany: {filing_data.company_info.name}")
    print(f"Period: {filing_data.period_end_date}")
    print(f"Total Facts: {len(filing_data.all_facts)}")
    
    print("\n" + "=" * 40)
    print("PROFITABILITY METRICS")
    print("=" * 40)
    
    profitability_metrics = service.calculate_metrics_by_category('profitability')
    for name, result in profitability_metrics.items():
        if result.value is not None:
            unit_symbol = "%" if result.unit == "percent" else ""
            print(f"{result.description:.<40} {result.value:>8.2f}{unit_symbol}")
        else:
            print(f"{result.description:.<40} {'N/A':>8}")
    
    print("\n" + "=" * 40)
    print("LIQUIDITY METRICS")
    print("=" * 40)
    
    liquidity_metrics = service.calculate_metrics_by_category('liquidity')
    for name, result in liquidity_metrics.items():
        if result.value is not None:
            unit_symbol = "%" if result.unit == "percent" else "x"
            print(f"{result.description:.<40} {result.value:>8.2f}{unit_symbol}")
        else:
            print(f"{result.description:.<40} {'N/A':>8}")
    
    print("\n" + "=" * 40)
    print("LEVERAGE METRICS")
    print("=" * 40)
    
    leverage_metrics = service.calculate_metrics_by_category('leverage')
    for name, result in leverage_metrics.items():
        if result.value is not None:
            unit_symbol = "%" if result.unit == "percent" else "x"
            print(f"{result.description:.<40} {result.value:>8.2f}{unit_symbol}")
        else:
            print(f"{result.description:.<40} {'N/A':>8}")
    
    print("\n" + "=" * 40)
    print("EFFICIENCY METRICS")
    print("=" * 40)
    
    efficiency_metrics = service.calculate_metrics_by_category('efficiency')
    for name, result in efficiency_metrics.items():
        if result.value is not None:
            unit_symbol = "%" if result.unit == "percent" else "x"
            print(f"{result.description:.<40} {result.value:>8.2f}{unit_symbol}")
        else:
            print(f"{result.description:.<40} {'N/A':>8}")
    
    return service


def demonstrate_custom_metrics(service):
    """Demonstrate custom metric creation"""
    print("\n" + "=" * 40)
    print("CUSTOM METRICS")
    print("=" * 40)
    
    # Add a custom metric: R&D Intensity
    rd_intensity_metric = MetricDefinition(
        name="rd_intensity",
        formula="R&D Expense / Revenue",
        calculation_func=lambda data: data.get('rd_expense', 0) / data.get('revenue', 1) if data.get('revenue') else None,
        category="efficiency",
        unit="percent",
        description="R&D spending as percentage of revenue",
        required_concepts=['ResearchAndDevelopmentExpense', 'Revenue']
    )
    
    # We need to access the metrics calculator directly for custom metrics
    # since the service doesn't expose this method yet
    calculator = service._metrics_calculator
    calculator.add_custom_metric(rd_intensity_metric)
    
    # Add another custom metric: Asset Quality Ratio
    asset_quality_metric = MetricDefinition(
        name="asset_quality_ratio",
        formula="(Cash + Receivables) / Total Assets",
        calculation_func=lambda data: (data.get('cash', 0) + data.get('receivables', 0)) / data.get('total_assets', 1) if data.get('total_assets') else None,
        category="liquidity",
        unit="percent",
        description="Quality of assets (liquid assets ratio)",
        required_concepts=['CashAndCashEquivalentsAtCarryingValue', 'AccountsReceivableNetCurrent', 'Assets']
    )
    
    calculator.add_custom_metric(asset_quality_metric)
    
    # Calculate custom metrics
    rd_result = calculator.calculate_metric('rd_intensity')
    asset_quality_result = calculator.calculate_metric('asset_quality_ratio')
    
    print(f"{rd_result.description:.<40} {rd_result.value:>8.2f}%" if rd_result.value else f"{rd_result.description:.<40} {'N/A':>8}")
    print(f"{asset_quality_result.description:.<40} {asset_quality_result.value:>8.2f}%" if asset_quality_result.value else f"{asset_quality_result.description:.<40} {'N/A':>8}")


def demonstrate_trend_analysis(service):
    """Demonstrate trend analysis capabilities"""
    print("\n" + "=" * 40)
    print("TREND ANALYSIS")
    print("=" * 40)
    
    # Calculate trend metrics comparing 2023 to 2022
    trend_metrics = service.calculate_trend_metrics(
        current_period="2023",
        previous_period="2022"
    )
    
    key_metrics = ['net_profit_margin', 'return_on_assets', 'return_on_equity']
    
    print(f"{'Metric':<25} {'2022':<10} {'2023':<10} {'Change':<10} {'Trend':<12}")
    print("-" * 70)
    
    for metric_name in key_metrics:
        if metric_name in trend_metrics:
            trend = trend_metrics[metric_name]
            if trend.current_value is not None and trend.previous_value is not None:
                change_str = f"{trend.change_percent:+.1f}%" if trend.change_percent else "N/A"
                trend_arrow = "↗" if trend.trend_direction == "improving" else "↘" if trend.trend_direction == "declining" else "→"
                
                print(f"{metric_name:<25} {trend.previous_value:<10.2f} {trend.current_value:<10.2f} {change_str:<10} {trend_arrow} {trend.trend_direction}")


def demonstrate_metrics_summary(service):
    """Demonstrate comprehensive metrics summary"""
    print("\n" + "=" * 40)
    print("METRICS SUMMARY")
    print("=" * 40)
    
    summary = service.get_metrics_summary()
    
    print("\nData Quality Summary:")
    quality = summary['data_quality']
    total_metrics = sum(quality.values())
    
    for quality_level, count in quality.items():
        percentage = (count / total_metrics * 100) if total_metrics > 0 else 0
        print(f"  {quality_level.title():.<20} {count:>3} ({percentage:>5.1f}%)")
    
    print(f"\nTotal Metrics Calculated: {total_metrics}")
    
    # Show category breakdown
    print("\nMetrics by Category:")
    for category in ['profitability', 'liquidity', 'leverage', 'efficiency', 'market']:
        if category in summary:
            available_metrics = len([m for m in summary[category].values() if m['value'] is not None])
            total_category_metrics = len(summary[category])
            print(f"  {category.title():.<20} {available_metrics}/{total_category_metrics}")


def demonstrate_financial_ratios_integration(service):
    """Demonstrate integration with standard FinancialRatios model"""
    print("\n" + "=" * 40)
    print("STANDARD FINANCIAL RATIOS")
    print("=" * 40)
    
    ratios = service.get_financial_ratios()
    ratios_dict = ratios.to_dict()
    
    for category, metrics in ratios_dict.items():
        if isinstance(metrics, dict) and any(v is not None for v in metrics.values()):
            print(f"\n{category.title()}:")
            for metric_name, value in metrics.items():
                if value is not None:
                    print(f"  {metric_name.replace('_', ' ').title():.<30} {value:>8.2f}")


def main():
    """Main demonstration function"""
    try:
        # Basic metrics demonstration
        service = demonstrate_basic_metrics()
        
        # Custom metrics demonstration
        demonstrate_custom_metrics(service)
        
        # Trend analysis demonstration
        demonstrate_trend_analysis(service)
        
        # Metrics summary demonstration
        demonstrate_metrics_summary(service)
        
        # Financial ratios integration demonstration
        demonstrate_financial_ratios_integration(service)
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        print("\nKey Features Demonstrated:")
        print("✓ Comprehensive financial metrics calculation")
        print("✓ Custom metric definition and calculation")
        print("✓ Trend analysis capabilities")
        print("✓ Data quality assessment")
        print("✓ Integration with existing FinancialRatios model")
        print("✓ Proper handling of XBRL decimal scaling")
        print("✓ Missing data detection and handling")
        
    except Exception as e:
        print(f"\nError during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())