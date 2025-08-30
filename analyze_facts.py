#!/usr/bin/env python3
"""
分析XBRL财务事实的详细内容
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from xbrl_financial_service import XBRLParser, FinancialService, Config
from xbrl_financial_service.utils.logging import setup_logging


def analyze_facts():
    """分析财务事实的详细内容"""
    print("🔍 XBRL财务事实详细分析")
    print("=" * 60)
    
    # Setup logging (减少输出)
    setup_logging(level="WARNING")
    
    # Create configuration
    config = Config()
    config.enable_parallel_processing = True
    
    # Create parser
    parser = XBRLParser(config)
    
    # Define file paths
    file_paths = {
        'schema': 'aapl-20240928.xsd',
        'calculation': 'aapl-20240928_cal.xml',
        'definition': 'aapl-20240928_def.xml',
        'label': 'aapl-20240928_lab.xml',
        'presentation': 'aapl-20240928_pre.xml',
        'instance': 'aapl-20240928_htm.xml'
    }
    
    try:
        print("📊 解析XBRL文件...")
        filing_data = parser.parse_filing(file_paths)
        
        print(f"✅ 解析完成！总共 {len(filing_data.all_facts)} 个事实")
        
        # 创建财务服务
        service = FinancialService(filing_data, config)
        
        # 分析损益表事实
        print(f"\n📈 损益表事实详细分析")
        print("=" * 40)
        
        income_statement = service.get_income_statement()
        if income_statement:
            facts = income_statement.facts
            print(f"损益表总事实数: {len(facts)}")
            
            # 按概念分组
            concept_counts = Counter(fact.concept for fact in facts)
            print(f"\n📋 按概念分组 (前20个):")
            for concept, count in concept_counts.most_common(20):
                print(f"  {concept}: {count}个")
            
            # 按期间分组
            period_counts = Counter(fact.period for fact in facts)
            print(f"\n📅 按期间分组:")
            for period, count in sorted(period_counts.items()):
                print(f"  {period}: {count}个事实")
            
            # 按单位分组
            unit_counts = Counter(fact.unit for fact in facts)
            print(f"\n💰 按单位分组:")
            for unit, count in unit_counts.most_common(10):
                unit_display = unit if unit else "无单位"
                print(f"  {unit_display}: {count}个")
            
            # 显示一些具体的事实示例
            print(f"\n🔍 损益表事实示例 (前10个):")
            for i, fact in enumerate(facts[:10], 1):
                value_display = f"{fact.value:,}" if isinstance(fact.value, (int, float)) else str(fact.value)
                print(f"  {i}. {fact.label}")
                print(f"     概念: {fact.concept}")
                print(f"     值: {value_display} {fact.unit or ''}")
                print(f"     期间: {fact.period}")
                print()
            
            # 分析为什么这么多事实
            print(f"\n🤔 为什么有这么多事实？")
            print("=" * 30)
            
            # 按概念类型分析
            concept_types = defaultdict(int)
            for fact in facts:
                if 'revenue' in fact.concept.lower() or 'revenue' in fact.label.lower():
                    concept_types['收入相关'] += 1
                elif 'expense' in fact.concept.lower() or 'expense' in fact.label.lower():
                    concept_types['费用相关'] += 1
                elif 'income' in fact.concept.lower() or 'income' in fact.label.lower():
                    concept_types['收益相关'] += 1
                elif 'cost' in fact.concept.lower() or 'cost' in fact.label.lower():
                    concept_types['成本相关'] += 1
                else:
                    concept_types['其他'] += 1
            
            print("按概念类型分布:")
            for concept_type, count in concept_types.items():
                print(f"  {concept_type}: {count}个事实")
            
            # 分析多期间数据
            unique_concepts = set(fact.concept for fact in facts)
            print(f"\n📊 统计信息:")
            print(f"  唯一概念数: {len(unique_concepts)}")
            print(f"  平均每个概念的事实数: {len(facts) / len(unique_concepts):.1f}")
            print(f"  不同期间数: {len(period_counts)}")
            
            # 查找重复最多的概念
            print(f"\n🔄 重复最多的概念 (可能是多期间数据):")
            for concept, count in concept_counts.most_common(5):
                # 找到这个概念的所有事实
                concept_facts = [f for f in facts if f.concept == concept]
                periods = set(f.period for f in concept_facts)
                print(f"  {concept}:")
                print(f"    总事实数: {count}")
                print(f"    涉及期间: {len(periods)}个")
                if len(periods) <= 5:  # 如果期间不多，显示具体期间
                    for period in sorted(periods):
                        period_facts = [f for f in concept_facts if f.period == period]
                        print(f"      {period}: {len(period_facts)}个事实")
        
        # 对比其他报表
        print(f"\n📊 各报表事实数对比:")
        print("=" * 30)
        
        statements = [
            ("损益表", service.get_income_statement()),
            ("资产负债表", service.get_balance_sheet()),
            ("现金流量表", service.get_cash_flow_statement())
        ]
        
        # 直接从filing_data获取其他报表
        if filing_data.shareholders_equity:
            statements.append(("股东权益表", filing_data.shareholders_equity))
        if filing_data.comprehensive_income:
            statements.append(("综合收益表", filing_data.comprehensive_income))
        
        for name, statement in statements:
            if statement:
                print(f"  {name}: {len(statement.facts)}个事实")
            else:
                print(f"  {name}: 未找到")
        
        print(f"\n💡 结论:")
        print("XBRL文件包含多个报告期间的数据（如年度、季度数据），")
        print("每个财务概念在不同期间都会有对应的事实，")
        print("所以总事实数会比预期的多。这是XBRL格式的正常特征。")
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_facts()