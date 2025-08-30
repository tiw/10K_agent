"""
Financial Metrics Calculator

Calculates comprehensive financial ratios and metrics from XBRL data,
including profitability, liquidity, leverage, and efficiency ratios.
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import date
import statistics
from decimal import Decimal

from ..models import FilingData, FinancialFact, FinancialRatios
from ..utils.logging import get_logger
from ..utils.exceptions import DataValidationError

logger = get_logger(__name__)


@dataclass
class MetricDefinition:
    """Definition of a custom financial metric"""
    name: str
    formula: str  # Human-readable formula description
    calculation_func: Callable[[Dict[str, float]], Optional[float]]
    category: str  # 'profitability', 'liquidity', 'leverage', 'efficiency', 'market'
    unit: str = "ratio"  # 'ratio', 'percent', 'currency', 'days'
    description: str = ""
    required_concepts: List[str] = field(default_factory=list)


@dataclass
class MetricResult:
    """Result of a metric calculation"""
    name: str
    value: Optional[float]
    unit: str
    category: str
    description: str
    formula: str
    data_quality: str = "good"  # 'good', 'estimated', 'poor', 'unavailable'
    missing_data: List[str] = field(default_factory=list)


@dataclass
class TrendMetric:
    """Metric with trend analysis"""
    current_value: Optional[float]
    previous_value: Optional[float]
    change_absolute: Optional[float] = None
    change_percent: Optional[float] = None
    trend_direction: str = "stable"  # 'improving', 'declining', 'stable'
    
    def __post_init__(self):
        if self.current_value is not None and self.previous_value is not None:
            self.change_absolute = self.current_value - self.previous_value
            if self.previous_value != 0:
                self.change_percent = (self.change_absolute / abs(self.previous_value)) * 100
                
                # Determine trend direction
                if self.change_percent > 5:
                    self.trend_direction = "improving"
                elif self.change_percent < -5:
                    self.trend_direction = "declining"
                else:
                    self.trend_direction = "stable"


class MetricsCalculator:
    """
    Comprehensive financial metrics calculator with support for
    standard ratios, custom metrics, and trend analysis
    """
    
    def __init__(self, filing_data: FilingData):
        self.filing_data = filing_data
        self.facts_by_concept = self._index_facts_by_concept()
        self.custom_metrics: Dict[str, MetricDefinition] = {}
        self._setup_standard_metrics()
    
    def _index_facts_by_concept(self) -> Dict[str, List[FinancialFact]]:
        """Index facts by concept for efficient lookup"""
        index = {}
        for fact in self.filing_data.all_facts:
            concept = fact.concept.split(':')[-1]  # Remove namespace prefix
            if concept not in index:
                index[concept] = []
            index[concept].append(fact)
        return index
    
    def _setup_standard_metrics(self):
        """Setup standard financial metrics definitions"""
        
        # Profitability Ratios
        self.add_custom_metric(MetricDefinition(
            name="gross_profit_margin",
            formula="(Revenue - Cost of Sales) / Revenue",
            calculation_func=lambda data: (data.get('revenue', 0) - data.get('cost_of_sales', 0)) / data.get('revenue', 1) if data.get('revenue') else None,
            category="profitability",
            unit="percent",
            description="Measures the percentage of revenue retained after direct costs",
            required_concepts=['Revenue', 'CostOfGoodsAndServicesSold']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="operating_profit_margin",
            formula="Operating Income / Revenue",
            calculation_func=lambda data: data.get('operating_income') / data.get('revenue') if data.get('revenue') and data.get('operating_income') else None,
            category="profitability",
            unit="percent",
            description="Measures operating efficiency and pricing power",
            required_concepts=['OperatingIncomeLoss', 'Revenue']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="net_profit_margin",
            formula="Net Income / Revenue",
            calculation_func=lambda data: data.get('net_income') / data.get('revenue') if data.get('revenue') and data.get('net_income') else None,
            category="profitability",
            unit="percent",
            description="Overall profitability after all expenses",
            required_concepts=['NetIncomeLoss', 'Revenue']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="return_on_assets",
            formula="Net Income / Total Assets",
            calculation_func=lambda data: data.get('net_income') / data.get('total_assets') if data.get('total_assets') and data.get('net_income') else None,
            category="profitability",
            unit="percent",
            description="Efficiency of asset utilization",
            required_concepts=['NetIncomeLoss', 'Assets']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="return_on_equity",
            formula="Net Income / Shareholders' Equity",
            calculation_func=lambda data: data.get('net_income') / data.get('shareholders_equity') if data.get('shareholders_equity') and data.get('net_income') else None,
            category="profitability",
            unit="percent",
            description="Return generated on shareholders' investment",
            required_concepts=['NetIncomeLoss', 'StockholdersEquity']
        ))
        
        # Liquidity Ratios
        self.add_custom_metric(MetricDefinition(
            name="current_ratio",
            formula="Current Assets / Current Liabilities",
            calculation_func=lambda data: data.get('current_assets') / data.get('current_liabilities') if data.get('current_liabilities') else None,
            category="liquidity",
            unit="ratio",
            description="Ability to pay short-term obligations",
            required_concepts=['AssetsCurrent', 'LiabilitiesCurrent']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="quick_ratio",
            formula="(Current Assets - Inventory) / Current Liabilities",
            calculation_func=lambda data: (data.get('current_assets', 0) - data.get('inventory', 0)) / data.get('current_liabilities') if data.get('current_liabilities') else None,
            category="liquidity",
            unit="ratio",
            description="Liquidity excluding inventory",
            required_concepts=['AssetsCurrent', 'LiabilitiesCurrent', 'InventoryNet']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="cash_ratio",
            formula="Cash and Cash Equivalents / Current Liabilities",
            calculation_func=lambda data: data.get('cash') / data.get('current_liabilities') if data.get('current_liabilities') and data.get('cash') else None,
            category="liquidity",
            unit="ratio",
            description="Most conservative liquidity measure",
            required_concepts=['CashAndCashEquivalentsAtCarryingValue', 'LiabilitiesCurrent']
        ))
        
        # Leverage Ratios
        self.add_custom_metric(MetricDefinition(
            name="debt_to_equity",
            formula="Total Debt / Shareholders' Equity",
            calculation_func=lambda data: data.get('total_debt') / data.get('shareholders_equity') if data.get('shareholders_equity') and data.get('total_debt') else None,
            category="leverage",
            unit="ratio",
            description="Financial leverage and capital structure",
            required_concepts=['LongTermDebtNoncurrent', 'StockholdersEquity']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="debt_to_assets",
            formula="Total Debt / Total Assets",
            calculation_func=lambda data: data.get('total_debt') / data.get('total_assets') if data.get('total_assets') and data.get('total_debt') else None,
            category="leverage",
            unit="percent",
            description="Proportion of assets financed by debt",
            required_concepts=['LongTermDebtNoncurrent', 'Assets']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="interest_coverage",
            formula="Operating Income / Interest Expense",
            calculation_func=lambda data: data.get('operating_income') / data.get('interest_expense') if data.get('interest_expense') and data.get('operating_income') else None,
            category="leverage",
            unit="ratio",
            description="Ability to pay interest on debt",
            required_concepts=['OperatingIncomeLoss', 'InterestExpense']
        ))
        
        # Efficiency Ratios
        self.add_custom_metric(MetricDefinition(
            name="asset_turnover",
            formula="Revenue / Total Assets",
            calculation_func=lambda data: data.get('revenue') / data.get('total_assets') if data.get('total_assets') and data.get('revenue') else None,
            category="efficiency",
            unit="ratio",
            description="Efficiency of asset utilization",
            required_concepts=['Revenue', 'Assets']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="inventory_turnover",
            formula="Cost of Sales / Average Inventory",
            calculation_func=lambda data: data.get('cost_of_sales') / data.get('inventory') if data.get('inventory') and data.get('cost_of_sales') else None,
            category="efficiency",
            unit="ratio",
            description="Efficiency of inventory management",
            required_concepts=['CostOfGoodsAndServicesSold', 'InventoryNet']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="receivables_turnover",
            formula="Revenue / Accounts Receivable",
            calculation_func=lambda data: data.get('revenue') / data.get('receivables') if data.get('receivables') and data.get('revenue') else None,
            category="efficiency",
            unit="ratio",
            description="Efficiency of receivables collection",
            required_concepts=['Revenue', 'AccountsReceivableNetCurrent']
        ))
        
        # Market Ratios
        self.add_custom_metric(MetricDefinition(
            name="earnings_per_share",
            formula="Net Income / Weighted Average Shares Outstanding",
            calculation_func=lambda data: data.get('net_income') / data.get('shares_outstanding') if data.get('shares_outstanding') and data.get('net_income') else None,
            category="market",
            unit="currency",
            description="Earnings attributable to each share",
            required_concepts=['NetIncomeLoss', 'WeightedAverageNumberOfSharesOutstandingBasic']
        ))
        
        self.add_custom_metric(MetricDefinition(
            name="book_value_per_share",
            formula="Shareholders' Equity / Shares Outstanding",
            calculation_func=lambda data: data.get('shareholders_equity') / data.get('shares_outstanding') if data.get('shares_outstanding') and data.get('shareholders_equity') else None,
            category="market",
            unit="currency",
            description="Book value attributable to each share",
            required_concepts=['StockholdersEquity', 'CommonStockSharesOutstanding']
        ))
    
    def add_custom_metric(self, metric_definition: MetricDefinition):
        """Add a custom metric definition"""
        self.custom_metrics[metric_definition.name] = metric_definition
        logger.info(f"Added custom metric: {metric_definition.name}")
    
    def calculate_all_metrics(self, period: Optional[str] = None) -> Dict[str, MetricResult]:
        """Calculate all available metrics"""
        logger.info("Calculating all financial metrics")
        
        # Get base financial data
        financial_data = self._extract_financial_data(period)
        
        results = {}
        for metric_name, metric_def in self.custom_metrics.items():
            try:
                result = self._calculate_metric(metric_def, financial_data)
                results[metric_name] = result
            except Exception as e:
                logger.warning(f"Failed to calculate {metric_name}: {str(e)}")
                results[metric_name] = MetricResult(
                    name=metric_name,
                    value=None,
                    unit=metric_def.unit,
                    category=metric_def.category,
                    description=metric_def.description,
                    formula=metric_def.formula,
                    data_quality="unavailable"
                )
        
        logger.info(f"Calculated {len([r for r in results.values() if r.value is not None])} metrics successfully")
        return results
    
    def calculate_metric(self, metric_name: str, period: Optional[str] = None) -> MetricResult:
        """Calculate a specific metric"""
        if metric_name not in self.custom_metrics:
            raise ValueError(f"Unknown metric: {metric_name}")
        
        metric_def = self.custom_metrics[metric_name]
        financial_data = self._extract_financial_data(period)
        
        return self._calculate_metric(metric_def, financial_data)
    
    def calculate_metrics_by_category(self, category: str, period: Optional[str] = None) -> Dict[str, MetricResult]:
        """Calculate all metrics in a specific category"""
        financial_data = self._extract_financial_data(period)
        results = {}
        
        for metric_name, metric_def in self.custom_metrics.items():
            if metric_def.category == category:
                try:
                    result = self._calculate_metric(metric_def, financial_data)
                    results[metric_name] = result
                except Exception as e:
                    logger.warning(f"Failed to calculate {metric_name}: {str(e)}")
        
        return results
    
    def calculate_trend_metrics(self, current_period: Optional[str] = None, 
                              previous_period: Optional[str] = None) -> Dict[str, TrendMetric]:
        """Calculate metrics with trend analysis"""
        logger.info("Calculating trend metrics")
        
        current_metrics = self.calculate_all_metrics(current_period)
        previous_metrics = self.calculate_all_metrics(previous_period)
        
        trend_metrics = {}
        for metric_name in current_metrics:
            current_value = current_metrics[metric_name].value
            previous_value = previous_metrics.get(metric_name, {}).value if metric_name in previous_metrics else None
            
            trend_metrics[metric_name] = TrendMetric(
                current_value=current_value,
                previous_value=previous_value
            )
        
        return trend_metrics
    
    def get_financial_ratios(self, period: Optional[str] = None) -> FinancialRatios:
        """Get financial ratios in the standard FinancialRatios format"""
        metrics = self.calculate_all_metrics(period)
        
        return FinancialRatios(
            # Profitability ratios
            gross_profit_margin=self._get_metric_value(metrics, 'gross_profit_margin'),
            operating_profit_margin=self._get_metric_value(metrics, 'operating_profit_margin'),
            net_profit_margin=self._get_metric_value(metrics, 'net_profit_margin'),
            return_on_assets=self._get_metric_value(metrics, 'return_on_assets'),
            return_on_equity=self._get_metric_value(metrics, 'return_on_equity'),
            
            # Liquidity ratios
            current_ratio=self._get_metric_value(metrics, 'current_ratio'),
            quick_ratio=self._get_metric_value(metrics, 'quick_ratio'),
            cash_ratio=self._get_metric_value(metrics, 'cash_ratio'),
            
            # Leverage ratios
            debt_to_equity=self._get_metric_value(metrics, 'debt_to_equity'),
            debt_to_assets=self._get_metric_value(metrics, 'debt_to_assets'),
            interest_coverage=self._get_metric_value(metrics, 'interest_coverage'),
            
            # Efficiency ratios
            asset_turnover=self._get_metric_value(metrics, 'asset_turnover'),
            inventory_turnover=self._get_metric_value(metrics, 'inventory_turnover'),
            receivables_turnover=self._get_metric_value(metrics, 'receivables_turnover'),
            
            # Market ratios
            earnings_per_share=self._get_metric_value(metrics, 'earnings_per_share'),
            book_value_per_share=self._get_metric_value(metrics, 'book_value_per_share')
        )
    
    def _calculate_metric(self, metric_def: MetricDefinition, financial_data: Dict[str, float]) -> MetricResult:
        """Calculate a single metric"""
        missing_data = []
        data_quality = "good"
        
        # Check for required data
        for concept in metric_def.required_concepts:
            concept_key = self._concept_to_key(concept)
            if concept_key not in financial_data or financial_data[concept_key] is None:
                missing_data.append(concept)
        
        # Determine data quality
        if missing_data:
            if len(missing_data) == len(metric_def.required_concepts):
                data_quality = "unavailable"
            else:
                data_quality = "estimated"
        
        # Calculate the metric
        try:
            value = metric_def.calculation_func(financial_data)
            
            # Convert to percentage if needed
            if metric_def.unit == "percent" and value is not None:
                value *= 100
                
        except (ZeroDivisionError, TypeError, KeyError):
            value = None
            data_quality = "poor"
        
        return MetricResult(
            name=metric_def.name,
            value=value,
            unit=metric_def.unit,
            category=metric_def.category,
            description=metric_def.description,
            formula=metric_def.formula,
            data_quality=data_quality,
            missing_data=missing_data
        )
    
    def _extract_financial_data(self, period: Optional[str] = None) -> Dict[str, float]:
        """Extract key financial data points for calculations"""
        data = {}
        
        # Revenue concepts
        data['revenue'] = self._get_concept_value('RevenueFromContractWithCustomerExcludingAssessedTax', period) or \
                         self._get_concept_value('Revenues', period)
        
        # Cost and expense concepts
        data['cost_of_sales'] = self._get_concept_value('CostOfGoodsAndServicesSold', period) or \
                               self._get_concept_value('CostOfRevenue', period)
        
        # Income concepts
        data['operating_income'] = self._get_concept_value('OperatingIncomeLoss', period)
        data['net_income'] = self._get_concept_value('NetIncomeLoss', period)
        
        # Balance sheet concepts
        data['total_assets'] = self._get_concept_value('Assets', period)
        data['current_assets'] = self._get_concept_value('AssetsCurrent', period)
        data['inventory'] = self._get_concept_value('InventoryNet', period)
        data['receivables'] = self._get_concept_value('AccountsReceivableNetCurrent', period)
        data['cash'] = self._get_concept_value('CashAndCashEquivalentsAtCarryingValue', period)
        
        data['current_liabilities'] = self._get_concept_value('LiabilitiesCurrent', period)
        data['total_debt'] = self._get_concept_value('LongTermDebtNoncurrent', period) or \
                            self._get_concept_value('LongTermDebt', period)
        data['shareholders_equity'] = self._get_concept_value('StockholdersEquity', period)
        
        # Other concepts
        data['interest_expense'] = self._get_concept_value('InterestExpense', period)
        data['shares_outstanding'] = self._get_concept_value('WeightedAverageNumberOfSharesOutstandingBasic', period) or \
                                   self._get_concept_value('CommonStockSharesOutstanding', period)
        
        return data
    
    def _get_concept_value(self, concept: str, period: Optional[str] = None) -> Optional[float]:
        """Get the value for a financial concept"""
        facts = self.facts_by_concept.get(concept, [])
        if not facts:
            return None
        
        # Filter by period if specified
        if period:
            facts = [f for f in facts if period in f.period]
        
        if not facts:
            return None
        
        # Get the most recent fact
        latest_fact = max(facts, key=lambda f: f.period_end or date.min)
        
        if isinstance(latest_fact.value, (int, float, Decimal)):
            # Apply scaling if decimals are specified
            value = float(latest_fact.value)
            if latest_fact.decimals is not None:
                value *= (10 ** (-latest_fact.decimals))
            return value
        
        return None
    
    def _concept_to_key(self, concept: str) -> str:
        """Convert concept name to data dictionary key"""
        # Simple mapping - could be enhanced
        concept_mapping = {
            'Revenue': 'revenue',
            'RevenueFromContractWithCustomerExcludingAssessedTax': 'revenue',
            'CostOfGoodsAndServicesSold': 'cost_of_sales',
            'OperatingIncomeLoss': 'operating_income',
            'NetIncomeLoss': 'net_income',
            'Assets': 'total_assets',
            'AssetsCurrent': 'current_assets',
            'LiabilitiesCurrent': 'current_liabilities',
            'StockholdersEquity': 'shareholders_equity',
            'LongTermDebtNoncurrent': 'total_debt',
            'InterestExpense': 'interest_expense',
            'InventoryNet': 'inventory',
            'AccountsReceivableNetCurrent': 'receivables',
            'CashAndCashEquivalentsAtCarryingValue': 'cash',
            'WeightedAverageNumberOfSharesOutstandingBasic': 'shares_outstanding',
            'CommonStockSharesOutstanding': 'shares_outstanding'
        }
        
        return concept_mapping.get(concept, concept.lower())
    
    def _get_metric_value(self, metrics: Dict[str, MetricResult], metric_name: str) -> Optional[float]:
        """Get metric value from results dictionary"""
        return metrics.get(metric_name, {}).value if metric_name in metrics else None
    
    def get_metrics_summary(self, period: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of all calculated metrics organized by category"""
        all_metrics = self.calculate_all_metrics(period)
        
        summary = {
            'profitability': {},
            'liquidity': {},
            'leverage': {},
            'efficiency': {},
            'market': {},
            'data_quality': {
                'good': 0,
                'estimated': 0,
                'poor': 0,
                'unavailable': 0
            }
        }
        
        for metric_name, result in all_metrics.items():
            category = result.category
            if category in summary:
                summary[category][metric_name] = {
                    'value': result.value,
                    'unit': result.unit,
                    'description': result.description,
                    'data_quality': result.data_quality
                }
            
            # Update data quality counts
            summary['data_quality'][result.data_quality] += 1
        
        return summary