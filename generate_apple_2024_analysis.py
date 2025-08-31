#!/usr/bin/env python3
"""
Apple 2024财报深度解读生成器

利用所有分析工具生成Apple 2024年财报的综合深度分析报告，
包括趋势分析、漏斗分析、细分分析、效率分析和财务指标分析。
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xbrl_financial_service.xbrl_parser import XBRLParser
from xbrl_financial_service.analysis.funnel_analyzer import FunnelAnalyzer
from xbrl_financial_service.analysis.trend_analyzer import TrendAnalyzer
from xbrl_financial_service.analysis.drill_down_engine import DrillDownEngine
from xbrl_financial_service.analysis.efficiency_calculator import EfficiencyCalculator
from xbrl_financial_service.analysis.metrics_calculator import MetricsCalculator
from xbrl_financial_service.utils.context_mapper import ContextMapper


class Apple2024AnalysisGenerator:
    """Apple 2024财报深度分析生成器"""
    
    def __init__(self):
        self.filing_data = None
        self.analyzers = {}
        self.report_data = {}
        
    def load_data(self):
        """加载Apple XBRL数据"""
        print("📁 加载Apple 2024 XBRL数据...")
        
        # 检查文件是否存在
        required_files = [
            'aapl-20240928_htm.xml',
            'aapl-20240928.xsd',
            'aapl-20240928_cal.xml',
            'aapl-20240928_def.xml',
            'aapl-20240928_lab.xml',
            'aapl-20240928_pre.xml'
        ]
        
        missing_files = []
        for file_name in required_files:
            if not Path(file_name).exists():
                missing_files.append(file_name)
        
        if missing_files:
            raise FileNotFoundError(f"缺少必要文件: {missing_files}")
        
        # 解析XBRL文件
        parser = XBRLParser()
        xbrl_files = {
            'instance': 'aapl-20240928_htm.xml',
            'schema': 'aapl-20240928.xsd',
            'calculation': 'aapl-20240928_cal.xml',
            'definition': 'aapl-20240928_def.xml',
            'label': 'aapl-20240928_lab.xml',
            'presentation': 'aapl-20240928_pre.xml'
        }
        
        self.filing_data = parser.parse_filing(xbrl_files)
        print(f"✅ 成功解析 {len(self.filing_data.all_facts)} 个财务事实")
        
        # 初始化所有分析器
        print("🔧 初始化分析工具...")
        self.analyzers = {
            'funnel': FunnelAnalyzer(self.filing_data),
            'trend': TrendAnalyzer(self.filing_data),
            'drill_down': DrillDownEngine(self.filing_data),
            'efficiency': EfficiencyCalculator(self.filing_data),
            'metrics': MetricsCalculator(self.filing_data),
            'context_mapper': ContextMapper(self.filing_data.all_facts)
        }
        print("✅ 所有分析工具初始化完成")
    
    def analyze_company_overview(self):
        """分析公司概况"""
        print("\n📊 分析公司概况...")
        
        company_info = self.filing_data.company_info
        context_summary = self.analyzers['context_mapper'].get_context_summary()
        
        self.report_data['company_overview'] = {
            'company_name': company_info.name if company_info else "Apple Inc.",
            'cik': company_info.cik if company_info else "0000320193",
            'fiscal_year': 2024,
            'period_end': "2024-09-28",
            'total_facts': len(self.filing_data.all_facts),
            'fiscal_years_available': context_summary['fiscal_years'],
            'context_summary': {
                'revenue_context': context_summary['context_details'][2024]['revenue_context'],
                'balance_sheet_context': context_summary['context_details'][2024]['balance_sheet_context']
            }
        }
    
    def analyze_financial_performance(self):
        """分析财务表现"""
        print("\n💰 分析财务表现...")
        
        # 获取关键财务数据
        revenue_2024 = self.analyzers['context_mapper'].get_revenue_for_year(2024)
        revenue_2023 = self.analyzers['context_mapper'].get_revenue_for_year(2023)
        revenue_2022 = self.analyzers['context_mapper'].get_revenue_for_year(2022)
        
        operating_income_2024 = self.analyzers['efficiency'].get_value_for_fiscal_year('OperatingIncomeLoss', 2024)
        net_income_2024 = self.analyzers['efficiency'].get_value_for_fiscal_year('NetIncomeLoss', 2024)
        
        # 计算增长率
        revenue_growth_yoy = ((revenue_2024 - revenue_2023) / revenue_2023 * 100) if revenue_2023 else None
        revenue_cagr_3y = (((revenue_2024 / revenue_2022) ** (1/2)) - 1) * 100 if revenue_2022 else None
        
        self.report_data['financial_performance'] = {
            'revenue': {
                '2024': revenue_2024,
                '2023': revenue_2023,
                '2022': revenue_2022,
                'yoy_growth': revenue_growth_yoy,
                'cagr_3y': revenue_cagr_3y
            },
            'profitability': {
                'operating_income': operating_income_2024,
                'net_income': net_income_2024,
                'operating_margin': (operating_income_2024 / revenue_2024 * 100) if revenue_2024 else None,
                'net_margin': (net_income_2024 / revenue_2024 * 100) if revenue_2024 else None
            }
        }
    
    def analyze_profitability_funnel(self):
        """分析盈利能力漏斗"""
        print("\n🔄 分析盈利能力漏斗...")
        
        funnel_2024 = self.analyzers['funnel'].get_profitability_funnel_by_year(2024)
        
        funnel_data = {
            'company_name': funnel_2024.company_name,
            'period': funnel_2024.period,
            'total_conversion_rate': funnel_2024.total_conversion_rate,
            'levels': [],
            'key_insights': funnel_2024.key_insights
        }
        
        for level in funnel_2024.levels:
            level_data = {
                'name': level.name,
                'value': level.value,
                'unit': level.unit,
                'conversion_rate': level.conversion_rate,
                'efficiency_ratio': level.efficiency_ratio,
                'children': []
            }
            
            for child in level.children:
                level_data['children'].append({
                    'name': child.name,
                    'value': child.value,
                    'conversion_rate': child.conversion_rate
                })
            
            funnel_data['levels'].append(level_data)
        
        self.report_data['profitability_funnel'] = funnel_data
    
    def analyze_trends(self):
        """分析趋势"""
        print("\n📈 分析多年趋势...")
        
        # 生成综合趋势报告
        trend_report = self.analyzers['trend'].generate_comprehensive_report()
        
        trend_data = {
            'company_name': trend_report.company_name,
            'analysis_period': trend_report.analysis_period,
            'overall_growth_score': trend_report.overall_growth_score,
            'growth_quality_score': trend_report.growth_quality_score,
            'executive_summary': trend_report.executive_summary
        }
        
        # 收入趋势
        if trend_report.revenue_trend:
            revenue_trend = trend_report.revenue_trend
            trend_data['revenue_trend'] = {
                'metric_name': revenue_trend.metric_name,
                'total_growth_rate': revenue_trend.total_growth_rate,
                'cagr': revenue_trend.cagr,
                'average_growth_rate': revenue_trend.average_growth_rate,
                'trend_direction': revenue_trend.trend_direction,
                'volatility': revenue_trend.volatility,
                'data_points': [
                    {
                        'period': point.period,
                        'value': point.value
                    } for point in revenue_trend.data_points
                ],
                'insights': revenue_trend.insights
            }
        
        # 利润趋势
        if trend_report.profit_trend:
            profit_trend = trend_report.profit_trend
            trend_data['profit_trend'] = {
                'metric_name': profit_trend.metric_name,
                'total_growth_rate': profit_trend.total_growth_rate,
                'cagr': profit_trend.cagr,
                'average_growth_rate': profit_trend.average_growth_rate,
                'trend_direction': profit_trend.trend_direction,
                'volatility': profit_trend.volatility,
                'insights': profit_trend.insights
            }
        
        # 利润率趋势
        if trend_report.margin_trends:
            trend_data['margin_trends'] = {}
            for margin_name, margin_trend in trend_report.margin_trends.items():
                trend_data['margin_trends'][margin_name] = {
                    'metric_name': margin_trend.metric_name,
                    'cagr': margin_trend.cagr,
                    'trend_direction': margin_trend.trend_direction,
                    'insights': margin_trend.insights
                }
        
        self.report_data['trends'] = trend_data
    
    def analyze_business_segments(self):
        """分析业务细分"""
        print("\n🔍 分析业务细分...")
        
        # 收入细分
        revenue_breakdown = self.analyzers['drill_down'].drill_down_revenue_by_year(2024)
        
        # 费用细分
        expense_breakdown = self.analyzers['drill_down'].drill_down_expenses_by_year(2024)
        
        # 资产细分
        asset_breakdown = self.analyzers['drill_down'].drill_down_assets_by_year(2024)
        
        self.report_data['business_segments'] = {
            'revenue_breakdown': {
                'total_value': revenue_breakdown.parent_value,
                'concentration_ratio': revenue_breakdown.concentration_ratio,
                'diversity_score': revenue_breakdown.diversity_score,
                'items': [
                    {
                        'name': item.name,
                        'value': item.value,
                        'percentage': item.percentage_of_total
                    } for item in revenue_breakdown.items[:10]  # 前10项
                ],
                'key_insights': revenue_breakdown.key_insights
            },
            'expense_breakdown': {
                'total_value': expense_breakdown.parent_value,
                'concentration_ratio': expense_breakdown.concentration_ratio,
                'items': [
                    {
                        'name': item.name,
                        'value': item.value,
                        'percentage': item.percentage_of_total
                    } for item in expense_breakdown.items[:10]
                ],
                'key_insights': expense_breakdown.key_insights
            },
            'asset_breakdown': {
                'total_value': asset_breakdown.parent_value,
                'concentration_ratio': asset_breakdown.concentration_ratio,
                'items': [
                    {
                        'name': item.name,
                        'value': item.value,
                        'percentage': item.percentage_of_total
                    } for item in asset_breakdown.items[:10]
                ],
                'key_insights': asset_breakdown.key_insights
            }
        }
    
    def analyze_efficiency_metrics(self):
        """分析效率指标"""
        print("\n⚡ 分析运营效率...")
        
        # 转换率分析
        conversion_analysis = self.analyzers['efficiency'].calculate_conversion_rates_by_year(2024)
        
        # 利润率分析
        margin_analysis = self.analyzers['efficiency'].calculate_margin_analysis_by_year(2024)
        
        # 资本效率分析
        capital_efficiency = self.analyzers['efficiency'].calculate_capital_efficiency_by_year(2024)
        
        self.report_data['efficiency_metrics'] = {
            'conversion_analysis': {
                'funnel_name': conversion_analysis.funnel_name,
                'total_conversion_rate': conversion_analysis.total_conversion_rate,
                'efficiency_score': conversion_analysis.efficiency_score,
                'stages': conversion_analysis.stages,
                'bottlenecks': conversion_analysis.bottlenecks,
                'improvement_opportunities': conversion_analysis.improvement_opportunities
            },
            'margin_analysis': {
                'period': margin_analysis.period,
                'margins': {}
            },
            'capital_efficiency': {
                'period': capital_efficiency.period,
                'capital_efficiency_score': capital_efficiency.capital_efficiency_score,
                'metrics': {},
                'key_insights': capital_efficiency.key_insights
            }
        }
        
        # 添加利润率详情
        for margin_name in ['gross_margin', 'operating_margin', 'net_margin', 'ebitda_margin', 'cash_margin']:
            margin = getattr(margin_analysis, margin_name)
            if margin:
                self.report_data['efficiency_metrics']['margin_analysis']['margins'][margin_name] = {
                    'value': margin.value,
                    'unit': margin.unit,
                    'performance_rating': margin.performance_rating,
                    'benchmark_value': margin.benchmark_value,
                    'description': margin.description
                }
        
        # 添加资本效率详情
        for metric_name in ['roe', 'roa', 'asset_turnover', 'inventory_turnover', 'receivables_turnover']:
            metric = getattr(capital_efficiency, metric_name)
            if metric:
                self.report_data['efficiency_metrics']['capital_efficiency']['metrics'][metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'performance_rating': metric.performance_rating,
                    'description': metric.description
                }
    
    def analyze_financial_ratios(self):
        """分析财务比率"""
        print("\n📊 分析财务比率...")
        
        # 获取2024年所有指标
        metrics_2024 = self.analyzers['metrics'].calculate_all_metrics_by_year(2024)
        
        # 获取指标摘要
        metrics_summary = self.analyzers['metrics'].get_metrics_summary_by_year(2024)
        
        # 按类别组织指标
        ratios_by_category = {}
        for category_name, category_metrics in metrics_summary['categories'].items():
            ratios_by_category[category_name] = {}
            for metric_name, metric_result in category_metrics.items():
                ratios_by_category[category_name][metric_name] = {
                    'value': metric_result.value,
                    'unit': metric_result.unit,
                    'description': metric_result.description,
                    'data_quality': metric_result.data_quality,
                    'formula': metric_result.formula
                }
        
        self.report_data['financial_ratios'] = {
            'fiscal_year': 2024,
            'categories': ratios_by_category,
            'data_quality': metrics_summary['data_quality'],
            'key_insights': metrics_summary['key_insights']
        }
    
    def generate_executive_summary(self):
        """生成执行摘要"""
        print("\n📝 生成执行摘要...")
        
        # 提取关键数据
        revenue_2024 = self.report_data['financial_performance']['revenue']['2024']
        revenue_growth = self.report_data['financial_performance']['revenue']['yoy_growth']
        net_margin = self.report_data['financial_performance']['profitability']['net_margin']
        
        # 生成摘要
        summary_points = []
        
        # 收入表现
        if revenue_2024:
            summary_points.append(f"2024财年营业收入达到${revenue_2024:,.0f}百万美元")
            if revenue_growth:
                if revenue_growth > 0:
                    summary_points.append(f"同比增长{revenue_growth:.1f}%，显示业务增长动力")
                else:
                    summary_points.append(f"同比下降{abs(revenue_growth):.1f}%，面临增长挑战")
        
        # 盈利能力
        if net_margin:
            if net_margin > 20:
                summary_points.append(f"净利润率{net_margin:.1f}%，盈利能力优秀")
            elif net_margin > 15:
                summary_points.append(f"净利润率{net_margin:.1f}%，盈利能力良好")
            else:
                summary_points.append(f"净利润率{net_margin:.1f}%，盈利能力需要关注")
        
        # 趋势洞察
        if 'trends' in self.report_data:
            trend_insights = self.report_data['trends'].get('executive_summary', [])
            summary_points.extend(trend_insights[:2])  # 添加前2个趋势洞察
        
        # 效率洞察
        if 'efficiency_metrics' in self.report_data:
            efficiency_score = self.report_data['efficiency_metrics']['capital_efficiency']['capital_efficiency_score']
            if efficiency_score > 70:
                summary_points.append("资本配置效率优秀，投资回报良好")
            elif efficiency_score > 50:
                summary_points.append("资本配置效率适中，有改善空间")
            else:
                summary_points.append("资本配置效率偏低，需要优化投资策略")
        
        self.report_data['executive_summary'] = {
            'generation_time': datetime.now().isoformat(),
            'key_points': summary_points,
            'overall_assessment': self._generate_overall_assessment()
        }
    
    def _generate_overall_assessment(self):
        """生成总体评估"""
        # 基于各项指标生成总体评估
        assessment_factors = []
        
        # 收入增长评估
        revenue_growth = self.report_data['financial_performance']['revenue'].get('yoy_growth')
        if revenue_growth:
            if revenue_growth > 5:
                assessment_factors.append("收入增长强劲")
            elif revenue_growth > 0:
                assessment_factors.append("收入保持增长")
            else:
                assessment_factors.append("收入面临下滑压力")
        
        # 盈利能力评估
        net_margin = self.report_data['financial_performance']['profitability'].get('net_margin')
        if net_margin:
            if net_margin > 20:
                assessment_factors.append("盈利能力优秀")
            elif net_margin > 15:
                assessment_factors.append("盈利能力良好")
            else:
                assessment_factors.append("盈利能力需要改善")
        
        # 趋势评估
        if 'trends' in self.report_data:
            growth_score = self.report_data['trends'].get('overall_growth_score', 0)
            if growth_score > 70:
                assessment_factors.append("增长趋势积极")
            elif growth_score > 50:
                assessment_factors.append("增长趋势稳定")
            else:
                assessment_factors.append("增长趋势需要关注")
        
        return "，".join(assessment_factors) + "。"
    
    def generate_report(self):
        """生成完整报告"""
        print("\n📋 生成完整分析报告...")
        
        # 执行所有分析
        self.analyze_company_overview()
        self.analyze_financial_performance()
        self.analyze_profitability_funnel()
        self.analyze_trends()
        self.analyze_business_segments()
        self.analyze_efficiency_metrics()
        self.analyze_financial_ratios()
        self.generate_executive_summary()
        
        # 添加报告元数据
        self.report_data['report_metadata'] = {
            'generation_time': datetime.now().isoformat(),
            'report_version': '1.0',
            'data_source': 'Apple Inc. 10-K Filing (2024-09-28)',
            'analysis_tools': list(self.analyzers.keys()),
            'context_mapping': {
                'revenue_context_id': self.report_data['company_overview']['context_summary']['revenue_context'],
                'balance_sheet_context_id': self.report_data['company_overview']['context_summary']['balance_sheet_context']
            }
        }
        
        return self.report_data
    
    def save_report(self, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            filename = f"apple_2024_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 报告已保存到: {filename}")
        return filename
    
    def print_summary(self):
        """打印报告摘要"""
        print("\n" + "="*80)
        print("🍎 APPLE 2024财年深度分析报告摘要")
        print("="*80)
        
        # 公司概况
        overview = self.report_data['company_overview']
        print(f"\n📊 公司概况:")
        print(f"   公司名称: {overview['company_name']}")
        print(f"   财年结束: {overview['period_end']}")
        print(f"   数据来源: Context ID {overview['context_summary']['revenue_context']} (收入) / {overview['context_summary']['balance_sheet_context']} (资产负债)")
        
        # 财务表现
        performance = self.report_data['financial_performance']
        print(f"\n💰 财务表现:")
        print(f"   2024年营业收入: ${performance['revenue']['2024']:,.0f} 百万美元")
        if performance['revenue']['yoy_growth']:
            print(f"   同比增长率: {performance['revenue']['yoy_growth']:+.1f}%")
        print(f"   营业利润率: {performance['profitability']['operating_margin']:.1f}%")
        print(f"   净利润率: {performance['profitability']['net_margin']:.1f}%")
        
        # 盈利漏斗
        funnel = self.report_data['profitability_funnel']
        print(f"\n🔄 盈利能力漏斗:")
        for level in funnel['levels']:
            if level['conversion_rate']:
                print(f"   {level['name']}: ${level['value']:,.0f}M ({level['conversion_rate']:.1f}%)")
            else:
                print(f"   {level['name']}: ${level['value']:,.0f}M")
        
        # 趋势分析
        if 'trends' in self.report_data:
            trends = self.report_data['trends']
            print(f"\n📈 趋势分析:")
            print(f"   整体增长评分: {trends['overall_growth_score']:.1f}/100")
            print(f"   增长质量评分: {trends['growth_quality_score']:.1f}/100")
            if trends.get('revenue_trend', {}).get('cagr'):
                print(f"   收入复合增长率: {trends['revenue_trend']['cagr']:.1f}%")
        
        # 业务细分
        segments = self.report_data['business_segments']
        print(f"\n🔍 业务细分:")
        print(f"   收入集中度: {segments['revenue_breakdown']['concentration_ratio']:.1f}% (前三大来源)")
        print(f"   收入多样性: {segments['revenue_breakdown']['diversity_score']:.1f}/100")
        
        # 效率指标
        efficiency = self.report_data['efficiency_metrics']
        print(f"\n⚡ 效率指标:")
        print(f"   资本效率评分: {efficiency['capital_efficiency']['capital_efficiency_score']:.1f}/100")
        if 'roe' in efficiency['capital_efficiency']['metrics']:
            roe = efficiency['capital_efficiency']['metrics']['roe']
            print(f"   股东权益回报率: {roe['value']:.1f}%")
        
        # 执行摘要
        summary = self.report_data['executive_summary']
        print(f"\n📝 执行摘要:")
        for point in summary['key_points'][:5]:  # 显示前5个要点
            print(f"   • {point}")
        print(f"\n   总体评估: {summary['overall_assessment']}")
        
        print("\n" + "="*80)


def main():
    """主函数"""
    print("🍎 Apple 2024财报深度解读生成器")
    print("="*60)
    
    try:
        # 创建分析生成器
        generator = Apple2024AnalysisGenerator()
        
        # 加载数据
        generator.load_data()
        
        # 生成报告
        report_data = generator.generate_report()
        
        # 保存报告
        filename = generator.save_report()
        
        # 打印摘要
        generator.print_summary()
        
        print(f"\n✅ 分析完成！详细报告已保存到: {filename}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
        print("请确保Apple XBRL文件在当前目录中")
        return False
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)