🚀 Advanced Financial Analysis Demo
============================================================
📊 Parsing Apple's XBRL filing...
2025-08-31 09:22:39,729 - xbrl_financial_service.xbrl_parser - INFO - Progress: 5.0% - Validating XBRL files
2025-08-31 09:22:39,807 - xbrl_financial_service.xbrl_parser - INFO - Progress: 10.0% - Starting XBRL parsing
2025-08-31 09:22:39,807 - xbrl_financial_service.parsers.schema_parser - INFO - Parsing schema file: aapl-20240928.xsd
2025-08-31 09:22:39,807 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsing calculation linkbase: aapl-20240928_cal.xml
2025-08-31 09:22:39,807 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsing definition linkbase: aapl-20240928_def.xml
2025-08-31 09:22:39,807 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsing label linkbase: aapl-20240928_lab.xml
2025-08-31 09:22:39,808 - xbrl_financial_service.parsers.schema_parser - INFO - Successfully parsed 77 elements from schema
2025-08-31 09:22:39,808 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsing presentation linkbase: aapl-20240928_pre.xml
2025-08-31 09:22:39,808 - xbrl_financial_service.xbrl_parser - INFO - Progress: 20.0% - Parsed schema
2025-08-31 09:22:39,811 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsed 209 calculation relationships
2025-08-31 09:22:39,811 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsed 384 definition relationships
2025-08-31 09:22:39,811 - xbrl_financial_service.xbrl_parser - INFO - Progress: 30.0% - Parsed calculation
2025-08-31 09:22:39,812 - xbrl_financial_service.parsers.instance_parser - INFO - Parsing instance document: aapl-20240928_htm.xml
2025-08-31 09:22:39,812 - xbrl_financial_service.xbrl_parser - INFO - Progress: 40.0% - Parsed definition
2025-08-31 09:22:39,816 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsed labels for 684 concepts
2025-08-31 09:22:39,818 - xbrl_financial_service.xbrl_parser - INFO - Progress: 50.0% - Parsed label
2025-08-31 09:22:39,820 - xbrl_financial_service.parsers.linkbase_parser - INFO - Parsed 767 presentation relationships
2025-08-31 09:22:39,822 - xbrl_financial_service.xbrl_parser - INFO - Progress: 60.0% - Parsed presentation
2025-08-31 09:22:39,832 - xbrl_financial_service.parsers.instance_parser - WARNING - Failed to parse fact element {http://xbrl.sec.gov/dei/2024}DocumentPeriodEndDate: could not convert string to float: '2024-09-28'
2025-08-31 09:22:39,832 - xbrl_financial_service.parsers.instance_parser - WARNING - Failed to parse fact element {http://xbrl.sec.gov/dei/2024}CurrentFiscalYearEndDate: could not convert string to float: '--09-28'
2025-08-31 09:22:39,832 - xbrl_financial_service.parsers.instance_parser - WARNING - Failed to parse fact element {http://xbrl.sec.gov/dei/2024}EntityFileNumber: could not convert string to float: '001-36743'
2025-08-31 09:22:39,832 - xbrl_financial_service.parsers.instance_parser - WARNING - Failed to parse fact element {http://xbrl.sec.gov/dei/2024}EntityTaxIdentificationNumber: could not convert string to float: '94-2404110'
2025-08-31 09:22:39,832 - xbrl_financial_service.parsers.instance_parser - WARNING - Failed to parse fact element {http://xbrl.sec.gov/dei/2024}LocalPhoneNumber: could not convert string to float: '996-1010'
2025-08-31 09:22:39,842 - xbrl_financial_service.parsers.instance_parser - INFO - Successfully parsed 1120 facts from instance document
2025-08-31 09:22:39,843 - xbrl_financial_service.xbrl_parser - INFO - Progress: 70.0% - Parsed instance
2025-08-31 09:22:39,843 - xbrl_financial_service.xbrl_parser - INFO - Progress: 80.0% - Building financial statements
2025-08-31 09:22:39,845 - xbrl_financial_service.xbrl_parser - INFO - Progress: 90.0% - Validating data
2025-08-31 09:22:39,856 - xbrl_financial_service.xbrl_parser - INFO - Data quality score: 91.01%
2025-08-31 09:22:39,856 - xbrl_financial_service.xbrl_parser - INFO - Total facts: 1040
2025-08-31 09:22:39,863 - xbrl_financial_service.xbrl_parser - INFO - Calculation accuracy: 0.00%
2025-08-31 09:22:39,863 - xbrl_financial_service.xbrl_parser - INFO - Validated calculations: 0
2025-08-31 09:22:39,863 - xbrl_financial_service.xbrl_parser - WARNING - Balance sheet equation validation failed
2025-08-31 09:22:39,863 - xbrl_financial_service.xbrl_parser - WARNING - Balance difference: 2853.24%
2025-08-31 09:22:39,863 - xbrl_financial_service.xbrl_parser - INFO - Progress: 100.0% - Parsing completed in 0.13s
2025-08-31 09:22:39,863 - xbrl_financial_service.xbrl_parser - INFO - Successfully parsed XBRL filing with 1120 facts
✅ Successfully parsed filing!
   Company: Apple Inc.
   Total Facts: 1120
2025-08-31 09:22:39,864 - xbrl_financial_service.database.connection - INFO - Creating database engine for: sqlite:///data/financial_data.db
2025-08-31 09:22:39,897 - xbrl_financial_service.database.operations - INFO - Database initialized successfully
2025-08-31 09:22:39,905 - xbrl_financial_service.search_engine - INFO - Built search indexes with 3 concepts
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: gross_profit_margin
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: operating_profit_margin
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: net_profit_margin
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: return_on_assets
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: return_on_equity
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: current_ratio
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: quick_ratio
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: cash_ratio
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: debt_to_equity
2025-08-31 09:22:39,905 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: debt_to_assets
2025-08-31 09:22:39,906 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: interest_coverage
2025-08-31 09:22:39,906 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: asset_turnover
2025-08-31 09:22:39,906 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: inventory_turnover
2025-08-31 09:22:39,906 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: receivables_turnover
2025-08-31 09:22:39,906 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: earnings_per_share
2025-08-31 09:22:39,906 - xbrl_financial_service.analysis.metrics_calculator - INFO - Added custom metric: book_value_per_share

🔄 FUNNEL ANALYSIS
========================================
2025-08-31 09:22:39,906 - xbrl_financial_service.utils.context_mapper - INFO - Analyzing XBRL contexts...
2025-08-31 09:22:39,907 - xbrl_financial_service.analysis.funnel_analyzer - INFO - Building profitability funnel

📈 Profitability Funnel (Apple Inc.):
   营业收入 (Revenue): $294,866
   毛利润 (Gross Profit): $109,633 (37.2%)
   营业利润 (Operating Income): $123,216 (41.8%)
     └─ 研发费用: $-31,370 (10.6%)
     └─ 销售管理费用: $-26,097 (8.9%)
   净利润 (Net Income): $93,736 (31.8%)

💡 Key Insights:
   • 毛利率 37.2% 处于合理水平
   • 营业利润率 41.8% 优秀，运营效率高
   • 净利润率 31.8%，整体盈利能力强
2025-08-31 09:22:39,907 - xbrl_financial_service.analysis.funnel_analyzer - INFO - Building cash conversion funnel

💰 Cash Conversion Funnel:
   营业收入 (Revenue): $294,866
   经营现金流 (Operating Cash Flow): $118,254 (40.1%)
   自由现金流 (Free Cash Flow): $108,807 (36.9%)

📈 TREND ANALYSIS
========================================
2025-08-31 09:22:39,908 - xbrl_financial_service.utils.context_mapper - INFO - Analyzing XBRL contexts...

📊 Revenue Trend Analysis:
   Periods analyzed: 3
   CAGR: -0.42%
   Trend direction: stable
   Average growth: -0.39%

   Period-by-period data:
     2021-09-26_to_2022-09-24: $394,328
     2022-09-25_to_2023-09-30: $383,285
     2023-10-01_to_2024-09-28: $391,035
2025-08-31 09:22:39,909 - xbrl_financial_service.analysis.trend_analyzer - INFO - Generating comprehensive trend report

📋 Comprehensive Trend Report:
   Overall growth score: 48.2/100
   Growth quality score: 50.0/100

   Executive Summary:
     • 营收复合增长率-0.4%，增长放缓
     • 利润复合增长率-3.1%，盈利增长滞后

🔍 DRILL-DOWN ANALYSIS
========================================
2025-08-31 09:22:39,910 - xbrl_financial_service.analysis.drill_down_engine - INFO - Performing revenue drill-down analysis

💰 Revenue Breakdown:
   Total Revenue: $294,866
   Breakdown items: 0
   Concentration ratio: 0.0%
   Diversity score: 0.0/100
2025-08-31 09:22:39,910 - xbrl_financial_service.analysis.drill_down_engine - INFO - Performing expense drill-down analysis

💸 Expense Breakdown:
   Total Expenses: $57,467

   Top expense categories:
     研发费用: $31,370 (54.6%)
     销售管理费用: $26,097 (45.4%)
     折旧摊销: $11,445 (19.9%)
2025-08-31 09:22:39,910 - xbrl_financial_service.analysis.drill_down_engine - INFO - Performing asset drill-down analysis

🏦 Asset Breakdown:
   Total Assets: $364,980

   Top asset categories:
     OtherAssetsNoncurrent: $74,834 (20.5%)
     固定资产: $45,680 (12.5%)
     应收账款: $33,410 (9.2%)
     现金及等价物: $29,943 (8.2%)
     存货: $7,286 (2.0%)

⚡ EFFICIENCY ANALYSIS
========================================
2025-08-31 09:22:39,910 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating conversion rates

🔄 Business Conversion Funnel:
   Efficiency score: 100.0/100
   Total conversion rate: 36.90%

   Conversion stages:
     营业收入: $294,866 (100.0%)
     营业利润: $123,216 (41.8%)
     净利润: $93,736 (31.8%)
     经营现金流: $118,254 (40.1%)
     自由现金流: $108,807 (36.9%)

   💡 Improvement opportunities:
     • 从营业收入到营业利润转换率下降58.2%，存在显著改善机会
2025-08-31 09:22:39,910 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating margin analysis

📊 Margin Analysis:
   Gross Margin: 37.2% (偏低) vs 65.0% benchmark
   Operating Margin: 41.8% (优秀) vs 25.0% benchmark
   Net Margin: 31.8% (优秀) vs 20.0% benchmark
   EBITDA Margin: 45.7%
   Cash Margin: 40.1% (优秀) vs 25.0% benchmark
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating capital efficiency

🏛️ Capital Efficiency:
   Overall score: 100.0/100
   ROE: 164.6% (优秀)
   ROA: 25.7% (优秀)
   Asset Turnover: 0.8倍 (良好)
   Inventory Turnover: 25.4倍
   Receivables Turnover: 8.8倍
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Generating comprehensive efficiency report
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating conversion rates
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating margin analysis
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating capital efficiency
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating conversion rates
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating margin analysis
2025-08-31 09:22:39,911 - xbrl_financial_service.analysis.efficiency_calculator - INFO - Calculating capital efficiency

📋 Efficiency Summary:
   Overall efficiency score: 100.0/100

   💪 Key Strengths:
     • 业务转换效率优秀，各环节协调良好
     • 股东权益回报率优秀，价值创造能力强

   📝 Executive Summary:
     • 整体运营效率优秀，各项指标表现良好
     • 净利润率31.8%，盈利能力强
     • 股东权益回报率164.6%，股东价值创造优秀

✅ Advanced financial analysis demo completed successfully!
