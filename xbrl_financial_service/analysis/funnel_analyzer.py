"""
Financial Funnel Analyzer

Analyzes financial data in a funnel/tree structure to show conversion efficiency
and business performance at different levels.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import date

from ..models import FilingData, FinancialFact
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FunnelLevel:
    """Represents a level in the financial funnel"""
    name: str
    value: float
    unit: str
    period: str
    conversion_rate: Optional[float] = None  # Conversion from previous level
    efficiency_ratio: Optional[float] = None  # Efficiency metric
    children: List['FunnelLevel'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class FinancialFunnel:
    """Complete financial funnel structure"""
    company_name: str
    period: str
    funnel_type: str  # 'profitability', 'cash_conversion', 'capital_efficiency'
    levels: List[FunnelLevel]
    total_conversion_rate: float
    key_insights: List[str]


class FunnelAnalyzer:
    """
    Analyzes financial data to create funnel/tree structures showing
    conversion efficiency and business performance
    """
    
    def __init__(self, filing_data: FilingData):
        self.filing_data = filing_data
        self.facts_by_concept = self._index_facts_by_concept()
    
    def _index_facts_by_concept(self) -> Dict[str, List[FinancialFact]]:
        """Index facts by concept for quick lookup"""
        index = {}
        for fact in self.filing_data.all_facts:
            concept = fact.concept.split(':')[-1]  # Remove namespace prefix
            if concept not in index:
                index[concept] = []
            index[concept].append(fact)
        return index
    
    def get_profitability_funnel(self, period: Optional[str] = None) -> FinancialFunnel:
        """
        Create profitability funnel: Revenue → Gross Profit → Operating Income → Net Income
        Shows conversion efficiency at each stage
        """
        logger.info("Building profitability funnel")
        
        # Get key financial metrics
        revenue = self._get_latest_value('RevenueFromContractWithCustomerExcludingAssessedTax', period)
        cost_of_sales = self._get_latest_value('CostOfGoodsAndServicesSold', period)
        gross_profit = revenue - cost_of_sales if revenue and cost_of_sales else None
        
        operating_expenses = self._get_latest_value('OperatingExpenses', period)
        operating_income = self._get_latest_value('OperatingIncomeLoss', period)
        
        tax_expense = self._get_latest_value('IncomeTaxExpenseBenefit', period)
        net_income = self._get_latest_value('NetIncomeLoss', period)
        
        # Build funnel levels
        levels = []
        
        if revenue:
            revenue_level = FunnelLevel(
                name="营业收入 (Revenue)",
                value=revenue,
                unit="USD",
                period=period or "Latest"
            )
            levels.append(revenue_level)
            
            # Add revenue breakdown if available
            product_revenue = self._get_latest_value('ProductSales', period)
            service_revenue = self._get_latest_value('ServiceSales', period)
            if product_revenue or service_revenue:
                if product_revenue:
                    revenue_level.children.append(FunnelLevel(
                        name="产品收入",
                        value=product_revenue,
                        unit="USD",
                        period=period or "Latest",
                        conversion_rate=product_revenue / revenue * 100
                    ))
                if service_revenue:
                    revenue_level.children.append(FunnelLevel(
                        name="服务收入", 
                        value=service_revenue,
                        unit="USD",
                        period=period or "Latest",
                        conversion_rate=service_revenue / revenue * 100
                    ))
        
        if gross_profit and revenue:
            gross_margin = gross_profit / revenue
            levels.append(FunnelLevel(
                name="毛利润 (Gross Profit)",
                value=gross_profit,
                unit="USD", 
                period=period or "Latest",
                conversion_rate=gross_margin * 100,
                efficiency_ratio=gross_margin
            ))
        
        if operating_income and revenue:
            operating_margin = operating_income / revenue
            levels.append(FunnelLevel(
                name="营业利润 (Operating Income)",
                value=operating_income,
                unit="USD",
                period=period or "Latest", 
                conversion_rate=operating_margin * 100,
                efficiency_ratio=operating_margin
            ))
            
            # Add operating expense breakdown
            rd_expense = self._get_latest_value('ResearchAndDevelopmentExpense', period)
            sga_expense = self._get_latest_value('SellingGeneralAndAdministrativeExpense', period)
            
            operating_level = levels[-1]
            if rd_expense:
                operating_level.children.append(FunnelLevel(
                    name="研发费用",
                    value=-rd_expense,  # Negative as it's an expense
                    unit="USD",
                    period=period or "Latest",
                    conversion_rate=rd_expense / revenue * 100
                ))
            if sga_expense:
                operating_level.children.append(FunnelLevel(
                    name="销售管理费用",
                    value=-sga_expense,
                    unit="USD", 
                    period=period or "Latest",
                    conversion_rate=sga_expense / revenue * 100
                ))
        
        if net_income and revenue:
            net_margin = net_income / revenue
            levels.append(FunnelLevel(
                name="净利润 (Net Income)",
                value=net_income,
                unit="USD",
                period=period or "Latest",
                conversion_rate=net_margin * 100,
                efficiency_ratio=net_margin
            ))
        
        # Calculate total conversion rate
        total_conversion = net_income / revenue * 100 if net_income and revenue else 0
        
        # Generate insights
        insights = self._generate_profitability_insights(levels)
        
        return FinancialFunnel(
            company_name=self.filing_data.company_info.name,
            period=period or "Latest",
            funnel_type="profitability",
            levels=levels,
            total_conversion_rate=total_conversion,
            key_insights=insights
        )
    
    def get_cash_conversion_funnel(self, period: Optional[str] = None) -> FinancialFunnel:
        """
        Create cash conversion funnel: Revenue → Operating Cash Flow → Free Cash Flow
        Shows how efficiently the company converts revenue to cash
        """
        logger.info("Building cash conversion funnel")
        
        revenue = self._get_latest_value('RevenueFromContractWithCustomerExcludingAssessedTax', period)
        operating_cash_flow = self._get_latest_value('NetCashProvidedByUsedInOperatingActivities', period)
        capex = self._get_latest_value('PaymentsToAcquirePropertyPlantAndEquipment', period)
        free_cash_flow = operating_cash_flow - capex if operating_cash_flow and capex else None
        
        levels = []
        
        if revenue:
            levels.append(FunnelLevel(
                name="营业收入 (Revenue)",
                value=revenue,
                unit="USD",
                period=period or "Latest"
            ))
        
        if operating_cash_flow and revenue:
            cash_conversion_rate = operating_cash_flow / revenue
            levels.append(FunnelLevel(
                name="经营现金流 (Operating Cash Flow)",
                value=operating_cash_flow,
                unit="USD",
                period=period or "Latest",
                conversion_rate=cash_conversion_rate * 100,
                efficiency_ratio=cash_conversion_rate
            ))
        
        if free_cash_flow and revenue:
            fcf_conversion_rate = free_cash_flow / revenue
            levels.append(FunnelLevel(
                name="自由现金流 (Free Cash Flow)",
                value=free_cash_flow,
                unit="USD",
                period=period or "Latest",
                conversion_rate=fcf_conversion_rate * 100,
                efficiency_ratio=fcf_conversion_rate
            ))
        
        total_conversion = free_cash_flow / revenue * 100 if free_cash_flow and revenue else 0
        insights = self._generate_cash_insights(levels)
        
        return FinancialFunnel(
            company_name=self.filing_data.company_info.name,
            period=period or "Latest",
            funnel_type="cash_conversion",
            levels=levels,
            total_conversion_rate=total_conversion,
            key_insights=insights
        )
    
    def get_capital_efficiency_funnel(self, period: Optional[str] = None) -> FinancialFunnel:
        """
        Create capital efficiency funnel: Assets → Equity → Returns → Distributions
        Shows how efficiently capital is deployed and returned
        """
        logger.info("Building capital efficiency funnel")
        
        total_assets = self._get_latest_value('Assets', period)
        total_equity = self._get_latest_value('StockholdersEquity', period)
        net_income = self._get_latest_value('NetIncomeLoss', period)
        dividends = self._get_latest_value('PaymentsOfDividends', period)
        share_repurchases = self._get_latest_value('PaymentsForRepurchaseOfCommonStock', period)
        
        levels = []
        
        if total_assets:
            levels.append(FunnelLevel(
                name="总资产 (Total Assets)",
                value=total_assets,
                unit="USD",
                period=period or "Latest"
            ))
        
        if total_equity and total_assets:
            equity_ratio = total_equity / total_assets
            levels.append(FunnelLevel(
                name="股东权益 (Shareholders' Equity)",
                value=total_equity,
                unit="USD",
                period=period or "Latest",
                conversion_rate=equity_ratio * 100,
                efficiency_ratio=equity_ratio
            ))
        
        if net_income and total_equity:
            roe = net_income / total_equity
            levels.append(FunnelLevel(
                name="净利润回报 (Net Income)",
                value=net_income,
                unit="USD",
                period=period or "Latest",
                conversion_rate=roe * 100,
                efficiency_ratio=roe
            ))
        
        # Capital distributions
        total_distributions = 0
        if dividends:
            total_distributions += dividends
        if share_repurchases:
            total_distributions += share_repurchases
            
        if total_distributions and net_income:
            payout_ratio = total_distributions / net_income
            levels.append(FunnelLevel(
                name="资本分配 (Capital Distributions)",
                value=total_distributions,
                unit="USD",
                period=period or "Latest",
                conversion_rate=payout_ratio * 100,
                efficiency_ratio=payout_ratio
            ))
        
        total_conversion = total_distributions / total_assets * 100 if total_distributions and total_assets else 0
        insights = self._generate_capital_insights(levels)
        
        return FinancialFunnel(
            company_name=self.filing_data.company_info.name,
            period=period or "Latest",
            funnel_type="capital_efficiency",
            levels=levels,
            total_conversion_rate=total_conversion,
            key_insights=insights
        )
    
    def _get_latest_value(self, concept: str, period: Optional[str] = None) -> Optional[float]:
        """Get the latest value for a financial concept"""
        facts = self.facts_by_concept.get(concept, [])
        if not facts:
            return None
        
        # Filter by period if specified
        if period:
            facts = [f for f in facts if period in f.period]
        
        # Get the most recent fact
        if facts:
            latest_fact = max(facts, key=lambda f: f.period_end or date.min)
            if isinstance(latest_fact.value, (int, float)):
                # Apply scaling if decimals are specified
                if latest_fact.decimals is not None:
                    return float(latest_fact.value) * (10 ** latest_fact.decimals)
                return float(latest_fact.value)
        
        return None
    
    def _generate_profitability_insights(self, levels: List[FunnelLevel]) -> List[str]:
        """Generate insights for profitability funnel"""
        insights = []
        
        if len(levels) >= 2:
            gross_margin = levels[1].efficiency_ratio if len(levels) > 1 else None
            if gross_margin:
                if gross_margin > 0.4:
                    insights.append(f"毛利率 {gross_margin:.1%} 表现优秀，显示强定价能力")
                elif gross_margin > 0.2:
                    insights.append(f"毛利率 {gross_margin:.1%} 处于合理水平")
                else:
                    insights.append(f"毛利率 {gross_margin:.1%} 偏低，需关注成本控制")
        
        if len(levels) >= 3:
            operating_margin = levels[2].efficiency_ratio
            if operating_margin:
                if operating_margin > 0.2:
                    insights.append(f"营业利润率 {operating_margin:.1%} 优秀，运营效率高")
                elif operating_margin > 0.1:
                    insights.append(f"营业利润率 {operating_margin:.1%} 良好")
                else:
                    insights.append(f"营业利润率 {operating_margin:.1%} 需要改善运营效率")
        
        if len(levels) >= 4:
            net_margin = levels[3].efficiency_ratio
            if net_margin:
                insights.append(f"净利润率 {net_margin:.1%}，整体盈利能力{'强' if net_margin > 0.15 else '一般' if net_margin > 0.05 else '偏弱'}")
        
        return insights
    
    def _generate_cash_insights(self, levels: List[FunnelLevel]) -> List[str]:
        """Generate insights for cash conversion funnel"""
        insights = []
        
        if len(levels) >= 2:
            cash_conversion = levels[1].efficiency_ratio
            if cash_conversion:
                if cash_conversion > 0.2:
                    insights.append(f"现金转换率 {cash_conversion:.1%} 优秀，现金创造能力强")
                elif cash_conversion > 0.1:
                    insights.append(f"现金转换率 {cash_conversion:.1%} 良好")
                else:
                    insights.append(f"现金转换率 {cash_conversion:.1%} 需要关注营运资金管理")
        
        if len(levels) >= 3:
            fcf_conversion = levels[2].efficiency_ratio
            if fcf_conversion:
                insights.append(f"自由现金流转换率 {fcf_conversion:.1%}，{'现金流充裕' if fcf_conversion > 0.15 else '现金流一般' if fcf_conversion > 0.05 else '现金流紧张'}")
        
        return insights
    
    def _generate_capital_insights(self, levels: List[FunnelLevel]) -> List[str]:
        """Generate insights for capital efficiency funnel"""
        insights = []
        
        if len(levels) >= 2:
            equity_ratio = levels[1].efficiency_ratio
            if equity_ratio:
                if equity_ratio > 0.5:
                    insights.append(f"权益比率 {equity_ratio:.1%}，财务结构稳健")
                elif equity_ratio > 0.3:
                    insights.append(f"权益比率 {equity_ratio:.1%}，财务杠杆适中")
                else:
                    insights.append(f"权益比率 {equity_ratio:.1%}，财务杠杆较高")
        
        if len(levels) >= 3:
            roe = levels[2].efficiency_ratio
            if roe:
                if roe > 0.15:
                    insights.append(f"股东权益回报率 {roe:.1%} 优秀")
                elif roe > 0.1:
                    insights.append(f"股东权益回报率 {roe:.1%} 良好")
                else:
                    insights.append(f"股东权益回报率 {roe:.1%} 需要提升")
        
        if len(levels) >= 4:
            payout_ratio = levels[3].efficiency_ratio
            if payout_ratio:
                insights.append(f"资本分配比率 {payout_ratio:.1%}，{'积极回报股东' if payout_ratio > 0.5 else '保守分配策略' if payout_ratio > 0.2 else '重投资策略'}")
        
        return insights