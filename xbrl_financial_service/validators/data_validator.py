"""
Data quality assurance module
Validates data completeness, consistency, and quality across financial statements
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime

from ..utils.exceptions import DataValidationError, CalculationError
from ..models import FinancialFact, FinancialStatement, FilingData


logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality, completeness, and consistency"""
    
    # Critical financial statement elements that should be present
    CRITICAL_ELEMENTS = {
        'income_statement': [
            'Revenues', 'Revenue', 'TotalRevenues',
            'NetIncomeLoss', 'NetIncome', 'ProfitLoss',
            'OperatingIncomeLoss', 'OperatingIncome'
        ],
        'balance_sheet': [
            'Assets', 'TotalAssets', 'AssetsCurrent',
            'Liabilities', 'LiabilitiesAndStockholdersEquity',
            'StockholdersEquity', 'ShareholdersEquity'
        ],
        'cash_flow': [
            'NetCashProvidedByUsedInOperatingActivities',
            'NetCashProvidedByUsedInInvestingActivities', 
            'NetCashProvidedByUsedInFinancingActivities',
            'CashAndCashEquivalentsAtCarryingValue'
        ]
    }
    
    # Common calculation relationships to validate
    BALANCE_SHEET_EQUATIONS = [
        ('Assets', '=', ['AssetsCurrent', 'AssetsNoncurrent']),
        ('LiabilitiesAndStockholdersEquity', '=', ['Liabilities', 'StockholdersEquity']),
        ('Assets', '=', ['LiabilitiesAndStockholdersEquity'])
    ]
    
    INCOME_STATEMENT_EQUATIONS = [
        ('GrossProfit', '=', ['Revenues', '-', 'CostOfRevenue']),
        ('OperatingIncomeLoss', '=', ['GrossProfit', '-', 'OperatingExpenses']),
        ('NetIncomeLoss', '=', ['OperatingIncomeLoss', '+', 'NonoperatingIncomeExpense', '-', 'IncomeTaxExpenseBenefit'])
    ]
    
    def __init__(self, tolerance: float = 0.01):
        """
        Initialize data validator
        
        Args:
            tolerance: Tolerance for calculation validation (as percentage)
        """
        self.tolerance = tolerance
        self.validation_errors: List[Dict] = []
        self.validation_warnings: List[Dict] = []
        self.data_quality_issues: List[Dict] = []
    
    def validate_data_completeness(self, filing_data: FilingData) -> Dict[str, Any]:
        """
        Validate completeness of financial data
        
        Args:
            filing_data: Complete filing data to validate
            
        Returns:
            Dict: Completeness report
            
        Raises:
            DataValidationError: If critical data is missing
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        completeness_report = {
            'missing_critical_elements': [],
            'missing_statements': [],
            'data_coverage': {},
            'period_coverage': set(),
            'completeness_score': 0.0
        }
        
        # Check for missing financial statements
        available_statements = set()
        if filing_data.income_statement and filing_data.income_statement.facts:
            available_statements.add('income_statement')
        if filing_data.balance_sheet and filing_data.balance_sheet.facts:
            available_statements.add('balance_sheet')
        if filing_data.cash_flow_statement and filing_data.cash_flow_statement.facts:
            available_statements.add('cash_flow')
        
        expected_statements = {'income_statement', 'balance_sheet', 'cash_flow'}
        missing_statements = expected_statements - available_statements
        
        if missing_statements:
            completeness_report['missing_statements'] = list(missing_statements)
            self.validation_warnings.append({
                'type': 'missing_statements',
                'message': f'Missing financial statements: {", ".join(missing_statements)}',
                'severity': 'high' if len(missing_statements) > 1 else 'medium'
            })
        
        # Check for missing critical elements in each statement
        for statement_type in available_statements:
            statement = getattr(filing_data, statement_type, None)
            if not statement:
                continue
                
            critical_elements = self.CRITICAL_ELEMENTS.get(statement_type, [])
            present_elements = {fact.concept for fact in statement.facts}
            
            missing_elements = []
            for element in critical_elements:
                if not any(element.lower() in concept.lower() for concept in present_elements):
                    missing_elements.append(element)
            
            if missing_elements:
                completeness_report['missing_critical_elements'].extend([
                    {'statement': statement_type, 'element': elem} for elem in missing_elements
                ])
        
        # Analyze period coverage
        all_facts = []
        for statement in [filing_data.income_statement, filing_data.balance_sheet, filing_data.cash_flow_statement]:
            if statement and statement.facts:
                all_facts.extend(statement.facts)
        
        periods = {fact.period for fact in all_facts if fact.period}
        completeness_report['period_coverage'] = periods
        
        # Calculate completeness score
        total_expected = len(expected_statements) * 10  # Assume 10 critical elements per statement
        total_missing = len(missing_statements) * 10 + len(completeness_report['missing_critical_elements'])
        completeness_report['completeness_score'] = max(0, (total_expected - total_missing) / total_expected)
        
        # Raise error if completeness is too low
        if completeness_report['completeness_score'] < 0.5:
            raise DataValidationError(
                f"Data completeness too low: {completeness_report['completeness_score']:.1%}",
                validation_type="data_completeness",
                details=completeness_report,
                suggestions=[
                    "Check if all required XBRL files were processed",
                    "Verify filing contains complete financial statements",
                    "Review parsing logic for missing elements"
                ]
            )
        
        return completeness_report
    
    def validate_data_consistency(self, filing_data: FilingData) -> Dict[str, Any]:
        """
        Validate consistency of data across statements and periods
        
        Args:
            filing_data: Filing data to validate
            
        Returns:
            Dict: Consistency validation report
        """
        consistency_report = {
            'cross_statement_issues': [],
            'period_consistency_issues': [],
            'unit_consistency_issues': [],
            'context_issues': []
        }
        
        # Check cross-statement consistency
        self._validate_cross_statement_consistency(filing_data, consistency_report)
        
        # Check period consistency
        self._validate_period_consistency(filing_data, consistency_report)
        
        # Check unit consistency
        self._validate_unit_consistency(filing_data, consistency_report)
        
        return consistency_report
    
    def validate_data_quality(self, filing_data: FilingData) -> Dict[str, Any]:
        """
        Validate overall data quality including outliers and anomalies
        
        Args:
            filing_data: Filing data to validate
            
        Returns:
            Dict: Data quality report
        """
        quality_report = {
            'outliers': [],
            'anomalies': [],
            'data_quality_score': 0.0,
            'recommendations': []
        }
        
        all_facts = []
        for statement in [filing_data.income_statement, filing_data.balance_sheet, filing_data.cash_flow_statement]:
            if statement and statement.facts:
                all_facts.extend(statement.facts)
        
        # Check for outliers in numeric values
        numeric_facts = [fact for fact in all_facts if self._is_numeric_value(fact.value)]
        
        if numeric_facts:
            values = [float(str(fact.value).replace(',', '')) for fact in numeric_facts]
            outliers = self._detect_outliers(values, numeric_facts)
            quality_report['outliers'] = outliers
        
        # Check for anomalies
        anomalies = self._detect_anomalies(all_facts)
        quality_report['anomalies'] = anomalies
        
        # Calculate quality score
        total_issues = len(quality_report['outliers']) + len(quality_report['anomalies'])
        total_facts = len(all_facts)
        
        if total_facts > 0:
            quality_report['data_quality_score'] = max(0, 1 - (total_issues / total_facts))
        else:
            quality_report['data_quality_score'] = 0.0
        
        # Generate recommendations
        if quality_report['data_quality_score'] < 0.8:
            quality_report['recommendations'].extend([
                "Review data for potential parsing errors",
                "Validate source XBRL files for accuracy",
                "Check for data entry errors in original filing"
            ])
        
        return quality_report
    
    def generate_data_quality_report(self, filing_data: FilingData) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report
        
        Args:
            filing_data: Filing data to analyze
            
        Returns:
            Dict: Comprehensive quality report
        """
        try:
            completeness = self.validate_data_completeness(filing_data)
            consistency = self.validate_data_consistency(filing_data)
            quality = self.validate_data_quality(filing_data)
            
            # Calculate overall score
            overall_score = (
                completeness['completeness_score'] * 0.4 +
                (1 - len(consistency['cross_statement_issues']) / 10) * 0.3 +
                quality['data_quality_score'] * 0.3
            )
            
            return {
                'overall_score': max(0, overall_score),
                'completeness': completeness,
                'consistency': consistency,
                'quality': quality,
                'validation_errors': self.validation_errors,
                'validation_warnings': self.validation_warnings,
                'summary': {
                    'total_facts': sum(len(stmt.facts) for stmt in [
                        filing_data.income_statement,
                        filing_data.balance_sheet, 
                        filing_data.cash_flow_statement
                    ] if stmt),
                    'error_count': len(self.validation_errors),
                    'warning_count': len(self.validation_warnings),
                    'is_acceptable': overall_score >= 0.7
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating data quality report: {e}")
            raise DataValidationError(
                f"Failed to generate data quality report: {str(e)}",
                validation_type="quality_report_generation",
                details={"error": str(e)}
            )
    
    def _validate_cross_statement_consistency(self, filing_data: FilingData, report: Dict) -> None:
        """Validate consistency across financial statements"""
        # Check if cash from balance sheet matches cash flow statement
        if filing_data.balance_sheet and filing_data.cash_flow_statement:
            bs_cash_facts = [
                fact for fact in filing_data.balance_sheet.facts
                if 'cash' in fact.concept.lower() and 'equivalent' in fact.concept.lower()
            ]
            
            cf_cash_facts = [
                fact for fact in filing_data.cash_flow_statement.facts
                if 'cash' in fact.concept.lower() and 'equivalent' in fact.concept.lower()
            ]
            
            # Compare cash values for same periods
            for bs_fact in bs_cash_facts:
                matching_cf_facts = [
                    cf_fact for cf_fact in cf_cash_facts
                    if cf_fact.period == bs_fact.period
                ]
                
                for cf_fact in matching_cf_facts:
                    if not self._values_approximately_equal(bs_fact.value, cf_fact.value):
                        report['cross_statement_issues'].append({
                            'type': 'cash_mismatch',
                            'balance_sheet_value': bs_fact.value,
                            'cash_flow_value': cf_fact.value,
                            'period': bs_fact.period,
                            'difference': abs(float(str(bs_fact.value)) - float(str(cf_fact.value)))
                        })
    
    def _validate_period_consistency(self, filing_data: FilingData, report: Dict) -> None:
        """Validate consistency across periods"""
        all_facts = []
        for statement in [filing_data.income_statement, filing_data.balance_sheet, filing_data.cash_flow_statement]:
            if statement and statement.facts:
                all_facts.extend(statement.facts)
        
        # Group facts by concept
        facts_by_concept = {}
        for fact in all_facts:
            if fact.concept not in facts_by_concept:
                facts_by_concept[fact.concept] = []
            facts_by_concept[fact.concept].append(fact)
        
        # Check for unusual period-over-period changes
        for concept, facts in facts_by_concept.items():
            if len(facts) < 2:
                continue
                
            # Sort by period
            sorted_facts = sorted(facts, key=lambda f: f.period)
            
            for i in range(1, len(sorted_facts)):
                prev_fact = sorted_facts[i-1]
                curr_fact = sorted_facts[i]
                
                if self._is_numeric_value(prev_fact.value) and self._is_numeric_value(curr_fact.value):
                    prev_val = float(str(prev_fact.value).replace(',', ''))
                    curr_val = float(str(curr_fact.value).replace(',', ''))
                    
                    if prev_val != 0:
                        change_pct = abs((curr_val - prev_val) / prev_val)
                        
                        # Flag unusual changes (>500% or <-90%)
                        if change_pct > 5.0:  # 500% change
                            report['period_consistency_issues'].append({
                                'type': 'unusual_change',
                                'concept': concept,
                                'previous_period': prev_fact.period,
                                'current_period': curr_fact.period,
                                'previous_value': prev_val,
                                'current_value': curr_val,
                                'change_percentage': change_pct * 100
                            })
    
    def _validate_unit_consistency(self, filing_data: FilingData, report: Dict) -> None:
        """Validate unit consistency for same concepts"""
        all_facts = []
        for statement in [filing_data.income_statement, filing_data.balance_sheet, filing_data.cash_flow_statement]:
            if statement and statement.facts:
                all_facts.extend(statement.facts)
        
        # Group facts by concept
        facts_by_concept = {}
        for fact in all_facts:
            if fact.concept not in facts_by_concept:
                facts_by_concept[fact.concept] = []
            facts_by_concept[fact.concept].append(fact)
        
        # Check unit consistency within each concept
        for concept, facts in facts_by_concept.items():
            units = {fact.unit for fact in facts if fact.unit}
            
            if len(units) > 1:
                report['unit_consistency_issues'].append({
                    'type': 'inconsistent_units',
                    'concept': concept,
                    'units_found': list(units),
                    'fact_count': len(facts)
                })
    
    def _is_numeric_value(self, value: Any) -> bool:
        """Check if value is numeric"""
        if value is None:
            return False
        
        try:
            float(str(value).replace(',', ''))
            return True
        except (ValueError, TypeError):
            return False
    
    def _values_approximately_equal(self, val1: Any, val2: Any) -> bool:
        """Check if two values are approximately equal within tolerance"""
        if not self._is_numeric_value(val1) or not self._is_numeric_value(val2):
            return str(val1) == str(val2)
        
        try:
            num1 = float(str(val1).replace(',', ''))
            num2 = float(str(val2).replace(',', ''))
            
            if num1 == 0 and num2 == 0:
                return True
            
            if num1 == 0 or num2 == 0:
                return abs(num1 - num2) < 1000  # Allow small absolute difference for zero values
            
            return abs((num1 - num2) / max(abs(num1), abs(num2))) <= self.tolerance
            
        except (ValueError, ZeroDivisionError):
            return False
    
    def _detect_outliers(self, values: List[float], facts: List[FinancialFact]) -> List[Dict]:
        """Detect statistical outliers in numeric values"""
        if len(values) < 4:
            return []
        
        # Calculate quartiles
        sorted_values = sorted(values)
        n = len(sorted_values)
        q1 = sorted_values[n // 4]
        q3 = sorted_values[3 * n // 4]
        iqr = q3 - q1
        
        # Define outlier bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append({
                    'type': 'statistical_outlier',
                    'concept': facts[i].concept,
                    'value': value,
                    'period': facts[i].period,
                    'bound_type': 'lower' if value < lower_bound else 'upper',
                    'bound_value': lower_bound if value < lower_bound else upper_bound
                })
        
        return outliers
    
    def _detect_anomalies(self, facts: List[FinancialFact]) -> List[Dict]:
        """Detect data anomalies"""
        anomalies = []
        
        for fact in facts:
            # Check for negative values where they shouldn't be
            if self._is_numeric_value(fact.value):
                value = float(str(fact.value).replace(',', ''))
                
                # Revenue should generally be positive
                if 'revenue' in fact.concept.lower() and value < 0:
                    anomalies.append({
                        'type': 'negative_revenue',
                        'concept': fact.concept,
                        'value': value,
                        'period': fact.period
                    })
                
                # Assets should generally be positive
                if 'asset' in fact.concept.lower() and 'liability' not in fact.concept.lower() and value < 0:
                    anomalies.append({
                        'type': 'negative_assets',
                        'concept': fact.concept,
                        'value': value,
                        'period': fact.period
                    })
            
            # Check for missing units on monetary values
            if (any(keyword in fact.concept.lower() for keyword in ['revenue', 'income', 'expense', 'asset', 'liability', 'cash']) 
                and not fact.unit):
                anomalies.append({
                    'type': 'missing_unit',
                    'concept': fact.concept,
                    'value': fact.value,
                    'period': fact.period
                })
        
        return anomalies