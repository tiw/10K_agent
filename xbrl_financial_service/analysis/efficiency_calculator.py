"""
Efficiency Calculator

Calculates conversion rates, margin analysis, and efficiency metrics
for comprehensive financial performance evaluation.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

from ..models import FilingData, FinancialFact
from ..utils.logging import get_logger
from ..utils.context_mapper import ContextMapper

logger = get_logger(__name__)


class EfficiencyType(Enum):
    """Types of efficiency metrics"""
    CONVERSION_RATE = "conversion_rate"
    MARGIN_EFFICIENCY = "margin_efficiency"
    CAPITAL_EFFICIENCY = "capital_efficiency"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    CASH_EFFICIENCY = "cash_efficiency"


@dataclass
class EfficiencyMetric:
    """Individual efficiency metric"""
    name: str
    value: float
    unit: str
    period: str
    
    # Benchmarking
    benchmark_value: Optional[float] = None
    performance_rating: Optional[str] = None  # "excellent", "good", "average", "poor"
    
    # Context
    description: str = ""
    interpretation: str = ""


@dataclass
class ConversionAnalysis:
    """Analysis of conversion rates through business funnel"""
    funnel_name: str
    period: str
    
    # Conversion stages
    stages: List[Tuple[str, float, float]]  # (stage_name, value, conversion_rate)
    
    # Overall metrics
    total_conversion_rate: float
    efficiency_score: float  # 0-100
    
    # Insights
    bottlenecks: List[str]
    improvement_opportunities: List[str]


@dataclass
class MarginAnalysis:
    """Comprehensive margin analysis"""
    period: str
    
    # Core margins
    gross_margin: Optional[EfficiencyMetric] = None
    operating_margin: Optional[EfficiencyMetric] = None
    net_margin: Optional[EfficiencyMetric] = None
    ebitda_margin: Optional[EfficiencyMetric] = None
    
    # Advanced margins
    contribution_margin: Optional[EfficiencyMetric] = None
    cash_margin: Optional[EfficiencyMetric] = None
    
    # Margin trends
    margin_stability: float = 0.0  # Lower is more stable
    margin_improvement: float = 0.0  # Period-over-period improvement
    
    # Insights
    key_insights: List[str] = None
    
    def __post_init__(self):
        if self.key_insights is None:
            self.key_insights = []


@dataclass
class CapitalEfficiencyAnalysis:
    """Analysis of capital deployment efficiency"""
    period: str
    
    # Return metrics
    roe: Optional[EfficiencyMetric] = None
    roa: Optional[EfficiencyMetric] = None
    roic: Optional[EfficiencyMetric] = None
    
    # Turnover metrics
    asset_turnover: Optional[EfficiencyMetric] = None
    inventory_turnover: Optional[EfficiencyMetric] = None
    receivables_turnover: Optional[EfficiencyMetric] = None
    
    # Efficiency ratios
    working_capital_efficiency: Optional[EfficiencyMetric] = None
    capital_allocation_efficiency: Optional[EfficiencyMetric] = None
    
    # Overall assessment
    capital_efficiency_score: float = 0.0
    key_insights: List[str] = None
    
    def __post_init__(self):
        if self.key_insights is None:
            self.key_insights = []


class EfficiencyCalculator:
    """
    Calculates various efficiency metrics including conversion rates,
    margins, and capital deployment efficiency
    """
    
    def __init__(self, filing_data: FilingData):
        self.filing_data = filing_data
        self.facts_by_concept = self._index_facts_by_concept()
        self.context_mapper = ContextMapper(filing_data.all_facts)
        
        # Benchmark values for performance rating
        self.benchmarks = self._load_industry_benchmarks()
    
    def _index_facts_by_concept(self) -> Dict[str, List[FinancialFact]]:
        """Index facts by concept for quick lookup"""
        index = {}
        for fact in self.filing_data.all_facts:
            concept = fact.concept.split(':')[-1]  # Remove namespace prefix
            if concept not in index:
                index[concept] = []
            index[concept].append(fact)
        return index
    
    def _load_industry_benchmarks(self) -> Dict[str, float]:
        """Load industry benchmark values for performance comparison"""
        # These would typically come from external data sources
        # For now, using technology industry averages
        return {
            'gross_margin': 65.0,  # 65% for tech companies
            'operating_margin': 25.0,  # 25% for tech companies
            'net_margin': 20.0,  # 20% for tech companies
            'roe': 15.0,  # 15% ROE
            'roa': 10.0,  # 10% ROA
            'asset_turnover': 0.8,  # 0.8x asset turnover
            'cash_conversion_rate': 25.0,  # 25% cash conversion
            'revenue_to_cash_conversion': 20.0  # 20% revenue to cash
        }
    
    def calculate_conversion_rates(self, period: Optional[str] = None) -> ConversionAnalysis:
        """
        Calculate conversion rates through the business funnel:
        Revenue → Operating Income → Net Income → Cash Flow → Free Cash Flow
        """
        logger.info("Calculating conversion rates")
        
        # Get key financial metrics
        revenue = self._get_latest_value('RevenueFromContractWithCustomerExcludingAssessedTax', period)
        operating_income = self._get_latest_value('OperatingIncomeLoss', period)
        net_income = self._get_latest_value('NetIncomeLoss', period)
        operating_cash_flow = self._get_latest_value('NetCashProvidedByUsedInOperatingActivities', period)
        capex = self._get_latest_value('PaymentsToAcquirePropertyPlantAndEquipment', period)
        free_cash_flow = operating_cash_flow - capex if operating_cash_flow and capex else None
        
        stages = []
        conversion_rates = []
        
        if revenue:
            stages.append(("营业收入", revenue, 100.0))
            
            if operating_income:
                op_conversion = (operating_income / revenue) * 100
                stages.append(("营业利润", operating_income, op_conversion))
                conversion_rates.append(op_conversion)
                
                if net_income:
                    net_conversion = (net_income / revenue) * 100
                    stages.append(("净利润", net_income, net_conversion))
                    conversion_rates.append(net_conversion)
                    
                    if operating_cash_flow:
                        cash_conversion = (operating_cash_flow / revenue) * 100
                        stages.append(("经营现金流", operating_cash_flow, cash_conversion))
                        conversion_rates.append(cash_conversion)
                        
                        if free_cash_flow:
                            fcf_conversion = (free_cash_flow / revenue) * 100
                            stages.append(("自由现金流", free_cash_flow, fcf_conversion))
                            conversion_rates.append(fcf_conversion)
        
        # Calculate overall metrics
        total_conversion = conversion_rates[-1] if conversion_rates else 0.0
        efficiency_score = self._calculate_conversion_efficiency_score(conversion_rates)
        
        # Identify bottlenecks and opportunities
        bottlenecks = self._identify_conversion_bottlenecks(stages)
        opportunities = self._identify_improvement_opportunities(stages)
        
        return ConversionAnalysis(
            funnel_name="业务转换漏斗",
            period=period or "Latest",
            stages=stages,
            total_conversion_rate=total_conversion,
            efficiency_score=efficiency_score,
            bottlenecks=bottlenecks,
            improvement_opportunities=opportunities
        )
    
    def calculate_margin_analysis(self, period: Optional[str] = None) -> MarginAnalysis:
        """Calculate comprehensive margin analysis"""
        logger.info("Calculating margin analysis")
        
        # Get financial data
        revenue = self._get_latest_value('RevenueFromContractWithCustomerExcludingAssessedTax', period)
        cost_of_sales = self._get_latest_value('CostOfGoodsAndServicesSold', period)
        operating_income = self._get_latest_value('OperatingIncomeLoss', period)
        net_income = self._get_latest_value('NetIncomeLoss', period)
        ebitda = self._calculate_ebitda(period)
        operating_cash_flow = self._get_latest_value('NetCashProvidedByUsedInOperatingActivities', period)
        
        analysis = MarginAnalysis(period=period or "Latest")
        
        if revenue and revenue != 0:
            # Gross margin
            if cost_of_sales:
                gross_profit = revenue - cost_of_sales
                gross_margin_pct = (gross_profit / revenue) * 100
                analysis.gross_margin = EfficiencyMetric(
                    name="毛利率",
                    value=gross_margin_pct,
                    unit="%",
                    period=period or "Latest",
                    benchmark_value=self.benchmarks.get('gross_margin'),
                    performance_rating=self._rate_performance(gross_margin_pct, self.benchmarks.get('gross_margin')),
                    description="毛利润占营业收入的比例",
                    interpretation=self._interpret_gross_margin(gross_margin_pct)
                )
            
            # Operating margin
            if operating_income:
                operating_margin_pct = (operating_income / revenue) * 100
                analysis.operating_margin = EfficiencyMetric(
                    name="营业利润率",
                    value=operating_margin_pct,
                    unit="%",
                    period=period or "Latest",
                    benchmark_value=self.benchmarks.get('operating_margin'),
                    performance_rating=self._rate_performance(operating_margin_pct, self.benchmarks.get('operating_margin')),
                    description="营业利润占营业收入的比例",
                    interpretation=self._interpret_operating_margin(operating_margin_pct)
                )
            
            # Net margin
            if net_income:
                net_margin_pct = (net_income / revenue) * 100
                analysis.net_margin = EfficiencyMetric(
                    name="净利润率",
                    value=net_margin_pct,
                    unit="%",
                    period=period or "Latest",
                    benchmark_value=self.benchmarks.get('net_margin'),
                    performance_rating=self._rate_performance(net_margin_pct, self.benchmarks.get('net_margin')),
                    description="净利润占营业收入的比例",
                    interpretation=self._interpret_net_margin(net_margin_pct)
                )
            
            # EBITDA margin
            if ebitda:
                ebitda_margin_pct = (ebitda / revenue) * 100
                analysis.ebitda_margin = EfficiencyMetric(
                    name="EBITDA利润率",
                    value=ebitda_margin_pct,
                    unit="%",
                    period=period or "Latest",
                    description="EBITDA占营业收入的比例",
                    interpretation=self._interpret_ebitda_margin(ebitda_margin_pct)
                )
            
            # Cash margin
            if operating_cash_flow:
                cash_margin_pct = (operating_cash_flow / revenue) * 100
                analysis.cash_margin = EfficiencyMetric(
                    name="现金利润率",
                    value=cash_margin_pct,
                    unit="%",
                    period=period or "Latest",
                    benchmark_value=self.benchmarks.get('cash_conversion_rate'),
                    performance_rating=self._rate_performance(cash_margin_pct, self.benchmarks.get('cash_conversion_rate')),
                    description="经营现金流占营业收入的比例",
                    interpretation=self._interpret_cash_margin(cash_margin_pct)
                )
        
        # Generate insights
        analysis.key_insights = self._generate_margin_insights(analysis)
        
        return analysis
    
    def calculate_capital_efficiency(self, period: Optional[str] = None) -> CapitalEfficiencyAnalysis:
        """Calculate capital deployment efficiency metrics"""
        logger.info("Calculating capital efficiency")
        
        # Get financial data
        net_income = self._get_latest_value('NetIncomeLoss', period)
        total_assets = self._get_latest_value('Assets', period)
        shareholders_equity = self._get_latest_value('StockholdersEquity', period)
        revenue = self._get_latest_value('RevenueFromContractWithCustomerExcludingAssessedTax', period)
        inventory = self._get_latest_value('InventoryNet', period)
        receivables = self._get_latest_value('AccountsReceivableNetCurrent', period)
        cost_of_sales = self._get_latest_value('CostOfGoodsAndServicesSold', period)
        
        analysis = CapitalEfficiencyAnalysis(period=period or "Latest")
        
        # ROE (Return on Equity)
        if net_income and shareholders_equity and shareholders_equity != 0:
            roe_pct = (net_income / shareholders_equity) * 100
            analysis.roe = EfficiencyMetric(
                name="股东权益回报率 (ROE)",
                value=roe_pct,
                unit="%",
                period=period or "Latest",
                benchmark_value=self.benchmarks.get('roe'),
                performance_rating=self._rate_performance(roe_pct, self.benchmarks.get('roe')),
                description="净利润相对于股东权益的回报率",
                interpretation=self._interpret_roe(roe_pct)
            )
        
        # ROA (Return on Assets)
        if net_income and total_assets and total_assets != 0:
            roa_pct = (net_income / total_assets) * 100
            analysis.roa = EfficiencyMetric(
                name="资产回报率 (ROA)",
                value=roa_pct,
                unit="%",
                period=period or "Latest",
                benchmark_value=self.benchmarks.get('roa'),
                performance_rating=self._rate_performance(roa_pct, self.benchmarks.get('roa')),
                description="净利润相对于总资产的回报率",
                interpretation=self._interpret_roa(roa_pct)
            )
        
        # Asset Turnover
        if revenue and total_assets and total_assets != 0:
            asset_turnover_ratio = revenue / total_assets
            analysis.asset_turnover = EfficiencyMetric(
                name="资产周转率",
                value=asset_turnover_ratio,
                unit="倍",
                period=period or "Latest",
                benchmark_value=self.benchmarks.get('asset_turnover'),
                performance_rating=self._rate_performance(asset_turnover_ratio, self.benchmarks.get('asset_turnover')),
                description="营业收入相对于总资产的周转效率",
                interpretation=self._interpret_asset_turnover(asset_turnover_ratio)
            )
        
        # Inventory Turnover
        if cost_of_sales and inventory and inventory != 0:
            inventory_turnover_ratio = cost_of_sales / inventory
            analysis.inventory_turnover = EfficiencyMetric(
                name="存货周转率",
                value=inventory_turnover_ratio,
                unit="倍",
                period=period or "Latest",
                description="销售成本相对于存货的周转效率",
                interpretation=self._interpret_inventory_turnover(inventory_turnover_ratio)
            )
        
        # Receivables Turnover
        if revenue and receivables and receivables != 0:
            receivables_turnover_ratio = revenue / receivables
            analysis.receivables_turnover = EfficiencyMetric(
                name="应收账款周转率",
                value=receivables_turnover_ratio,
                unit="倍",
                period=period or "Latest",
                description="营业收入相对于应收账款的周转效率",
                interpretation=self._interpret_receivables_turnover(receivables_turnover_ratio)
            )
        
        # Calculate overall capital efficiency score
        analysis.capital_efficiency_score = self._calculate_capital_efficiency_score(analysis)
        
        # Generate insights
        analysis.key_insights = self._generate_capital_efficiency_insights(analysis)
        
        return analysis
    
    def get_comprehensive_efficiency_report(self, period: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive efficiency analysis report"""
        logger.info("Generating comprehensive efficiency report")
        
        return {
            'conversion_analysis': self.calculate_conversion_rates(period),
            'margin_analysis': self.calculate_margin_analysis(period),
            'capital_efficiency': self.calculate_capital_efficiency(period),
            'summary': self._generate_efficiency_summary(period)
        }
    
    def _get_latest_value(self, concept: str, period: Optional[str] = None) -> Optional[float]:
        """Get the latest value for a financial concept using Context ID mapping"""
        # If period is specified as a fiscal year, use context mapper
        if period and period.isdigit():
            fiscal_year = int(period)
            # Determine if this is a revenue/income statement concept or balance sheet concept
            prefer_duration = any(term in concept.lower() for term in ['revenue', 'income', 'expense', 'cost', 'sales', 'cash'])
            return self.context_mapper.get_concept_value_for_year(concept, fiscal_year, prefer_duration)
        
        # Fallback to original method for backward compatibility
        facts = self.facts_by_concept.get(concept, [])
        if not facts:
            return None
        
        # Filter by period if specified
        if period:
            facts = [f for f in facts if period in f.period]
        
        # Get the most recent fact
        if facts:
            latest_fact = max(facts, key=lambda f: f.period_end or f.period)
            if isinstance(latest_fact.value, (int, float)):
                value = float(latest_fact.value)
                # Apply scaling if decimals are specified
                if latest_fact.decimals is not None:
                    value *= (10 ** latest_fact.decimals)
                return value
        
        return None
    
    def get_value_for_fiscal_year(self, concept: str, fiscal_year: int) -> Optional[float]:
        """Get value for a concept using Context ID mapping for a specific fiscal year"""
        prefer_duration = any(term in concept.lower() for term in ['revenue', 'income', 'expense', 'cost', 'sales', 'cash'])
        return self.context_mapper.get_concept_value_for_year(concept, fiscal_year, prefer_duration)
    
    def _calculate_ebitda(self, period: Optional[str] = None) -> Optional[float]:
        """Calculate EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization)"""
        operating_income = self._get_latest_value('OperatingIncomeLoss', period)
        depreciation = self._get_latest_value('DepreciationDepletionAndAmortization', period)
        
        if operating_income:
            ebitda = operating_income
            if depreciation:
                ebitda += depreciation
            return ebitda
        
        return None
    
    def _rate_performance(self, value: float, benchmark: Optional[float]) -> str:
        """Rate performance against benchmark"""
        if not benchmark:
            return "无基准"
        
        ratio = value / benchmark
        if ratio >= 1.2:
            return "优秀"
        elif ratio >= 1.0:
            return "良好"
        elif ratio >= 0.8:
            return "一般"
        else:
            return "偏低"
    
    def _calculate_conversion_efficiency_score(self, conversion_rates: List[float]) -> float:
        """Calculate overall conversion efficiency score (0-100)"""
        if not conversion_rates:
            return 0.0
        
        # Weight later stages more heavily as they represent end-to-end efficiency
        weights = [1.0, 1.5, 2.0, 2.5, 3.0][:len(conversion_rates)]
        
        weighted_scores = []
        for i, rate in enumerate(conversion_rates):
            # Score based on conversion rate
            if rate > 30:
                score = 100
            elif rate > 20:
                score = 90
            elif rate > 15:
                score = 80
            elif rate > 10:
                score = 70
            elif rate > 5:
                score = 60
            else:
                score = max(0, 50 + rate)
            
            weighted_scores.append(score * weights[i])
        
        total_weight = sum(weights[:len(conversion_rates)])
        return sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
    
    def _identify_conversion_bottlenecks(self, stages: List[Tuple[str, float, float]]) -> List[str]:
        """Identify bottlenecks in the conversion funnel"""
        bottlenecks = []
        
        for i in range(1, len(stages)):
            stage_name, value, conversion_rate = stages[i]
            
            if conversion_rate < 10:
                bottlenecks.append(f"{stage_name}转换率过低({conversion_rate:.1f}%)，需要重点关注")
            elif conversion_rate < 20:
                bottlenecks.append(f"{stage_name}转换率偏低({conversion_rate:.1f}%)，有改善空间")
        
        return bottlenecks
    
    def _identify_improvement_opportunities(self, stages: List[Tuple[str, float, float]]) -> List[str]:
        """Identify improvement opportunities"""
        opportunities = []
        
        if len(stages) >= 2:
            # Check for large drops between stages
            for i in range(1, len(stages)):
                prev_rate = stages[i-1][2]
                curr_rate = stages[i][2]
                drop = prev_rate - curr_rate
                
                if drop > 20:
                    opportunities.append(f"从{stages[i-1][0]}到{stages[i][0]}转换率下降{drop:.1f}%，存在显著改善机会")
                elif drop > 10:
                    opportunities.append(f"从{stages[i-1][0]}到{stages[i][0]}可以进一步优化转换效率")
        
        return opportunities
    
    def _calculate_capital_efficiency_score(self, analysis: CapitalEfficiencyAnalysis) -> float:
        """Calculate overall capital efficiency score"""
        scores = []
        
        if analysis.roe and analysis.roe.benchmark_value:
            roe_score = min(100, (analysis.roe.value / analysis.roe.benchmark_value) * 100)
            scores.append(roe_score)
        
        if analysis.roa and analysis.roa.benchmark_value:
            roa_score = min(100, (analysis.roa.value / analysis.roa.benchmark_value) * 100)
            scores.append(roa_score)
        
        if analysis.asset_turnover and analysis.asset_turnover.benchmark_value:
            turnover_score = min(100, (analysis.asset_turnover.value / analysis.asset_turnover.benchmark_value) * 100)
            scores.append(turnover_score)
        
        return statistics.mean(scores) if scores else 50.0
    
    # Interpretation methods
    def _interpret_gross_margin(self, margin: float) -> str:
        if margin > 70:
            return "毛利率优秀，产品定价能力强，成本控制良好"
        elif margin > 50:
            return "毛利率良好，具有一定的定价优势"
        elif margin > 30:
            return "毛利率一般，需要关注成本控制或提升产品价值"
        else:
            return "毛利率偏低，成本压力较大，需要优化成本结构"
    
    def _interpret_operating_margin(self, margin: float) -> str:
        if margin > 30:
            return "营业利润率优秀，运营效率很高"
        elif margin > 20:
            return "营业利润率良好，运营管理有效"
        elif margin > 10:
            return "营业利润率一般，运营效率有提升空间"
        else:
            return "营业利润率偏低，需要改善运营效率"
    
    def _interpret_net_margin(self, margin: float) -> str:
        if margin > 25:
            return "净利润率优秀，整体盈利能力强"
        elif margin > 15:
            return "净利润率良好，盈利能力稳健"
        elif margin > 5:
            return "净利润率一般，盈利能力有待提升"
        else:
            return "净利润率偏低，盈利能力需要改善"
    
    def _interpret_ebitda_margin(self, margin: float) -> str:
        if margin > 35:
            return "EBITDA利润率优秀，核心业务盈利能力强"
        elif margin > 25:
            return "EBITDA利润率良好，业务盈利能力稳健"
        elif margin > 15:
            return "EBITDA利润率一般，核心业务有改善空间"
        else:
            return "EBITDA利润率偏低，核心业务盈利能力需要提升"
    
    def _interpret_cash_margin(self, margin: float) -> str:
        if margin > 30:
            return "现金利润率优秀，现金创造能力强"
        elif margin > 20:
            return "现金利润率良好，现金流健康"
        elif margin > 10:
            return "现金利润率一般，现金流管理有改善空间"
        else:
            return "现金利润率偏低，需要关注现金流管理"
    
    def _interpret_roe(self, roe: float) -> str:
        if roe > 20:
            return "股东权益回报率优秀，为股东创造高价值"
        elif roe > 15:
            return "股东权益回报率良好，股东回报稳健"
        elif roe > 10:
            return "股东权益回报率一般，股东回报有提升空间"
        else:
            return "股东权益回报率偏低，需要提升股东价值创造"
    
    def _interpret_roa(self, roa: float) -> str:
        if roa > 15:
            return "资产回报率优秀，资产利用效率很高"
        elif roa > 10:
            return "资产回报率良好，资产管理有效"
        elif roa > 5:
            return "资产回报率一般，资产利用效率有改善空间"
        else:
            return "资产回报率偏低，需要提升资产利用效率"
    
    def _interpret_asset_turnover(self, turnover: float) -> str:
        if turnover > 1.5:
            return "资产周转率优秀，资产利用效率很高"
        elif turnover > 1.0:
            return "资产周转率良好，资产利用合理"
        elif turnover > 0.5:
            return "资产周转率一般，资产利用效率有提升空间"
        else:
            return "资产周转率偏低，资产利用效率需要改善"
    
    def _interpret_inventory_turnover(self, turnover: float) -> str:
        if turnover > 12:
            return "存货周转率优秀，库存管理高效"
        elif turnover > 8:
            return "存货周转率良好，库存控制有效"
        elif turnover > 4:
            return "存货周转率一般，库存管理有改善空间"
        else:
            return "存货周转率偏低，需要优化库存管理"
    
    def _interpret_receivables_turnover(self, turnover: float) -> str:
        if turnover > 12:
            return "应收账款周转率优秀，回款效率很高"
        elif turnover > 8:
            return "应收账款周转率良好，回款管理有效"
        elif turnover > 4:
            return "应收账款周转率一般，回款效率有提升空间"
        else:
            return "应收账款周转率偏低，需要加强回款管理"
    
    def _generate_margin_insights(self, analysis: MarginAnalysis) -> List[str]:
        """Generate insights for margin analysis"""
        insights = []
        
        if analysis.gross_margin:
            insights.append(f"毛利率{analysis.gross_margin.value:.1f}%，{analysis.gross_margin.interpretation}")
        
        if analysis.operating_margin:
            insights.append(f"营业利润率{analysis.operating_margin.value:.1f}%，{analysis.operating_margin.interpretation}")
        
        if analysis.net_margin:
            insights.append(f"净利润率{analysis.net_margin.value:.1f}%，{analysis.net_margin.interpretation}")
        
        # Compare margins for insights
        if analysis.gross_margin and analysis.operating_margin:
            margin_drop = analysis.gross_margin.value - analysis.operating_margin.value
            if margin_drop > 40:
                insights.append(f"毛利率到营业利润率下降{margin_drop:.1f}%，运营费用占比较高")
            elif margin_drop > 20:
                insights.append(f"毛利率到营业利润率下降{margin_drop:.1f}%，运营费用控制适中")
        
        return insights
    
    def _generate_capital_efficiency_insights(self, analysis: CapitalEfficiencyAnalysis) -> List[str]:
        """Generate insights for capital efficiency analysis"""
        insights = []
        
        if analysis.roe:
            insights.append(f"股东权益回报率{analysis.roe.value:.1f}%，{analysis.roe.interpretation}")
        
        if analysis.roa:
            insights.append(f"资产回报率{analysis.roa.value:.1f}%，{analysis.roa.interpretation}")
        
        if analysis.asset_turnover:
            insights.append(f"资产周转率{analysis.asset_turnover.value:.1f}倍，{analysis.asset_turnover.interpretation}")
        
        # DuPont analysis insight
        if analysis.roe and analysis.roa and analysis.asset_turnover:
            leverage_multiplier = analysis.roe.value / analysis.roa.value if analysis.roa.value != 0 else 0
            if leverage_multiplier > 2:
                insights.append(f"财务杠杆倍数{leverage_multiplier:.1f}，使用适度财务杠杆提升股东回报")
            elif leverage_multiplier > 1.5:
                insights.append(f"财务杠杆倍数{leverage_multiplier:.1f}，财务结构相对保守")
        
        return insights
    
    def _generate_efficiency_summary(self, period: Optional[str] = None) -> Dict[str, Any]:
        """Generate efficiency analysis summary"""
        conversion = self.calculate_conversion_rates(period)
        margin = self.calculate_margin_analysis(period)
        capital = self.calculate_capital_efficiency(period)
        
        return {
            'overall_efficiency_score': (conversion.efficiency_score + capital.capital_efficiency_score) / 2,
            'key_strengths': self._identify_key_strengths(conversion, margin, capital),
            'improvement_areas': self._identify_improvement_areas(conversion, margin, capital),
            'executive_summary': self._generate_executive_summary(conversion, margin, capital)
        }
    
    def _identify_key_strengths(self, conversion: ConversionAnalysis, 
                              margin: MarginAnalysis, capital: CapitalEfficiencyAnalysis) -> List[str]:
        """Identify key efficiency strengths"""
        strengths = []
        
        if conversion.efficiency_score > 80:
            strengths.append("业务转换效率优秀，各环节协调良好")
        
        if margin.gross_margin and margin.gross_margin.value > 60:
            strengths.append("毛利率水平优秀，产品竞争力强")
        
        if capital.roe and capital.roe.value > 20:
            strengths.append("股东权益回报率优秀，价值创造能力强")
        
        if capital.asset_turnover and capital.asset_turnover.value > 1.2:
            strengths.append("资产周转效率高，资产利用充分")
        
        return strengths
    
    def _identify_improvement_areas(self, conversion: ConversionAnalysis,
                                  margin: MarginAnalysis, capital: CapitalEfficiencyAnalysis) -> List[str]:
        """Identify areas for efficiency improvement"""
        areas = []
        
        if conversion.efficiency_score < 60:
            areas.append("业务转换效率有待提升，需要优化各环节流程")
        
        if margin.operating_margin and margin.operating_margin.value < 15:
            areas.append("营业利润率偏低，需要控制运营成本")
        
        if capital.roa and capital.roa.value < 8:
            areas.append("资产回报率偏低，需要提升资产利用效率")
        
        if margin.cash_margin and margin.cash_margin.value < 15:
            areas.append("现金转换效率偏低，需要改善现金流管理")
        
        return areas
    
    def _generate_executive_summary(self, conversion: ConversionAnalysis,
                                  margin: MarginAnalysis, capital: CapitalEfficiencyAnalysis) -> List[str]:
        """Generate executive summary"""
        summary = []
        
        # Overall efficiency assessment
        avg_score = (conversion.efficiency_score + capital.capital_efficiency_score) / 2
        if avg_score > 80:
            summary.append("整体运营效率优秀，各项指标表现良好")
        elif avg_score > 60:
            summary.append("整体运营效率良好，部分指标有提升空间")
        else:
            summary.append("整体运营效率需要改善，建议重点关注关键指标")
        
        # Key metric highlights
        if margin.net_margin:
            summary.append(f"净利润率{margin.net_margin.value:.1f}%，盈利能力{'强' if margin.net_margin.value > 20 else '一般' if margin.net_margin.value > 10 else '偏弱'}")
        
        if capital.roe:
            summary.append(f"股东权益回报率{capital.roe.value:.1f}%，股东价值创造{'优秀' if capital.roe.value > 20 else '良好' if capital.roe.value > 15 else '一般'}")
        
        return summary 
   
    def calculate_conversion_rates_by_year(self, fiscal_year: int) -> ConversionAnalysis:
        """
        Calculate conversion rates for a specific fiscal year using Context ID mapping
        """
        logger.info(f"Calculating conversion rates for FY{fiscal_year}")
        
        # Get key financial metrics using context mapping
        revenue = self.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', fiscal_year)
        operating_income = self.get_value_for_fiscal_year('OperatingIncomeLoss', fiscal_year)
        net_income = self.get_value_for_fiscal_year('NetIncomeLoss', fiscal_year)
        operating_cash_flow = self.get_value_for_fiscal_year('NetCashProvidedByUsedInOperatingActivities', fiscal_year)
        capex = self.get_value_for_fiscal_year('PaymentsToAcquirePropertyPlantAndEquipment', fiscal_year)
        
        free_cash_flow = operating_cash_flow - capex if operating_cash_flow and capex else None
        
        # Build conversion stages
        stages = []
        if revenue:
            stages.append(("Revenue", revenue, 100.0))
            
            if operating_income:
                conversion_rate = (operating_income / revenue) * 100
                stages.append(("Operating Income", operating_income, conversion_rate))
                
                if net_income:
                    conversion_rate = (net_income / revenue) * 100
                    stages.append(("Net Income", net_income, conversion_rate))
                    
                    if operating_cash_flow:
                        conversion_rate = (operating_cash_flow / revenue) * 100
                        stages.append(("Operating Cash Flow", operating_cash_flow, conversion_rate))
                        
                        if free_cash_flow:
                            conversion_rate = (free_cash_flow / revenue) * 100
                            stages.append(("Free Cash Flow", free_cash_flow, conversion_rate))
        
        # Calculate overall metrics
        total_conversion_rate = (free_cash_flow / revenue * 100) if revenue and free_cash_flow else 0
        efficiency_score = min(100, max(0, total_conversion_rate * 4))  # Scale to 0-100
        
        # Identify bottlenecks and opportunities
        bottlenecks = []
        opportunities = []
        
        if len(stages) >= 2:
            for i in range(1, len(stages)):
                stage_name, _, conversion_rate = stages[i]
                if conversion_rate < 20:
                    bottlenecks.append(f"{stage_name}转换率偏低 ({conversion_rate:.1f}%)")
                elif conversion_rate > 30:
                    opportunities.append(f"{stage_name}表现优秀 ({conversion_rate:.1f}%)")
        
        return ConversionAnalysis(
            funnel_name=f"Business Conversion Funnel FY{fiscal_year}",
            period=f"FY{fiscal_year}",
            stages=stages,
            total_conversion_rate=total_conversion_rate,
            efficiency_score=efficiency_score,
            bottlenecks=bottlenecks,
            improvement_opportunities=opportunities
        )
    
    def calculate_margin_analysis_by_year(self, fiscal_year: int) -> MarginAnalysis:
        """
        Calculate comprehensive margin analysis for a specific fiscal year
        """
        logger.info(f"Calculating margin analysis for FY{fiscal_year}")
        
        # Get financial data using context mapping
        revenue = self.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', fiscal_year)
        cost_of_sales = self.get_value_for_fiscal_year('CostOfGoodsAndServicesSold', fiscal_year)
        operating_income = self.get_value_for_fiscal_year('OperatingIncomeLoss', fiscal_year)
        net_income = self.get_value_for_fiscal_year('NetIncomeLoss', fiscal_year)
        
        ebitda = self._calculate_ebitda_by_year(fiscal_year)
        operating_cash_flow = self.get_value_for_fiscal_year('NetCashProvidedByUsedInOperatingActivities', fiscal_year)
        
        analysis = MarginAnalysis(period=f"FY{fiscal_year}")
        
        if revenue:
            # Gross margin
            if cost_of_sales:
                gross_profit = revenue - cost_of_sales
                gross_margin_pct = (gross_profit / revenue) * 100
                analysis.gross_margin = EfficiencyMetric(
                    name="Gross Margin",
                    value=gross_margin_pct,
                    unit="%",
                    period=f"FY{fiscal_year}",
                    benchmark_value=self.benchmarks.get('gross_margin'),
                    performance_rating=self._rate_performance(gross_margin_pct, self.benchmarks.get('gross_margin', 0)),
                    description="Revenue minus cost of sales as percentage of revenue"
                )
            
            # Operating margin
            if operating_income:
                operating_margin_pct = (operating_income / revenue) * 100
                analysis.operating_margin = EfficiencyMetric(
                    name="Operating Margin",
                    value=operating_margin_pct,
                    unit="%",
                    period=f"FY{fiscal_year}",
                    benchmark_value=self.benchmarks.get('operating_margin'),
                    performance_rating=self._rate_performance(operating_margin_pct, self.benchmarks.get('operating_margin', 0)),
                    description="Operating income as percentage of revenue"
                )
            
            # Net margin
            if net_income:
                net_margin_pct = (net_income / revenue) * 100
                analysis.net_margin = EfficiencyMetric(
                    name="Net Margin",
                    value=net_margin_pct,
                    unit="%",
                    period=f"FY{fiscal_year}",
                    benchmark_value=self.benchmarks.get('net_margin'),
                    performance_rating=self._rate_performance(net_margin_pct, self.benchmarks.get('net_margin', 0)),
                    description="Net income as percentage of revenue"
                )
            
            # EBITDA margin
            if ebitda:
                ebitda_margin_pct = (ebitda / revenue) * 100
                analysis.ebitda_margin = EfficiencyMetric(
                    name="EBITDA Margin",
                    value=ebitda_margin_pct,
                    unit="%",
                    period=f"FY{fiscal_year}",
                    description="EBITDA as percentage of revenue"
                )
            
            # Cash margin
            if operating_cash_flow:
                cash_margin_pct = (operating_cash_flow / revenue) * 100
                analysis.cash_margin = EfficiencyMetric(
                    name="Cash Margin",
                    value=cash_margin_pct,
                    unit="%",
                    period=f"FY{fiscal_year}",
                    benchmark_value=self.benchmarks.get('cash_conversion_rate'),
                    performance_rating=self._rate_performance(cash_margin_pct, self.benchmarks.get('cash_conversion_rate', 0)),
                    description="Operating cash flow as percentage of revenue"
                )
        
        # Generate insights
        analysis.key_insights = self._generate_margin_insights(analysis)
        analysis.key_insights.append(f"数据来源: FY{fiscal_year} Context ID映射")
        
        return analysis
    
    def calculate_capital_efficiency_by_year(self, fiscal_year: int) -> CapitalEfficiencyAnalysis:
        """
        Calculate capital efficiency analysis for a specific fiscal year
        """
        logger.info(f"Calculating capital efficiency for FY{fiscal_year}")
        
        # Get financial data using context mapping
        net_income = self.get_value_for_fiscal_year('NetIncomeLoss', fiscal_year)
        # Balance sheet items use instant context
        total_assets = self.context_mapper.get_concept_value_for_year('Assets', fiscal_year, prefer_duration=False)
        shareholders_equity = self.context_mapper.get_concept_value_for_year('StockholdersEquity', fiscal_year, prefer_duration=False)
        revenue = self.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', fiscal_year)
        inventory = self.context_mapper.get_concept_value_for_year('InventoryNet', fiscal_year, prefer_duration=False)
        receivables = self.context_mapper.get_concept_value_for_year('AccountsReceivableNetCurrent', fiscal_year, prefer_duration=False)
        cost_of_sales = self.get_value_for_fiscal_year('CostOfGoodsAndServicesSold', fiscal_year)
        
        analysis = CapitalEfficiencyAnalysis(period=f"FY{fiscal_year}")
        
        # ROE (Return on Equity)
        if net_income and shareholders_equity and shareholders_equity != 0:
            roe_pct = (net_income / shareholders_equity) * 100
            analysis.roe = EfficiencyMetric(
                name="Return on Equity",
                value=roe_pct,
                unit="%",
                period=f"FY{fiscal_year}",
                benchmark_value=self.benchmarks.get('roe'),
                performance_rating=self._rate_performance(roe_pct, self.benchmarks.get('roe', 0)),
                description="Net income as percentage of shareholders' equity"
            )
        
        # ROA (Return on Assets)
        if net_income and total_assets and total_assets != 0:
            roa_pct = (net_income / total_assets) * 100
            analysis.roa = EfficiencyMetric(
                name="Return on Assets",
                value=roa_pct,
                unit="%",
                period=f"FY{fiscal_year}",
                benchmark_value=self.benchmarks.get('roa'),
                performance_rating=self._rate_performance(roa_pct, self.benchmarks.get('roa', 0)),
                description="Net income as percentage of total assets"
            )
        
        # Asset Turnover
        if revenue and total_assets and total_assets != 0:
            asset_turnover_ratio = revenue / total_assets
            analysis.asset_turnover = EfficiencyMetric(
                name="Asset Turnover",
                value=asset_turnover_ratio,
                unit="x",
                period=f"FY{fiscal_year}",
                benchmark_value=self.benchmarks.get('asset_turnover'),
                performance_rating=self._rate_performance(asset_turnover_ratio, self.benchmarks.get('asset_turnover', 0)),
                description="Revenue divided by total assets"
            )
        
        # Inventory Turnover
        if cost_of_sales and inventory and inventory != 0:
            inventory_turnover_ratio = cost_of_sales / inventory
            analysis.inventory_turnover = EfficiencyMetric(
                name="Inventory Turnover",
                value=inventory_turnover_ratio,
                unit="x",
                period=f"FY{fiscal_year}",
                description="Cost of sales divided by inventory"
            )
        
        # Receivables Turnover
        if revenue and receivables and receivables != 0:
            receivables_turnover_ratio = revenue / receivables
            analysis.receivables_turnover = EfficiencyMetric(
                name="Receivables Turnover",
                value=receivables_turnover_ratio,
                unit="x",
                period=f"FY{fiscal_year}",
                description="Revenue divided by accounts receivable"
            )
        
        # Calculate overall capital efficiency score
        scores = []
        if analysis.roe and analysis.roe.value:
            scores.append(min(100, analysis.roe.value * 5))  # Scale ROE
        if analysis.roa and analysis.roa.value:
            scores.append(min(100, analysis.roa.value * 8))  # Scale ROA
        if analysis.asset_turnover and analysis.asset_turnover.value:
            scores.append(min(100, analysis.asset_turnover.value * 100))  # Scale asset turnover
        
        analysis.capital_efficiency_score = statistics.mean(scores) if scores else 0
        
        # Generate insights
        analysis.key_insights = self._generate_capital_efficiency_insights(analysis)
        analysis.key_insights.append(f"数据来源: FY{fiscal_year} Context ID映射")
        
        return analysis
    
    def _calculate_ebitda_by_year(self, fiscal_year: int) -> Optional[float]:
        """Calculate EBITDA for a specific fiscal year"""
        operating_income = self.get_value_for_fiscal_year('OperatingIncomeLoss', fiscal_year)
        depreciation = self.get_value_for_fiscal_year('DepreciationDepletionAndAmortization', fiscal_year)
        
        if operating_income:
            ebitda = operating_income
            if depreciation:
                ebitda += depreciation
            return ebitda
        
        return None