#!/usr/bin/env python3
"""
Demo script for Financial Statement Builders

This script demonstrates how to use the new statement builders to construct
properly structured financial statements from XBRL facts.
"""

from datetime import date
from xbrl_financial_service.financial_service import FinancialService
from xbrl_financial_service.models import (
    FilingData, CompanyInfo, FinancialFact, StatementType
)


def create_sample_filing_data():
    """Create sample filing data for demonstration"""
    
    # Company information
    company_info = CompanyInfo(
        name="Demo Corporation",
        cik="0001234567",
        ticker="DEMO"
    )
    
    # Sample financial facts
    facts = [
        # Income Statement Facts
        FinancialFact(
            concept="us-gaap:Revenues",
            label="Total Revenues",
            value=500000,  # $500M (with decimals=-3, this becomes $500B)
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:CostOfRevenue",
            label="Cost of Revenue",
            value=300000,  # $300M -> $300B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:GrossProfit",
            label="Gross Profit",
            value=200000,  # $200M -> $200B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:OperatingExpenses",
            label="Operating Expenses",
            value=100000,  # $100M -> $100B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:OperatingIncomeLoss",
            label="Operating Income",
            value=100000,  # $100M -> $100B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:NetIncomeLoss",
            label="Net Income",
            value=75000,   # $75M -> $75B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        
        # Balance Sheet Facts
        FinancialFact(
            concept="us-gaap:CashAndCashEquivalents",
            label="Cash and Cash Equivalents",
            value=50000,   # $50M -> $50B
            unit="USD",
            decimals=-3,
            period="2023-12-31"
        ),
        FinancialFact(
            concept="us-gaap:AssetsCurrent",
            label="Current Assets",
            value=150000,  # $150M -> $150B
            unit="USD",
            decimals=-3,
            period="2023-12-31"
        ),
        FinancialFact(
            concept="us-gaap:Assets",
            label="Total Assets",
            value=400000,  # $400M -> $400B
            unit="USD",
            decimals=-3,
            period="2023-12-31"
        ),
        FinancialFact(
            concept="us-gaap:LiabilitiesCurrent",
            label="Current Liabilities",
            value=80000,   # $80M -> $80B
            unit="USD",
            decimals=-3,
            period="2023-12-31"
        ),
        FinancialFact(
            concept="us-gaap:Liabilities",
            label="Total Liabilities",
            value=200000,  # $200M -> $200B
            unit="USD",
            decimals=-3,
            period="2023-12-31"
        ),
        FinancialFact(
            concept="us-gaap:StockholdersEquity",
            label="Stockholders' Equity",
            value=200000,  # $200M -> $200B
            unit="USD",
            decimals=-3,
            period="2023-12-31"
        ),
        
        # Cash Flow Facts
        FinancialFact(
            concept="us-gaap:NetCashProvidedByUsedInOperatingActivities",
            label="Net Cash from Operating Activities",
            value=90000,   # $90M -> $90B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:NetCashProvidedByUsedInInvestingActivities",
            label="Net Cash from Investing Activities",
            value=-30000,  # -$30M -> -$30B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:NetCashProvidedByUsedInFinancingActivities",
            label="Net Cash from Financing Activities",
            value=-20000,  # -$20M -> -$20B
            unit="USD",
            decimals=-3,
            period="2023"
        ),
        FinancialFact(
            concept="us-gaap:DepreciationDepletionAndAmortization",
            label="Depreciation and Amortization",
            value=25000,   # $25M -> $25B
            unit="USD",
            decimals=-3,
            period="2023"
        )
    ]
    
    # Create filing data
    filing_data = FilingData(
        company_info=company_info,
        filing_date=date(2024, 3, 15),
        period_end_date=date(2023, 12, 31),
        form_type="10-K",
        all_facts=facts
    )
    
    return filing_data


def print_statement_summary(statement, statement_name):
    """Print a summary of a financial statement"""
    print(f"\n{'='*60}")
    print(f"{statement_name.upper()}")
    print(f"{'='*60}")
    print(f"Company: {statement.company_name}")
    print(f"Period End: {statement.period_end}")
    print(f"Total Facts: {len(statement.facts)}")
    print(f"Presentation Items: {len(statement.presentation_order)}")
    
    print(f"\nKey Line Items:")
    print(f"{'Concept':<50} {'Value':>15}")
    print(f"{'-'*65}")
    
    # Show first 10 facts
    for i, fact in enumerate(statement.facts[:10]):
        value_str = f"${fact.get_scaled_value():,.0f}" if isinstance(fact.get_scaled_value(), (int, float)) else str(fact.get_scaled_value())
        concept_short = fact.concept.split(':')[-1][:45]
        print(f"{concept_short:<50} {value_str:>15}")
    
    if len(statement.facts) > 10:
        print(f"... and {len(statement.facts) - 10} more facts")


def main():
    """Main demo function"""
    print("Financial Statement Builders Demo")
    print("=" * 50)
    
    # Create sample data
    print("Creating sample filing data...")
    filing_data = create_sample_filing_data()
    
    # Create financial service
    service = FinancialService()
    service.load_filing_data(filing_data)
    
    print(f"Loaded filing data with {len(filing_data.all_facts)} facts")
    
    # Build individual statements
    print("\nBuilding financial statements...")
    
    # Income Statement
    income_statement = service.build_financial_statement(StatementType.INCOME_STATEMENT)
    if income_statement:
        print_statement_summary(income_statement, "Income Statement")
    
    # Balance Sheet
    balance_sheet = service.build_financial_statement(StatementType.BALANCE_SHEET)
    if balance_sheet:
        print_statement_summary(balance_sheet, "Balance Sheet")
    
    # Cash Flow Statement
    cash_flow_statement = service.build_financial_statement(StatementType.CASH_FLOW_STATEMENT)
    if cash_flow_statement:
        print_statement_summary(cash_flow_statement, "Cash Flow Statement")
    
    # Rebuild all statements at once
    print(f"\n{'='*60}")
    print("REBUILDING ALL STATEMENTS")
    print(f"{'='*60}")
    
    service.rebuild_all_statements()
    
    print("All statements rebuilt successfully!")
    print(f"Income Statement: {'✓' if service.filing_data.income_statement else '✗'}")
    print(f"Balance Sheet: {'✓' if service.filing_data.balance_sheet else '✗'}")
    print(f"Cash Flow Statement: {'✓' if service.filing_data.cash_flow_statement else '✗'}")
    
    # Show summary data
    print(f"\n{'='*60}")
    print("FILING SUMMARY")
    print(f"{'='*60}")
    
    summary = service.get_summary_data()
    print(f"Company: {summary['company_info']['name']}")
    print(f"Form Type: {summary['form_type']}")
    print(f"Filing Date: {summary['filing_date']}")
    print(f"Period End: {summary['period_end_date']}")
    print(f"Total Facts: {summary['total_facts']}")
    
    print(f"\nStatements Available:")
    for stmt_type, available in summary['statements_available'].items():
        status = "✓" if available else "✗"
        print(f"  {stmt_type.replace('_', ' ').title()}: {status}")
    
    print(f"\nKey Financial Ratios:")
    ratios = summary.get('key_ratios', {})
    for ratio_name, ratio_value in ratios.items():
        if ratio_value is not None:
            if 'margin' in ratio_name or 'return' in ratio_name:
                print(f"  {ratio_name.replace('_', ' ').title()}: {ratio_value:.2%}")
            else:
                print(f"  {ratio_name.replace('_', ' ').title()}: {ratio_value:.2f}")
        else:
            print(f"  {ratio_name.replace('_', ' ').title()}: N/A")
    
    print(f"\n{'='*60}")
    print("Demo completed successfully!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()