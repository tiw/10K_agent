"""
Drill Down Engine

Provides detailed breakdowns of financial data by segments, products, 
geographic regions, and expense categories for comprehensive analysis.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models import FilingData, FinancialFact
from ..utils.logging import get_logger
from ..utils.context_mapper import ContextMapper

logger = get_logger(__name__)


class BreakdownType(Enum):
    """Types of breakdowns supported"""
    PRODUCT_LINE = "product_line"
    GEOGRAPHIC_SEGMENT = "geographic_segment"
    EXPENSE_CATEGORY = "expense_category"
    BUSINESS_SEGMENT = "business_segment"
    REVENUE_STREAM = "revenue_stream"


@dataclass
class BreakdownItem:
    """Individual item in a breakdown"""
    name: str
    value: float
    unit: str
    percentage_of_total: float
    period: str
    
    # Additional metadata
    description: Optional[str] = None
    growth_rate: Optional[float] = None  # Period-over-period growth
    trend_direction: Optional[str] = None  # "up", "down", "stable"


@dataclass
class DrillDownAnalysis:
    """Complete drill-down analysis result"""
    breakdown_type: BreakdownType
    parent_metric: str
    parent_value: float
    period: str
    
    # Breakdown items
    items: List[BreakdownItem]
    
    # Analysis metrics
    concentration_ratio: float  # Top 3 items as % of total
    diversity_score: float  # How evenly distributed the breakdown is
    
    # Insights
    key_insights: List[str]
    
    def __post_init__(self):
        if not self.key_insights:
            self.key_insights = []


class DrillDownEngine:
    """
    Engine for drilling down into financial metrics to provide detailed
    breakdowns by various dimensions like segments, products, and categories
    """
    
    def __init__(self, filing_data: FilingData):
        self.filing_data = filing_data
        self.facts_by_concept = self._index_facts_by_concept()
        self.dimensional_facts = self._index_dimensional_facts()
        self.context_mapper = ContextMapper(filing_data.all_facts)
    
    def _index_facts_by_concept(self) -> Dict[str, List[FinancialFact]]:
        """Index facts by concept for quick lookup"""
        index = {}
        for fact in self.filing_data.all_facts:
            concept = fact.concept.split(':')[-1]  # Remove namespace prefix
            if concept not in index:
                index[concept] = []
            index[concept].append(fact)
        return index
    
    def _index_dimensional_facts(self) -> Dict[str, Dict[str, List[FinancialFact]]]:
        """Index facts by concept and dimensions"""
        index = {}
        for fact in self.filing_data.all_facts:
            concept = fact.concept.split(':')[-1]
            if concept not in index:
                index[concept] = {}
            
            # Group by dimensions if available
            dimension_key = self._get_dimension_key(fact)
            if dimension_key not in index[concept]:
                index[concept][dimension_key] = []
            index[concept][dimension_key].append(fact)
        
        return index
    
    def _get_dimension_key(self, fact: FinancialFact) -> str:
        """Extract dimension key from fact"""
        if hasattr(fact, 'dimensions') and fact.dimensions:
            # Create a key from all dimensions
            dim_parts = []
            for dim_name, dim_value in sorted(fact.dimensions.items()):
                dim_parts.append(f"{dim_name}:{dim_value}")
            return "|".join(dim_parts) if dim_parts else "default"
        return "default"
    
    def drill_down_revenue(self, period: Optional[str] = None) -> DrillDownAnalysis:
        """
        Drill down revenue by product lines and geographic segments
        """
        logger.info("Performing revenue drill-down analysis")
        
        # Get total revenue
        total_revenue = self._get_latest_value('RevenueFromContractWithCustomerExcludingAssessedTax', period)
        if not total_revenue:
            return self._create_empty_analysis(BreakdownType.REVENUE_STREAM, "Revenue", period)
        
        # Try to find revenue breakdowns
        breakdown_items = []
        
        # Look for product-specific revenue
        product_revenue_concepts = [
            'ProductSales',
            'ServiceSales', 
            'SoftwareRevenue',
            'HardwareRevenue',
            'SubscriptionRevenue',
            'LicenseRevenue'
        ]
        
        for concept in product_revenue_concepts:
            value = self._get_latest_value(concept, period)
            if value:
                percentage = (value / total_revenue) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=period or "Latest"
                ))
        
        # Look for geographic revenue breakdowns
        geographic_concepts = [
            'RevenueFromExternalCustomersUnitedStates',
            'RevenueFromExternalCustomersChina',
            'RevenueFromExternalCustomersEurope',
            'RevenueFromExternalCustomersJapan',
            'RevenueFromExternalCustomersAsia',
            'RevenueFromExternalCustomersAmericas'
        ]
        
        for concept in geographic_concepts:
            value = self._get_latest_value(concept, period)
            if value:
                percentage = (value / total_revenue) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=period or "Latest"
                ))
        
        # If no specific breakdowns found, try dimensional analysis
        if not breakdown_items:
            breakdown_items = self._analyze_dimensional_revenue(total_revenue, period)
        
        # Sort by value descending
        breakdown_items.sort(key=lambda x: x.value, reverse=True)
        
        # Calculate analysis metrics
        concentration_ratio = self._calculate_concentration_ratio(breakdown_items)
        diversity_score = self._calculate_diversity_score(breakdown_items)
        
        # Generate insights
        insights = self._generate_revenue_insights(breakdown_items, concentration_ratio, diversity_score)
        
        return DrillDownAnalysis(
            breakdown_type=BreakdownType.REVENUE_STREAM,
            parent_metric="Revenue",
            parent_value=total_revenue,
            period=period or "Latest",
            items=breakdown_items,
            concentration_ratio=concentration_ratio,
            diversity_score=diversity_score,
            key_insights=insights
        )
    
    def drill_down_expenses(self, period: Optional[str] = None) -> DrillDownAnalysis:
        """
        Drill down operating expenses by category
        """
        logger.info("Performing expense drill-down analysis")
        
        # Get total operating expenses
        total_expenses = self._get_latest_value('OperatingExpenses', period)
        if not total_expenses:
            return self._create_empty_analysis(BreakdownType.EXPENSE_CATEGORY, "Operating Expenses", period)
        
        breakdown_items = []
        
        # Major expense categories
        expense_concepts = [
            'ResearchAndDevelopmentExpense',
            'SellingGeneralAndAdministrativeExpense',
            'MarketingExpense',
            'SalariesAndWages',
            'DepreciationDepletionAndAmortization',
            'RentExpense',
            'ProfessionalFees',
            'TravelAndEntertainmentExpense',
            'UtilitiesExpense',
            'InsuranceExpense'
        ]
        
        for concept in expense_concepts:
            value = self._get_latest_value(concept, period)
            if value:
                percentage = (value / total_expenses) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=period or "Latest"
                ))
        
        # Sort by value descending
        breakdown_items.sort(key=lambda x: x.value, reverse=True)
        
        # Calculate analysis metrics
        concentration_ratio = self._calculate_concentration_ratio(breakdown_items)
        diversity_score = self._calculate_diversity_score(breakdown_items)
        
        # Generate insights
        insights = self._generate_expense_insights(breakdown_items, concentration_ratio, diversity_score)
        
        return DrillDownAnalysis(
            breakdown_type=BreakdownType.EXPENSE_CATEGORY,
            parent_metric="Operating Expenses",
            parent_value=total_expenses,
            period=period or "Latest",
            items=breakdown_items,
            concentration_ratio=concentration_ratio,
            diversity_score=diversity_score,
            key_insights=insights
        )
    
    def drill_down_assets(self, period: Optional[str] = None) -> DrillDownAnalysis:
        """
        Drill down total assets by category
        """
        logger.info("Performing asset drill-down analysis")
        
        # Get total assets
        total_assets = self._get_latest_value('Assets', period)
        if not total_assets:
            return self._create_empty_analysis(BreakdownType.BUSINESS_SEGMENT, "Assets", period)
        
        breakdown_items = []
        
        # Asset categories
        asset_concepts = [
            'CashAndCashEquivalentsAtCarryingValue',
            'MarketableSecurities',
            'AccountsReceivableNetCurrent',
            'InventoryNet',
            'PropertyPlantAndEquipmentNet',
            'Goodwill',
            'IntangibleAssetsNetExcludingGoodwill',
            'InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures',
            'DeferredTaxAssetsNetNoncurrent',
            'OtherAssetsNoncurrent'
        ]
        
        for concept in asset_concepts:
            value = self._get_latest_value(concept, period)
            if value:
                percentage = (value / total_assets) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=period or "Latest"
                ))
        
        # Sort by value descending
        breakdown_items.sort(key=lambda x: x.value, reverse=True)
        
        # Calculate analysis metrics
        concentration_ratio = self._calculate_concentration_ratio(breakdown_items)
        diversity_score = self._calculate_diversity_score(breakdown_items)
        
        # Generate insights
        insights = self._generate_asset_insights(breakdown_items, concentration_ratio, diversity_score)
        
        return DrillDownAnalysis(
            breakdown_type=BreakdownType.BUSINESS_SEGMENT,
            parent_metric="Total Assets",
            parent_value=total_assets,
            period=period or "Latest",
            items=breakdown_items,
            concentration_ratio=concentration_ratio,
            diversity_score=diversity_score,
            key_insights=insights
        )
    
    def get_comprehensive_breakdown(self, period: Optional[str] = None) -> Dict[str, DrillDownAnalysis]:
        """
        Get comprehensive breakdown analysis for all major categories
        """
        logger.info("Generating comprehensive breakdown analysis")
        
        return {
            'revenue': self.drill_down_revenue(period),
            'expenses': self.drill_down_expenses(period),
            'assets': self.drill_down_assets(period)
        }
    
    def _analyze_dimensional_revenue(self, total_revenue: float, period: Optional[str]) -> List[BreakdownItem]:
        """Analyze revenue using dimensional data if available"""
        breakdown_items = []
        
        # Look for revenue facts with dimensions
        revenue_facts = self.dimensional_facts.get('RevenueFromContractWithCustomerExcludingAssessedTax', {})
        
        for dimension_key, facts in revenue_facts.items():
            if dimension_key != "default" and facts:
                # Get the latest fact for this dimension
                latest_fact = max(facts, key=lambda f: f.period_end or f.period)
                if isinstance(latest_fact.value, (int, float)):
                    value = float(latest_fact.value)
                    if latest_fact.decimals is not None:
                        value *= (10 ** latest_fact.decimals)
                    
                    percentage = (value / total_revenue) * 100
                    breakdown_items.append(BreakdownItem(
                        name=self._format_dimension_name(dimension_key),
                        value=value,
                        unit="USD",
                        percentage_of_total=percentage,
                        period=period or "Latest"
                    ))
        
        return breakdown_items
    
    def _get_latest_value(self, concept: str, period: Optional[str] = None) -> Optional[float]:
        """Get the latest value for a financial concept using Context ID mapping"""
        # If period is specified as a fiscal year, use context mapper
        if period and period.isdigit():
            fiscal_year = int(period)
            # Determine if this is a revenue/income statement concept or balance sheet concept
            prefer_duration = any(term in concept.lower() for term in ['revenue', 'income', 'expense', 'cost', 'sales'])
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
        prefer_duration = any(term in concept.lower() for term in ['revenue', 'income', 'expense', 'cost', 'sales'])
        return self.context_mapper.get_concept_value_for_year(concept, fiscal_year, prefer_duration)
    
    def _humanize_concept_name(self, concept: str) -> str:
        """Convert XBRL concept name to human-readable format"""
        # Simple mapping for common concepts
        name_mapping = {
            'ProductSales': '产品销售',
            'ServiceSales': '服务收入',
            'SoftwareRevenue': '软件收入',
            'HardwareRevenue': '硬件收入',
            'SubscriptionRevenue': '订阅收入',
            'LicenseRevenue': '许可收入',
            'RevenueFromExternalCustomersUnitedStates': '美国收入',
            'RevenueFromExternalCustomersChina': '中国收入',
            'RevenueFromExternalCustomersEurope': '欧洲收入',
            'RevenueFromExternalCustomersJapan': '日本收入',
            'RevenueFromExternalCustomersAsia': '亚洲收入',
            'RevenueFromExternalCustomersAmericas': '美洲收入',
            'ResearchAndDevelopmentExpense': '研发费用',
            'SellingGeneralAndAdministrativeExpense': '销售管理费用',
            'MarketingExpense': '营销费用',
            'SalariesAndWages': '薪资费用',
            'DepreciationDepletionAndAmortization': '折旧摊销',
            'CashAndCashEquivalentsAtCarryingValue': '现金及等价物',
            'MarketableSecurities': '有价证券',
            'AccountsReceivableNetCurrent': '应收账款',
            'InventoryNet': '存货',
            'PropertyPlantAndEquipmentNet': '固定资产',
            'Goodwill': '商誉',
            'IntangibleAssetsNetExcludingGoodwill': '无形资产'
        }
        
        return name_mapping.get(concept, concept)
    
    def _format_dimension_name(self, dimension_key: str) -> str:
        """Format dimension key into readable name"""
        if dimension_key == "default":
            return "默认"
        
        # Parse dimension key and format
        parts = dimension_key.split("|")
        formatted_parts = []
        for part in parts:
            if ":" in part:
                dim_name, dim_value = part.split(":", 1)
                formatted_parts.append(f"{dim_name}: {dim_value}")
            else:
                formatted_parts.append(part)
        
        return " | ".join(formatted_parts)
    
    def _calculate_concentration_ratio(self, items: List[BreakdownItem]) -> float:
        """Calculate concentration ratio (top 3 items as % of total)"""
        if len(items) < 3:
            return sum(item.percentage_of_total for item in items)
        
        top_3_percentage = sum(item.percentage_of_total for item in items[:3])
        return top_3_percentage
    
    def _calculate_diversity_score(self, items: List[BreakdownItem]) -> float:
        """Calculate diversity score (0-100, higher = more diverse)"""
        if not items:
            return 0.0
        
        # Calculate Herfindahl-Hirschman Index (HHI) and convert to diversity score
        hhi = sum((item.percentage_of_total / 100) ** 2 for item in items)
        
        # Convert HHI to diversity score (0-100)
        # HHI ranges from 1/n to 1, where n is number of items
        # Diversity score is inverse: higher when more diverse
        max_hhi = 1.0
        min_hhi = 1.0 / len(items) if items else 1.0
        
        diversity_score = (1 - (hhi - min_hhi) / (max_hhi - min_hhi)) * 100
        return max(0, min(100, diversity_score))
    
    def _generate_revenue_insights(self, items: List[BreakdownItem], 
                                 concentration_ratio: float, diversity_score: float) -> List[str]:
        """Generate insights for revenue breakdown"""
        insights = []
        
        if items:
            top_item = items[0]
            insights.append(f"最大收入来源是{top_item.name}，占总收入的{top_item.percentage_of_total:.1f}%")
        
        if concentration_ratio > 75:
            insights.append(f"收入高度集中，前三大来源占{concentration_ratio:.1f}%，存在集中风险")
        elif concentration_ratio > 50:
            insights.append(f"收入相对集中，前三大来源占{concentration_ratio:.1f}%")
        else:
            insights.append(f"收入来源较为分散，前三大来源占{concentration_ratio:.1f}%")
        
        if diversity_score > 70:
            insights.append("收入来源多样化程度高，风险分散良好")
        elif diversity_score > 40:
            insights.append("收入来源多样化程度中等")
        else:
            insights.append("收入来源集中度较高，建议增加收入来源多样性")
        
        return insights
    
    def _generate_expense_insights(self, items: List[BreakdownItem],
                                 concentration_ratio: float, diversity_score: float) -> List[str]:
        """Generate insights for expense breakdown"""
        insights = []
        
        if items:
            top_item = items[0]
            insights.append(f"最大费用项目是{top_item.name}，占总费用的{top_item.percentage_of_total:.1f}%")
        
        # Look for R&D expenses specifically
        rd_items = [item for item in items if "研发" in item.name]
        if rd_items:
            rd_percentage = sum(item.percentage_of_total for item in rd_items)
            if rd_percentage > 20:
                insights.append(f"研发投入占费用{rd_percentage:.1f}%，创新投入较高")
            elif rd_percentage > 10:
                insights.append(f"研发投入占费用{rd_percentage:.1f}%，保持适度创新投入")
        
        if concentration_ratio > 60:
            insights.append("费用结构相对集中，主要费用项目明确")
        else:
            insights.append("费用结构较为分散，成本控制需要全面管理")
        
        return insights
    
    def _generate_asset_insights(self, items: List[BreakdownItem],
                               concentration_ratio: float, diversity_score: float) -> List[str]:
        """Generate insights for asset breakdown"""
        insights = []
        
        if items:
            top_item = items[0]
            insights.append(f"最大资产类别是{top_item.name}，占总资产的{top_item.percentage_of_total:.1f}%")
        
        # Look for cash and liquid assets
        liquid_items = [item for item in items if any(keyword in item.name for keyword in ["现金", "证券", "有价证券"])]
        if liquid_items:
            liquid_percentage = sum(item.percentage_of_total for item in liquid_items)
            if liquid_percentage > 30:
                insights.append(f"流动性资产占{liquid_percentage:.1f}%，现金充裕")
            elif liquid_percentage > 15:
                insights.append(f"流动性资产占{liquid_percentage:.1f}%，流动性良好")
            else:
                insights.append(f"流动性资产占{liquid_percentage:.1f}%，流动性相对较低")
        
        # Look for fixed assets
        fixed_items = [item for item in items if any(keyword in item.name for keyword in ["固定资产", "设备"])]
        if fixed_items:
            fixed_percentage = sum(item.percentage_of_total for item in fixed_items)
            if fixed_percentage > 40:
                insights.append("固定资产占比较高，属于资本密集型业务")
            elif fixed_percentage > 20:
                insights.append("固定资产占比适中，资产结构平衡")
        
        return insights
    
    def _create_empty_analysis(self, breakdown_type: BreakdownType, 
                             parent_metric: str, period: Optional[str]) -> DrillDownAnalysis:
        """Create empty analysis when no data is available"""
        return DrillDownAnalysis(
            breakdown_type=breakdown_type,
            parent_metric=parent_metric,
            parent_value=0.0,
            period=period or "Latest",
            items=[],
            concentration_ratio=0.0,
            diversity_score=0.0,
            key_insights=["暂无可用的细分数据进行分析"]
        )   
 
    def drill_down_revenue_by_year(self, fiscal_year: int) -> DrillDownAnalysis:
        """
        Drill down revenue by product lines and geographic segments for a specific fiscal year
        """
        logger.info(f"Performing revenue drill-down analysis for FY{fiscal_year}")
        
        # Get total revenue using context mapping
        total_revenue = self.get_value_for_fiscal_year('RevenueFromContractWithCustomerExcludingAssessedTax', fiscal_year)
        if not total_revenue:
            return self._create_empty_analysis(BreakdownType.REVENUE_STREAM, "Revenue", f"FY{fiscal_year}")
        
        breakdown_items = []
        
        # Find all revenue facts for the fiscal year and analyze by context
        revenue_by_context = self._find_revenue_segments_by_context(fiscal_year)
        
        # Convert context-based revenue to breakdown items
        for context_info in revenue_by_context:
            if context_info['value'] != total_revenue:  # Exclude total revenue
                percentage = (context_info['value'] / total_revenue) * 100
                breakdown_items.append(BreakdownItem(
                    name=context_info['segment_name'],
                    value=context_info['value'],
                    unit="USD",
                    percentage_of_total=percentage,
                    period=f"FY{fiscal_year}",
                    description=f"Context: {context_info['context_id']}"
                ))
        
        # If no context-based segments found, try traditional concept-based approach
        if not breakdown_items:
            breakdown_items = self._find_revenue_segments_by_concept(fiscal_year, total_revenue)
        
        # Sort by value descending
        breakdown_items.sort(key=lambda x: x.value, reverse=True)
        
        # Calculate analysis metrics
        concentration_ratio = self._calculate_concentration_ratio(breakdown_items)
        diversity_score = self._calculate_diversity_score(breakdown_items)
        
        # Generate insights
        insights = self._generate_revenue_insights(breakdown_items, concentration_ratio, diversity_score)
        insights.append(f"数据来源: FY{fiscal_year} Context ID映射")
        
        return DrillDownAnalysis(
            breakdown_type=BreakdownType.REVENUE_STREAM,
            parent_metric="Revenue",
            parent_value=total_revenue,
            period=f"FY{fiscal_year}",
            items=breakdown_items,
            concentration_ratio=concentration_ratio,
            diversity_score=diversity_score,
            key_insights=insights
        )
    
    def _find_revenue_segments_by_context(self, fiscal_year: int) -> List[Dict[str, Any]]:
        """Find revenue segments by analyzing different contexts"""
        revenue_segments = []
        
        # Find all revenue facts for the fiscal year
        revenue_facts = []
        for fact in self.filing_data.all_facts:
            if ('RevenueFromContractWithCustomerExcludingAssessedTax' in fact.concept and 
                fact.period_end and fact.period_end.year == fiscal_year and
                isinstance(fact.value, (int, float))):
                scaled_value = fact.get_scaled_value()
                revenue_facts.append({
                    'context_id': fact.context_id,
                    'value': scaled_value,
                    'period': fact.period
                })
        
        # Sort by value to identify segments
        revenue_facts.sort(key=lambda x: x['value'], reverse=True)
        
        # Map known Apple revenue segments based on typical values
        segment_mapping = {
            # These are approximate mappings based on Apple's typical revenue structure
            'iPhone': {'min_pct': 45, 'max_pct': 55},      # ~50% of total revenue
            'Services': {'min_pct': 20, 'max_pct': 30},    # ~25% of total revenue  
            'Mac': {'min_pct': 6, 'max_pct': 12},          # ~8% of total revenue
            'iPad': {'min_pct': 6, 'max_pct': 12},         # ~7% of total revenue
            'Wearables': {'min_pct': 8, 'max_pct': 15},    # ~9% of total revenue
        }
        
        total_revenue = revenue_facts[0]['value'] if revenue_facts else 0
        
        for fact in revenue_facts:
            if fact['value'] == total_revenue:
                continue  # Skip total revenue
            
            percentage = (fact['value'] / total_revenue * 100) if total_revenue else 0
            segment_name = f"收入细分 {fact['context_id']}"
            
            # Try to identify the segment based on percentage
            for segment, pct_range in segment_mapping.items():
                if pct_range['min_pct'] <= percentage <= pct_range['max_pct']:
                    segment_name = segment
                    break
            
            revenue_segments.append({
                'context_id': fact['context_id'],
                'value': fact['value'],
                'percentage': percentage,
                'segment_name': segment_name
            })
        
        return revenue_segments
    
    def _find_revenue_segments_by_concept(self, fiscal_year: int, total_revenue: float) -> List[BreakdownItem]:
        """Fallback method to find revenue segments by concept names"""
        breakdown_items = []
        
        # Look for product-specific revenue
        product_revenue_concepts = [
            'ProductSales',
            'ServiceSales', 
            'SoftwareRevenue',
            'HardwareRevenue',
            'SubscriptionRevenue',
            'LicenseRevenue'
        ]
        
        for concept in product_revenue_concepts:
            value = self.get_value_for_fiscal_year(concept, fiscal_year)
            if value:
                percentage = (value / total_revenue) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=f"FY{fiscal_year}"
                ))
        
        # Look for geographic revenue breakdowns
        geographic_concepts = [
            'RevenueFromExternalCustomersUnitedStates',
            'RevenueFromExternalCustomersChina',
            'RevenueFromExternalCustomersEurope',
            'RevenueFromExternalCustomersJapan',
            'RevenueFromExternalCustomersAsia',
            'RevenueFromExternalCustomersAmericas'
        ]
        
        for concept in geographic_concepts:
            value = self.get_value_for_fiscal_year(concept, fiscal_year)
            if value:
                percentage = (value / total_revenue) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=f"FY{fiscal_year}"
                ))
        
        return breakdown_items
    
    def drill_down_expenses_by_year(self, fiscal_year: int) -> DrillDownAnalysis:
        """
        Drill down operating expenses by category for a specific fiscal year
        """
        logger.info(f"Performing expense drill-down analysis for FY{fiscal_year}")
        
        # Get total operating expenses using context mapping
        total_expenses = self.get_value_for_fiscal_year('OperatingExpenses', fiscal_year)
        if not total_expenses:
            return self._create_empty_analysis(BreakdownType.EXPENSE_CATEGORY, "Operating Expenses", f"FY{fiscal_year}")
        
        breakdown_items = []
        
        # Major expense categories
        expense_concepts = [
            'ResearchAndDevelopmentExpense',
            'SellingGeneralAndAdministrativeExpense',
            'MarketingExpense',
            'SalariesAndWages',
            'DepreciationDepletionAndAmortization',
            'RentExpense',
            'ProfessionalFees',
            'TravelAndEntertainmentExpense',
            'UtilitiesExpense',
            'InsuranceExpense'
        ]
        
        for concept in expense_concepts:
            value = self.get_value_for_fiscal_year(concept, fiscal_year)
            if value:
                percentage = (value / total_expenses) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=f"FY{fiscal_year}"
                ))
        
        # Sort by value descending
        breakdown_items.sort(key=lambda x: x.value, reverse=True)
        
        # Calculate analysis metrics
        concentration_ratio = self._calculate_concentration_ratio(breakdown_items)
        diversity_score = self._calculate_diversity_score(breakdown_items)
        
        # Generate insights
        insights = self._generate_expense_insights(breakdown_items, concentration_ratio, diversity_score)
        insights.append(f"数据来源: FY{fiscal_year} Context ID映射")
        
        return DrillDownAnalysis(
            breakdown_type=BreakdownType.EXPENSE_CATEGORY,
            parent_metric="Operating Expenses",
            parent_value=total_expenses,
            period=f"FY{fiscal_year}",
            items=breakdown_items,
            concentration_ratio=concentration_ratio,
            diversity_score=diversity_score,
            key_insights=insights
        )
    
    def drill_down_assets_by_year(self, fiscal_year: int) -> DrillDownAnalysis:
        """
        Drill down total assets by category for a specific fiscal year
        """
        logger.info(f"Performing asset drill-down analysis for FY{fiscal_year}")
        
        # Get total assets using context mapping (balance sheet data, prefer instant)
        total_assets = self.context_mapper.get_concept_value_for_year('Assets', fiscal_year, prefer_duration=False)
        if not total_assets:
            return self._create_empty_analysis(BreakdownType.BUSINESS_SEGMENT, "Assets", f"FY{fiscal_year}")
        
        breakdown_items = []
        
        # Asset categories
        asset_concepts = [
            'CashAndCashEquivalentsAtCarryingValue',
            'MarketableSecurities',
            'AccountsReceivableNetCurrent',
            'InventoryNet',
            'PropertyPlantAndEquipmentNet',
            'Goodwill',
            'IntangibleAssetsNetExcludingGoodwill',
            'InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures',
            'DeferredTaxAssetsNetNoncurrent',
            'OtherAssetsNoncurrent'
        ]
        
        for concept in asset_concepts:
            # Assets are balance sheet items, prefer instant context
            value = self.context_mapper.get_concept_value_for_year(concept, fiscal_year, prefer_duration=False)
            if value:
                percentage = (value / total_assets) * 100
                breakdown_items.append(BreakdownItem(
                    name=self._humanize_concept_name(concept),
                    value=value,
                    unit="USD",
                    percentage_of_total=percentage,
                    period=f"FY{fiscal_year}"
                ))
        
        # Sort by value descending
        breakdown_items.sort(key=lambda x: x.value, reverse=True)
        
        # Calculate analysis metrics
        concentration_ratio = self._calculate_concentration_ratio(breakdown_items)
        diversity_score = self._calculate_diversity_score(breakdown_items)
        
        # Generate insights
        insights = self._generate_asset_insights(breakdown_items, concentration_ratio, diversity_score)
        insights.append(f"数据来源: FY{fiscal_year} Context ID映射")
        
        return DrillDownAnalysis(
            breakdown_type=BreakdownType.BUSINESS_SEGMENT,
            parent_metric="Total Assets",
            parent_value=total_assets,
            period=f"FY{fiscal_year}",
            items=breakdown_items,
            concentration_ratio=concentration_ratio,
            diversity_score=diversity_score,
            key_insights=insights
        )
    
    def get_comprehensive_breakdown_by_year(self, fiscal_year: int) -> Dict[str, DrillDownAnalysis]:
        """
        Get comprehensive breakdown analysis for all major categories for a specific fiscal year
        """
        logger.info(f"Generating comprehensive breakdown analysis for FY{fiscal_year}")
        
        return {
            'revenue': self.drill_down_revenue_by_year(fiscal_year),
            'expenses': self.drill_down_expenses_by_year(fiscal_year),
            'assets': self.drill_down_assets_by_year(fiscal_year)
        }