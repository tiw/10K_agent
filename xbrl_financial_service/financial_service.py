"""
Main Financial Service

High-level interface for financial data operations and analysis.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import date

from .models import (
    FilingData, FinancialStatement, FinancialFact, FinancialRatios,
    StatementType, CompanyInfo
)
from .statement_builders import StatementBuilderFactory
from .database import DatabaseManager
from .config import Config
from .utils.logging import get_logger
from .utils.exceptions import QueryError, DataValidationError
from .analysis.metrics_calculator import MetricsCalculator, MetricResult, TrendMetric

logger = get_logger(__name__)


class FinancialService:
    """
    Main service for financial data operations
    """
    
    def __init__(self, filing_data: Optional[FilingData] = None, config: Optional[Config] = None):
        self.config = config or Config()
        self.db_manager = DatabaseManager(self.config)
        self.filing_data = filing_data
        
        # Cache for computed ratios
        self._ratios_cache: Optional[FinancialRatios] = None
        
        # Initialize metrics calculator if filing data is available
        self._metrics_calculator: Optional[MetricsCalculator] = None
        if filing_data:
            self._metrics_calculator = MetricsCalculator(filing_data)
    
    def load_filing_data(self, filing_data: FilingData):
        """Load filing data into the service"""
        self.filing_data = filing_data
        self._ratios_cache = None  # Clear cache
        
        # Initialize metrics calculator
        self._metrics_calculator = MetricsCalculator(filing_data)
        
        # Save to database
        try:
            filing_id = self.db_manager.save_filing_data(filing_data)
            logger.info(f"Saved filing data to database with ID: {filing_id}")
        except Exception as e:
            logger.warning(f"Failed to save filing data to database: {str(e)}")
    
    def get_income_statement(self, period: Optional[str] = None) -> Optional[FinancialStatement]:
        """
        Get income statement data
        
        Args:
            period: Optional period filter (not implemented yet)
            
        Returns:
            FinancialStatement or None if not available
        """
        if not self.filing_data:
            raise QueryError("No filing data loaded")
        
        return self.filing_data.income_statement
    
    def get_balance_sheet(self, period: Optional[str] = None) -> Optional[FinancialStatement]:
        """
        Get balance sheet data
        
        Args:
            period: Optional period filter (not implemented yet)
            
        Returns:
            FinancialStatement or None if not available
        """
        if not self.filing_data:
            raise QueryError("No filing data loaded")
        
        return self.filing_data.balance_sheet
    
    def get_cash_flow_statement(self, period: Optional[str] = None) -> Optional[FinancialStatement]:
        """
        Get cash flow statement data
        
        Args:
            period: Optional period filter (not implemented yet)
            
        Returns:
            FinancialStatement or None if not available
        """
        if not self.filing_data:
            raise QueryError("No filing data loaded")
        
        return self.filing_data.cash_flow_statement
    
    def get_financial_ratios(self) -> FinancialRatios:
        """
        Calculate and return financial ratios using the enhanced metrics calculator
        
        Returns:
            FinancialRatios object with calculated ratios
        """
        if self._ratios_cache:
            return self._ratios_cache
        
        if not self.filing_data or not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        # Use the enhanced metrics calculator
        ratios = self._metrics_calculator.get_financial_ratios()
        self._ratios_cache = ratios
        return ratios
    
    def search_facts(self, query: str, limit: int = 50) -> List[FinancialFact]:
        """
        Search for financial facts
        
        Args:
            query: Search query (concept name or label pattern)
            limit: Maximum number of results
            
        Returns:
            List of matching FinancialFact objects
        """
        if not self.filing_data:
            raise QueryError("No filing data loaded")
        
        query_lower = query.lower()
        matching_facts = []
        
        for fact in self.filing_data.all_facts:
            if (query_lower in fact.concept.lower() or 
                query_lower in fact.label.lower()):
                matching_facts.append(fact)
                
                if len(matching_facts) >= limit:
                    break
        
        return matching_facts
    
    def get_company_info(self) -> Optional[CompanyInfo]:
        """
        Get company information
        
        Returns:
            CompanyInfo object or None if not available
        """
        if not self.filing_data:
            return None
        
        return self.filing_data.company_info
    
    def get_fact_by_concept(self, concept: str) -> Optional[FinancialFact]:
        """
        Get a specific fact by concept name
        
        Args:
            concept: Concept name to search for
            
        Returns:
            FinancialFact or None if not found
        """
        if not self.filing_data:
            return None
        
        for fact in self.filing_data.all_facts:
            if fact.concept == concept or fact.concept.endswith(f":{concept}"):
                return fact
        
        return None
    
    def _calculate_financial_ratios(self) -> FinancialRatios:
        """Calculate financial ratios from available data"""
        ratios = FinancialRatios()
        
        try:
            # Get key financial figures
            revenue = self._get_numeric_fact_value(['Revenue', 'RevenueFromContractWithCustomerExcludingAssessedTax'])
            net_income = self._get_numeric_fact_value(['NetIncomeLoss'])
            total_assets = self._get_numeric_fact_value(['Assets'])
            total_equity = self._get_numeric_fact_value(['StockholdersEquity'])
            current_assets = self._get_numeric_fact_value(['AssetsCurrent'])
            current_liabilities = self._get_numeric_fact_value(['LiabilitiesCurrent'])
            total_debt = self._get_numeric_fact_value(['LongTermDebtNoncurrent', 'LongTermDebt'])
            
            # Calculate profitability ratios
            if revenue and net_income:
                ratios.net_profit_margin = net_income / revenue
            
            if total_assets and net_income:
                ratios.return_on_assets = net_income / total_assets
            
            if total_equity and net_income:
                ratios.return_on_equity = net_income / total_equity
            
            # Calculate liquidity ratios
            if current_assets and current_liabilities:
                ratios.current_ratio = current_assets / current_liabilities
            
            # Calculate leverage ratios
            if total_debt and total_equity:
                ratios.debt_to_equity = total_debt / total_equity
            
            if total_debt and total_assets:
                ratios.debt_to_assets = total_debt / total_assets
            
            logger.info("Successfully calculated financial ratios")
            
        except Exception as e:
            logger.warning(f"Error calculating financial ratios: {str(e)}")
        
        return ratios
    
    def _get_numeric_fact_value(self, concept_names: List[str]) -> Optional[float]:
        """
        Get numeric value for a fact by trying multiple concept names
        
        Args:
            concept_names: List of concept names to try
            
        Returns:
            Numeric value or None if not found
        """
        for concept_name in concept_names:
            fact = self.get_fact_by_concept(concept_name)
            if fact and isinstance(fact.value, (int, float)):
                # Apply scaling if decimals are specified
                if fact.decimals is not None:
                    return float(fact.value) * (10 ** fact.decimals)
                return float(fact.value)
        
        return None
    
    def build_financial_statement(self, statement_type: StatementType) -> Optional[FinancialStatement]:
        """
        Build a financial statement using the statement builders
        
        Args:
            statement_type: Type of statement to build
            
        Returns:
            Built FinancialStatement or None if cannot be built
        """
        if not self.filing_data:
            raise QueryError("No filing data loaded")
        
        try:
            # Create builder for the statement type
            builder = StatementBuilderFactory.create_builder(
                statement_type=statement_type,
                facts=self.filing_data.all_facts,
                presentation_relationships=[],  # TODO: Add when available
                calculation_relationships=[]    # TODO: Add when available
            )
            
            # Build the statement
            statement = builder.build_statement(
                company_name=self.filing_data.company_info.name if self.filing_data.company_info else "Unknown",
                period_end=self.filing_data.period_end_date
            )
            
            logger.info(f"Successfully built {statement_type.value} with {len(statement.facts)} facts")
            return statement
            
        except Exception as e:
            logger.error(f"Failed to build {statement_type.value}: {str(e)}")
            return None
    
    def rebuild_all_statements(self):
        """
        Rebuild all financial statements using the statement builders
        """
        if not self.filing_data:
            raise QueryError("No filing data loaded")
        
        logger.info("Rebuilding all financial statements")
        
        # Build each statement type
        self.filing_data.income_statement = self.build_financial_statement(StatementType.INCOME_STATEMENT)
        self.filing_data.balance_sheet = self.build_financial_statement(StatementType.BALANCE_SHEET)
        self.filing_data.cash_flow_statement = self.build_financial_statement(StatementType.CASH_FLOW_STATEMENT)
        
        # Clear ratios cache since statements have changed
        self._ratios_cache = None
        
        logger.info("Completed rebuilding all financial statements")
    
    def get_summary_data(self) -> Dict[str, Any]:
        """
        Get summary data for the filing
        
        Returns:
            Dictionary with summary information
        """
        if not self.filing_data:
            return {}
        
        summary = {
            'company_info': self.filing_data.company_info.to_dict() if self.filing_data.company_info else {},
            'filing_date': self.filing_data.filing_date.isoformat() if self.filing_data.filing_date else None,
            'period_end_date': self.filing_data.period_end_date.isoformat() if self.filing_data.period_end_date else None,
            'form_type': self.filing_data.form_type,
            'total_facts': len(self.filing_data.all_facts),
            'statements_available': {
                'income_statement': self.filing_data.income_statement is not None,
                'balance_sheet': self.filing_data.balance_sheet is not None,
                'cash_flow_statement': self.filing_data.cash_flow_statement is not None,
                'shareholders_equity': self.filing_data.shareholders_equity is not None,
                'comprehensive_income': self.filing_data.comprehensive_income is not None
            }
        }
        
        # Add key financial metrics if available
        try:
            ratios = self.get_financial_ratios()
            summary['key_ratios'] = {
                'net_profit_margin': ratios.net_profit_margin,
                'return_on_assets': ratios.return_on_assets,
                'return_on_equity': ratios.return_on_equity,
                'current_ratio': ratios.current_ratio,
                'debt_to_equity': ratios.debt_to_equity
            }
        except Exception:
            summary['key_ratios'] = {}
        
        return summary
    
    def calculate_all_metrics(self, period: Optional[str] = None) -> Dict[str, MetricResult]:
        """
        Calculate all available financial metrics
        
        Args:
            period: Optional period filter
            
        Returns:
            Dictionary of metric results
        """
        if not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        return self._metrics_calculator.calculate_all_metrics(period)
    
    def calculate_metric(self, metric_name: str, period: Optional[str] = None) -> MetricResult:
        """
        Calculate a specific financial metric
        
        Args:
            metric_name: Name of the metric to calculate
            period: Optional period filter
            
        Returns:
            MetricResult object
        """
        if not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        return self._metrics_calculator.calculate_metric(metric_name, period)
    
    def calculate_metrics_by_category(self, category: str, period: Optional[str] = None) -> Dict[str, MetricResult]:
        """
        Calculate all metrics in a specific category
        
        Args:
            category: Category name ('profitability', 'liquidity', 'leverage', 'efficiency', 'market')
            period: Optional period filter
            
        Returns:
            Dictionary of metric results for the category
        """
        if not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        return self._metrics_calculator.calculate_metrics_by_category(category, period)
    
    def calculate_trend_metrics(self, current_period: Optional[str] = None, 
                              previous_period: Optional[str] = None) -> Dict[str, TrendMetric]:
        """
        Calculate metrics with trend analysis
        
        Args:
            current_period: Current period for comparison
            previous_period: Previous period for comparison
            
        Returns:
            Dictionary of trend metrics
        """
        if not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        return self._metrics_calculator.calculate_trend_metrics(current_period, previous_period)
    
    def get_metrics_summary(self, period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a comprehensive summary of all calculated metrics
        
        Args:
            period: Optional period filter
            
        Returns:
            Dictionary with metrics organized by category and data quality summary
        """
        if not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        return self._metrics_calculator.get_metrics_summary(period)
    
    def add_custom_metric(self, metric_definition) -> None:
        """
        Add a custom metric definition
        
        Args:
            metric_definition: MetricDefinition object defining the custom metric
        """
        if not self._metrics_calculator:
            raise QueryError("No filing data loaded")
        
        self._metrics_calculator.add_custom_metric(metric_definition)
        # Clear cache since new metrics are available
        self._ratios_cache = None