"""
Financial Trend Analyzer

Analyzes horizontal trends across multiple periods to show growth patterns
and business momentum.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import date, datetime
import statistics

from ..models import FilingData, FinancialFact, PeriodType
from ..utils.logging import get_logger
from ..utils.context_mapper import ContextMapper

logger = get_logger(__name__)


@dataclass
class TrendPoint:
    """A single point in a trend analysis"""
    period: str
    value: float
    period_start: Optional[date] = None
    period_end: Optional[date] = None


@dataclass
class TrendAnalysis:
    """Complete trend analysis for a financial metric"""
    metric_name: str
    unit: str
    data_points: List[TrendPoint]
    
    # Growth metrics
    total_growth_rate: Optional[float] = None  # Total growth over period
    cagr: Optional[float] = None  # Compound Annual Growth Rate
    average_growth_rate: Optional[float] = None  # Average period-over-period growth
    
    # Trend characteristics
    trend_direction: str = "stable"  # "growing", "declining", "stable", "volatile"
    volatility: Optional[float] = None  # Standard deviation of growth rates
    
    # Insights
    insights: List[str] = None
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []


@dataclass
class ComprehensiveTrendReport:
    """Complete trend analysis report"""
    company_name: str
    analysis_period: str
    
    # Core business metrics trends
    revenue_trend: Optional[TrendAnalysis] = None
    profit_trend: Optional[TrendAnalysis] = None
    cash_flow_trend: Optional[TrendAnalysis] = None
    
    # Efficiency trends
    margin_trends: Dict[str, TrendAnalysis] = None
    return_trends: Dict[str, TrendAnalysis] = None
    
    # Growth summary
    overall_growth_score: float = 0.0
    growth_quality_score: float = 0.0
    
    # Key insights
    executive_summary: List[str] = None
    
    def __post_init__(self):
        if self.margin_trends is None:
            self.margin_trends = {}
        if self.return_trends is None:
            self.return_trends = {}
        if self.executive_summary is None:
            self.executive_summary = []


class TrendAnalyzer:
    """
    Analyzes financial trends across multiple periods to identify
    growth patterns and business momentum
    """
    
    def __init__(self, filing_data: FilingData):
        self.filing_data = filing_data
        self.facts_by_concept = self._index_facts_by_concept_and_period()
        self.context_mapper = ContextMapper(filing_data.all_facts)
    
    def _index_facts_by_concept_and_period(self) -> Dict[str, Dict[str, FinancialFact]]:
        """Index facts by concept and period for trend analysis"""
        index = {}
        for fact in self.filing_data.all_facts:
            concept = fact.concept.split(':')[-1]  # Remove namespace prefix
            if concept not in index:
                index[concept] = {}
            
            # Use period as key
            period_key = fact.period
            index[concept][period_key] = fact
        
        return index
    
    def analyze_revenue_trend(self) -> TrendAnalysis:
        """Analyze revenue growth trend"""
        return self._analyze_metric_trend(
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            '营业收入趋势'
        )
    
    def analyze_profit_trend(self) -> TrendAnalysis:
        """Analyze profit growth trend"""
        return self._analyze_metric_trend(
            'NetIncomeLoss',
            '净利润趋势'
        )
    
    def analyze_cash_flow_trend(self) -> TrendAnalysis:
        """Analyze cash flow trend"""
        return self._analyze_metric_trend(
            'NetCashProvidedByUsedInOperatingActivities',
            '经营现金流趋势'
        )
    
    def analyze_margin_trends(self) -> Dict[str, TrendAnalysis]:
        """Analyze various margin trends"""
        margins = {}
        
        # Get revenue data for margin calculations
        revenue_data = self._get_time_series_data('RevenueFromContractWithCustomerExcludingAssessedTax')
        
        if revenue_data:
            # Gross margin trend
            cost_data = self._get_time_series_data('CostOfGoodsAndServicesSold')
            if cost_data:
                gross_margin_data = []
                for period in revenue_data:
                    if period in cost_data:
                        revenue = revenue_data[period]
                        cost = cost_data[period]
                        if revenue and cost and revenue != 0:
                            margin = (revenue - cost) / revenue * 100
                            gross_margin_data.append(TrendPoint(period, margin))
                
                if gross_margin_data:
                    margins['gross_margin'] = self._create_trend_analysis(
                        gross_margin_data, '毛利率趋势', '%'
                    )
            
            # Operating margin trend
            operating_income_data = self._get_time_series_data('OperatingIncomeLoss')
            if operating_income_data:
                operating_margin_data = []
                for period in revenue_data:
                    if period in operating_income_data:
                        revenue = revenue_data[period]
                        operating_income = operating_income_data[period]
                        if revenue and operating_income and revenue != 0:
                            margin = operating_income / revenue * 100
                            operating_margin_data.append(TrendPoint(period, margin))
                
                if operating_margin_data:
                    margins['operating_margin'] = self._create_trend_analysis(
                        operating_margin_data, '营业利润率趋势', '%'
                    )
            
            # Net margin trend
            net_income_data = self._get_time_series_data('NetIncomeLoss')
            if net_income_data:
                net_margin_data = []
                for period in revenue_data:
                    if period in net_income_data:
                        revenue = revenue_data[period]
                        net_income = net_income_data[period]
                        if revenue and net_income and revenue != 0:
                            margin = net_income / revenue * 100
                            net_margin_data.append(TrendPoint(period, margin))
                
                if net_margin_data:
                    margins['net_margin'] = self._create_trend_analysis(
                        net_margin_data, '净利润率趋势', '%'
                    )
        
        return margins
    
    def analyze_return_trends(self) -> Dict[str, TrendAnalysis]:
        """Analyze return on investment trends"""
        returns = {}
        
        # ROE trend
        net_income_data = self._get_time_series_data('NetIncomeLoss')
        equity_data = self._get_time_series_data('StockholdersEquity')
        
        if net_income_data and equity_data:
            roe_data = []
            for period in net_income_data:
                if period in equity_data:
                    net_income = net_income_data[period]
                    equity = equity_data[period]
                    if net_income and equity and equity != 0:
                        roe = net_income / equity * 100
                        roe_data.append(TrendPoint(period, roe))
            
            if roe_data:
                returns['roe'] = self._create_trend_analysis(
                    roe_data, '股东权益回报率趋势', '%'
                )
        
        # ROA trend
        assets_data = self._get_time_series_data('Assets')
        if net_income_data and assets_data:
            roa_data = []
            for period in net_income_data:
                if period in assets_data:
                    net_income = net_income_data[period]
                    assets = assets_data[period]
                    if net_income and assets and assets != 0:
                        roa = net_income / assets * 100
                        roa_data.append(TrendPoint(period, roa))
            
            if roa_data:
                returns['roa'] = self._create_trend_analysis(
                    roa_data, '资产回报率趋势', '%'
                )
        
        return returns
    
    def generate_comprehensive_report(self) -> ComprehensiveTrendReport:
        """Generate a comprehensive trend analysis report"""
        logger.info("Generating comprehensive trend report")
        
        # Analyze core metrics
        revenue_trend = self.analyze_revenue_trend()
        profit_trend = self.analyze_profit_trend()
        cash_flow_trend = self.analyze_cash_flow_trend()
        
        # Analyze efficiency metrics
        margin_trends = self.analyze_margin_trends()
        return_trends = self.analyze_return_trends()
        
        # Calculate overall scores
        growth_score = self._calculate_growth_score([revenue_trend, profit_trend, cash_flow_trend])
        quality_score = self._calculate_quality_score(margin_trends, return_trends)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            revenue_trend, profit_trend, cash_flow_trend, margin_trends, return_trends
        )
        
        return ComprehensiveTrendReport(
            company_name=self.filing_data.company_info.name,
            analysis_period=f"{len(revenue_trend.data_points) if revenue_trend else 0} periods",
            revenue_trend=revenue_trend,
            profit_trend=profit_trend,
            cash_flow_trend=cash_flow_trend,
            margin_trends=margin_trends,
            return_trends=return_trends,
            overall_growth_score=growth_score,
            growth_quality_score=quality_score,
            executive_summary=executive_summary
        )
    
    def _analyze_metric_trend(self, concept: str, metric_name: str) -> Optional[TrendAnalysis]:
        """Analyze trend for a specific financial metric"""
        time_series_data = self._get_time_series_data(concept)
        if not time_series_data:
            return None
        
        # Convert to TrendPoint objects
        data_points = []
        for period, value in time_series_data.items():
            if value is not None:
                # Try to extract period dates
                period_start, period_end = self._parse_period_dates(period)
                data_points.append(TrendPoint(
                    period=period,
                    value=value,
                    period_start=period_start,
                    period_end=period_end
                ))
        
        # Sort by period end date
        data_points.sort(key=lambda x: x.period_end or date.min)
        
        return self._create_trend_analysis(data_points, metric_name, 'USD')
    
    def _get_time_series_data(self, concept: str) -> Dict[str, float]:
        """Get time series data for a concept with proper context filtering"""
        concept_data = self.facts_by_concept.get(concept, {})
        time_series = {}
        
        for period, fact in concept_data.items():
            # Validate that this is the right type of fact for the concept
            if self._is_valid_fact_for_concept(fact, concept):
                if isinstance(fact.value, (int, float)):
                    value = float(fact.value)
                    # Apply scaling if decimals are specified
                    if fact.decimals is not None:
                        value *= (10 ** fact.decimals)
                    time_series[period] = value
        
        return time_series
    
    def _is_valid_fact_for_concept(self, fact: FinancialFact, concept: str) -> bool:
        """Validate that a fact is appropriate for the given concept"""
        # For revenue and income statement items, prefer duration periods
        if any(keyword in concept.lower() for keyword in ['revenue', 'income', 'expense', 'cost', 'sales']):
            return fact.period_type == PeriodType.DURATION
        
        # For balance sheet items, prefer instant periods
        if any(keyword in concept.lower() for keyword in ['assets', 'liabilities', 'equity', 'cash', 'debt']):
            return fact.period_type == PeriodType.INSTANT
        
        # For other concepts, accept both types
        return True
    
    def get_revenue_for_fiscal_year(self, fiscal_year: int) -> Optional[float]:
        """Get revenue for a specific fiscal year with proper context validation"""
        revenue_concepts = [
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'Revenues'
        ]
        
        for concept in revenue_concepts:
            facts = self.facts_by_concept.get(concept, {})
            
            # Find facts for the specified fiscal year
            for period, fact in facts.items():
                if (fact.period_end and 
                    fact.period_end.year == fiscal_year and 
                    fact.period_type == PeriodType.DURATION):
                    
                    if isinstance(fact.value, (int, float)):
                        value = float(fact.value)
                        if fact.decimals is not None:
                            value *= (10 ** fact.decimals)
                        return value
        
        return None
    
    def _create_trend_analysis(self, data_points: List[TrendPoint], metric_name: str, unit: str) -> TrendAnalysis:
        """Create trend analysis from data points"""
        if len(data_points) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                unit=unit,
                data_points=data_points,
                trend_direction="insufficient_data"
            )
        
        # Calculate growth metrics
        values = [point.value for point in data_points]
        
        # Total growth rate
        total_growth = (values[-1] - values[0]) / abs(values[0]) * 100 if values[0] != 0 else None
        
        # Period-over-period growth rates
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                growth_rate = (values[i] - values[i-1]) / abs(values[i-1]) * 100
                growth_rates.append(growth_rate)
        
        # Average growth rate
        avg_growth = statistics.mean(growth_rates) if growth_rates else None
        
        # CAGR (if we have enough periods)
        cagr = None
        if len(data_points) >= 3 and values[0] != 0:
            years = len(data_points) - 1
            cagr = ((values[-1] / abs(values[0])) ** (1/years) - 1) * 100
        
        # Volatility
        volatility = statistics.stdev(growth_rates) if len(growth_rates) > 1 else None
        
        # Trend direction
        trend_direction = self._determine_trend_direction(growth_rates, volatility)
        
        # Generate insights
        insights = self._generate_trend_insights(
            metric_name, total_growth, avg_growth, cagr, volatility, trend_direction
        )
        
        return TrendAnalysis(
            metric_name=metric_name,
            unit=unit,
            data_points=data_points,
            total_growth_rate=total_growth,
            cagr=cagr,
            average_growth_rate=avg_growth,
            trend_direction=trend_direction,
            volatility=volatility,
            insights=insights
        )
    
    def _parse_period_dates(self, period: str) -> Tuple[Optional[date], Optional[date]]:
        """Parse period string to extract start and end dates"""
        try:
            if '_to_' in period:
                start_str, end_str = period.split('_to_')
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
                return start_date, end_date
            else:
                # Single date
                single_date = datetime.strptime(period, '%Y-%m-%d').date()
                return None, single_date
        except ValueError:
            return None, None
    
    def _determine_trend_direction(self, growth_rates: List[float], volatility: Optional[float]) -> str:
        """Determine overall trend direction"""
        if not growth_rates:
            return "stable"
        
        avg_growth = statistics.mean(growth_rates)
        
        # High volatility threshold
        high_volatility = volatility and volatility > 20
        
        if high_volatility:
            return "volatile"
        elif avg_growth > 5:
            return "growing"
        elif avg_growth < -5:
            return "declining"
        else:
            return "stable"
    
    def _generate_trend_insights(self, metric_name: str, total_growth: Optional[float], 
                                avg_growth: Optional[float], cagr: Optional[float],
                                volatility: Optional[float], trend_direction: str) -> List[str]:
        """Generate insights for trend analysis"""
        insights = []
        
        if total_growth is not None:
            if total_growth > 20:
                insights.append(f"{metric_name}总体增长{total_growth:.1f}%，表现强劲")
            elif total_growth > 0:
                insights.append(f"{metric_name}总体增长{total_growth:.1f}%，保持正增长")
            else:
                insights.append(f"{metric_name}总体下降{abs(total_growth):.1f}%，需要关注")
        
        if cagr is not None:
            if cagr > 15:
                insights.append(f"复合年增长率{cagr:.1f}%，增长动力强劲")
            elif cagr > 5:
                insights.append(f"复合年增长率{cagr:.1f}%，稳健增长")
            elif cagr > 0:
                insights.append(f"复合年增长率{cagr:.1f}%，温和增长")
            else:
                insights.append(f"复合年增长率{cagr:.1f}%，呈下降趋势")
        
        if volatility is not None:
            if volatility > 30:
                insights.append(f"增长波动性较高({volatility:.1f}%)，业绩不够稳定")
            elif volatility > 15:
                insights.append(f"增长波动性适中({volatility:.1f}%)，总体可控")
            else:
                insights.append(f"增长波动性较低({volatility:.1f}%)，业绩稳定")
        
        # Trend direction insights
        if trend_direction == "growing":
            insights.append("整体呈上升趋势，发展势头良好")
        elif trend_direction == "declining":
            insights.append("整体呈下降趋势，需要关注业务调整")
        elif trend_direction == "volatile":
            insights.append("增长波动较大，建议关注业务稳定性")
        
        return insights
    
    def _calculate_growth_score(self, trends: List[Optional[TrendAnalysis]]) -> float:
        """Calculate overall growth score (0-100)"""
        scores = []
        
        for trend in trends:
            if trend and trend.cagr is not None:
                # Score based on CAGR
                if trend.cagr > 20:
                    scores.append(100)
                elif trend.cagr > 15:
                    scores.append(90)
                elif trend.cagr > 10:
                    scores.append(80)
                elif trend.cagr > 5:
                    scores.append(70)
                elif trend.cagr > 0:
                    scores.append(60)
                else:
                    scores.append(max(0, 50 + trend.cagr))  # Negative growth
        
        return statistics.mean(scores) if scores else 50.0
    
    def _calculate_quality_score(self, margin_trends: Dict[str, TrendAnalysis], 
                                return_trends: Dict[str, TrendAnalysis]) -> float:
        """Calculate growth quality score (0-100)"""
        scores = []
        
        # Margin improvement scores
        for trend in margin_trends.values():
            if trend.average_growth_rate is not None:
                if trend.average_growth_rate > 2:
                    scores.append(90)
                elif trend.average_growth_rate > 0:
                    scores.append(70)
                else:
                    scores.append(30)
        
        # Return improvement scores
        for trend in return_trends.values():
            if trend.average_growth_rate is not None:
                if trend.average_growth_rate > 2:
                    scores.append(90)
                elif trend.average_growth_rate > 0:
                    scores.append(70)
                else:
                    scores.append(30)
        
        return statistics.mean(scores) if scores else 50.0
    
    def _generate_executive_summary(self, revenue_trend: Optional[TrendAnalysis],
                                  profit_trend: Optional[TrendAnalysis],
                                  cash_flow_trend: Optional[TrendAnalysis],
                                  margin_trends: Dict[str, TrendAnalysis],
                                  return_trends: Dict[str, TrendAnalysis]) -> List[str]:
        """Generate executive summary"""
        summary = []
        
        # Revenue summary
        if revenue_trend and revenue_trend.cagr:
            summary.append(f"营收复合增长率{revenue_trend.cagr:.1f}%，{'增长强劲' if revenue_trend.cagr > 10 else '稳健增长' if revenue_trend.cagr > 5 else '增长放缓'}")
        
        # Profitability summary
        if profit_trend and profit_trend.cagr:
            profit_performance = '盈利能力提升' if (revenue_trend and profit_trend.cagr > revenue_trend.cagr) or not revenue_trend else '盈利增长滞后'
            summary.append(f"利润复合增长率{profit_trend.cagr:.1f}%，{profit_performance}")
        
        # Margin trends summary
        if 'net_margin' in margin_trends:
            net_margin_trend = margin_trends['net_margin']
            if net_margin_trend.trend_direction == "growing":
                summary.append("净利润率呈上升趋势，运营效率改善")
            elif net_margin_trend.trend_direction == "declining":
                summary.append("净利润率呈下降趋势，需关注成本控制")
        
        # Cash flow summary
        if cash_flow_trend and cash_flow_trend.trend_direction == "growing":
            summary.append("现金流增长良好，财务状况健康")
        
        return summary