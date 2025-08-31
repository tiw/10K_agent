"""
Calculation validation module
Validates calculation relationships against linkbase rules and financial logic
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from decimal import Decimal, InvalidOperation
from collections import defaultdict

from ..utils.exceptions import CalculationError, DataValidationError
from ..models import FinancialFact, CalculationRelationship, FilingData


logger = logging.getLogger(__name__)


class CalculationValidator:
    """Validates financial calculations against XBRL linkbase rules"""
    
    def __init__(self, tolerance: float = 0.02):
        """
        Initialize calculation validator
        
        Args:
            tolerance: Tolerance for calculation validation (as percentage, default 2%)
        """
        self.tolerance = tolerance
        self.validation_errors: List[Dict] = []
        self.validation_warnings: List[Dict] = []
    
    def validate_calculations(self, filing_data: FilingData) -> Dict[str, Any]:
        """
        Validate all calculations in the filing data
        
        Args:
            filing_data: Complete filing data with calculation relationships
            
        Returns:
            Dict: Calculation validation report
            
        Raises:
            CalculationError: If critical calculation errors are found
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        validation_report = {
            'calculation_errors': [],
            'calculation_warnings': [],
            'validated_calculations': 0,
            'failed_calculations': 0,
            'calculation_accuracy': 0.0,
            'critical_errors': []
        }
        
        # Validate calculations for each statement
        for statement_name, statement in [
            ('income_statement', filing_data.income_statement),
            ('balance_sheet', filing_data.balance_sheet),
            ('cash_flow_statement', filing_data.cash_flow_statement)
        ]:
            if not statement or not statement.calculations:
                continue
            
            statement_report = self._validate_statement_calculations(
                statement, statement_name
            )
            
            validation_report['calculation_errors'].extend(statement_report['errors'])
            validation_report['calculation_warnings'].extend(statement_report['warnings'])
            validation_report['validated_calculations'] += statement_report['validated_count']
            validation_report['failed_calculations'] += statement_report['failed_count']
        
        # Calculate overall accuracy
        total_calculations = validation_report['validated_calculations'] + validation_report['failed_calculations']
        if total_calculations > 0:
            validation_report['calculation_accuracy'] = (
                validation_report['validated_calculations'] / total_calculations
            )
        
        # Identify critical errors
        critical_errors = [
            error for error in validation_report['calculation_errors']
            if error.get('severity') == 'critical'
        ]
        validation_report['critical_errors'] = critical_errors
        
        # Only raise exception if there are actual critical errors and we have calculations to validate
        if len(critical_errors) > 5 and total_calculations > 0:
            raise CalculationError(
                f"Calculation validation failed: {len(critical_errors)} critical errors, "
                f"{validation_report['calculation_accuracy']:.1%} accuracy",
                calculation_type="overall_validation",
                details=validation_report,
                suggestions=[
                    "Review XBRL calculation linkbase for errors",
                    "Check for data parsing issues",
                    "Verify source filing accuracy",
                    "Review calculation relationship definitions"
                ]
            )
        
        return validation_report
    
    def validate_balance_sheet_equation(self, balance_sheet_facts: List[FinancialFact]) -> Dict[str, Any]:
        """
        Validate the fundamental balance sheet equation: Assets = Liabilities + Equity
        
        Args:
            balance_sheet_facts: List of balance sheet facts
            
        Returns:
            Dict: Balance sheet equation validation report
        """
        equation_report = {
            'is_balanced': False,
            'assets_total': None,
            'liabilities_total': None,
            'equity_total': None,
            'liabilities_plus_equity': None,
            'difference': None,
            'difference_percentage': None,
            'periods_validated': []
        }
        
        # Group facts by period
        facts_by_period = defaultdict(list)
        for fact in balance_sheet_facts:
            facts_by_period[fact.period].append(fact)
        
        period_results = []
        
        for period, period_facts in facts_by_period.items():
            period_result = self._validate_period_balance_sheet_equation(period_facts, period)
            period_results.append(period_result)
            equation_report['periods_validated'].append(period_result)
        
        # Overall assessment
        balanced_periods = [r for r in period_results if r['is_balanced']]
        equation_report['is_balanced'] = len(balanced_periods) == len(period_results)
        
        if period_results:
            # Use most recent period for summary
            latest_result = max(period_results, key=lambda x: x['period'])
            equation_report.update({
                'assets_total': latest_result['assets_total'],
                'liabilities_total': latest_result['liabilities_total'],
                'equity_total': latest_result['equity_total'],
                'liabilities_plus_equity': latest_result['liabilities_plus_equity'],
                'difference': latest_result['difference'],
                'difference_percentage': latest_result['difference_percentage']
            })
        
        return equation_report
    
    def validate_income_statement_calculations(self, income_facts: List[FinancialFact]) -> Dict[str, Any]:
        """
        Validate income statement calculation relationships
        
        Args:
            income_facts: List of income statement facts
            
        Returns:
            Dict: Income statement validation report
        """
        validation_report = {
            'gross_profit_validation': [],
            'operating_income_validation': [],
            'net_income_validation': [],
            'calculation_errors': [],
            'overall_accuracy': 0.0
        }
        
        # Group facts by period
        facts_by_period = defaultdict(list)
        for fact in income_facts:
            facts_by_period[fact.period].append(fact)
        
        total_validations = 0
        successful_validations = 0
        
        for period, period_facts in facts_by_period.items():
            # Validate Gross Profit = Revenue - Cost of Revenue
            gross_profit_result = self._validate_gross_profit_calculation(period_facts, period)
            if gross_profit_result:
                validation_report['gross_profit_validation'].append(gross_profit_result)
                total_validations += 1
                if gross_profit_result['is_valid']:
                    successful_validations += 1
            
            # Validate Operating Income calculations
            operating_income_result = self._validate_operating_income_calculation(period_facts, period)
            if operating_income_result:
                validation_report['operating_income_validation'].append(operating_income_result)
                total_validations += 1
                if operating_income_result['is_valid']:
                    successful_validations += 1
            
            # Validate Net Income calculations
            net_income_result = self._validate_net_income_calculation(period_facts, period)
            if net_income_result:
                validation_report['net_income_validation'].append(net_income_result)
                total_validations += 1
                if net_income_result['is_valid']:
                    successful_validations += 1
        
        # Calculate overall accuracy
        if total_validations > 0:
            validation_report['overall_accuracy'] = successful_validations / total_validations
        
        return validation_report
    
    def validate_cash_flow_calculations(self, cash_flow_facts: List[FinancialFact]) -> Dict[str, Any]:
        """
        Validate cash flow statement calculations
        
        Args:
            cash_flow_facts: List of cash flow facts
            
        Returns:
            Dict: Cash flow validation report
        """
        validation_report = {
            'cash_change_validation': [],
            'section_totals_validation': [],
            'calculation_errors': [],
            'overall_accuracy': 0.0
        }
        
        # Group facts by period
        facts_by_period = defaultdict(list)
        for fact in cash_flow_facts:
            facts_by_period[fact.period].append(fact)
        
        total_validations = 0
        successful_validations = 0
        
        for period, period_facts in facts_by_period.items():
            # Validate total cash change = operating + investing + financing
            cash_change_result = self._validate_cash_change_calculation(period_facts, period)
            if cash_change_result:
                validation_report['cash_change_validation'].append(cash_change_result)
                total_validations += 1
                if cash_change_result['is_valid']:
                    successful_validations += 1
        
        # Calculate overall accuracy
        if total_validations > 0:
            validation_report['overall_accuracy'] = successful_validations / total_validations
        
        return validation_report
    
    def _validate_statement_calculations(self, statement, statement_name: str) -> Dict[str, Any]:
        """Validate calculations for a specific statement"""
        report = {
            'statement': statement_name,
            'errors': [],
            'warnings': [],
            'validated_count': 0,
            'failed_count': 0
        }
        
        if not statement.calculations:
            return report
        
        # Group facts by concept for easy lookup
        facts_by_concept = {fact.concept: fact for fact in statement.facts}
        
        # Group calculations by period and parent
        calculations_by_period = defaultdict(lambda: defaultdict(list))
        
        for calc in statement.calculations:
            # Find facts for this calculation
            parent_facts = [f for f in statement.facts if f.concept == calc.parent]
            child_facts = [f for f in statement.facts if f.concept == calc.child]
            
            for parent_fact in parent_facts:
                for child_fact in child_facts:
                    if parent_fact.period == child_fact.period:
                        calculations_by_period[parent_fact.period][calc.parent].append({
                            'calculation': calc,
                            'parent_fact': parent_fact,
                            'child_fact': child_fact
                        })
        
        # Validate each calculation group
        for period, parent_calculations in calculations_by_period.items():
            for parent_concept, calc_items in parent_calculations.items():
                result = self._validate_calculation_group(calc_items, period, parent_concept)
                
                report['validated_count'] += 1
                
                if result['is_valid']:
                    if result.get('warnings'):
                        report['warnings'].extend(result['warnings'])
                else:
                    report['failed_count'] += 1
                    report['errors'].append(result)
        
        return report
    
    def _validate_calculation_group(self, calc_items: List[Dict], period: str, parent_concept: str) -> Dict[str, Any]:
        """Validate a group of calculations for the same parent concept and period"""
        if not calc_items:
            return {'is_valid': True}
        
        parent_fact = calc_items[0]['parent_fact']
        parent_value = self._get_numeric_value(parent_fact.value)
        
        if parent_value is None:
            return {
                'is_valid': False,
                'error_type': 'non_numeric_parent',
                'parent_concept': parent_concept,
                'period': period,
                'message': f"Parent value is not numeric: {parent_fact.value}"
            }
        
        # Calculate expected value from children
        calculated_value = 0.0
        child_details = []
        
        for item in calc_items:
            calc = item['calculation']
            child_fact = item['child_fact']
            child_value = self._get_numeric_value(child_fact.value)
            
            if child_value is None:
                return {
                    'is_valid': False,
                    'error_type': 'non_numeric_child',
                    'parent_concept': parent_concept,
                    'child_concept': calc.child,
                    'period': period,
                    'message': f"Child value is not numeric: {child_fact.value}"
                }
            
            weighted_value = child_value * calc.weight
            calculated_value += weighted_value
            
            child_details.append({
                'concept': calc.child,
                'value': child_value,
                'weight': calc.weight,
                'weighted_value': weighted_value
            })
        
        # Check if calculation is valid within tolerance
        is_valid = self._values_approximately_equal(parent_value, calculated_value)
        
        result = {
            'is_valid': is_valid,
            'parent_concept': parent_concept,
            'period': period,
            'parent_value': parent_value,
            'calculated_value': calculated_value,
            'difference': abs(parent_value - calculated_value),
            'difference_percentage': abs((parent_value - calculated_value) / parent_value) if parent_value != 0 else 0,
            'child_details': child_details
        }
        
        if not is_valid:
            result.update({
                'error_type': 'calculation_mismatch',
                'message': f"Calculation mismatch for {parent_concept}: expected {calculated_value}, got {parent_value}",
                'severity': 'critical' if result['difference_percentage'] > 0.1 else 'warning'
            })
        
        return result
    
    def _validate_period_balance_sheet_equation(self, period_facts: List[FinancialFact], period: str) -> Dict[str, Any]:
        """Validate balance sheet equation for a specific period"""
        # Find assets, liabilities, and equity totals
        assets_total = self._find_concept_value(period_facts, ['Assets', 'TotalAssets'])
        liabilities_total = self._find_concept_value(period_facts, ['Liabilities', 'TotalLiabilities', 'LiabilitiesTotal'])
        equity_total = self._find_concept_value(period_facts, ['StockholdersEquity', 'ShareholdersEquity', 'Equity'])
        
        # Also try to find combined liabilities and equity
        liabilities_plus_equity = self._find_concept_value(
            period_facts, 
            ['LiabilitiesAndStockholdersEquity', 'LiabilitiesAndShareholdersEquity']
        )
        
        result = {
            'period': period,
            'assets_total': assets_total,
            'liabilities_total': liabilities_total,
            'equity_total': equity_total,
            'liabilities_plus_equity': liabilities_plus_equity,
            'is_balanced': False,
            'difference': None,
            'difference_percentage': None
        }
        
        # Check equation: Assets = Liabilities + Equity
        if assets_total is not None and liabilities_total is not None and equity_total is not None:
            calculated_total = liabilities_total + equity_total
            result['liabilities_plus_equity'] = calculated_total
            result['difference'] = abs(assets_total - calculated_total)
            
            if assets_total != 0:
                result['difference_percentage'] = result['difference'] / abs(assets_total)
            
            result['is_balanced'] = self._values_approximately_equal(assets_total, calculated_total)
        
        # Alternative check: Assets = LiabilitiesAndEquity (if available)
        elif assets_total is not None and liabilities_plus_equity is not None:
            result['difference'] = abs(assets_total - liabilities_plus_equity)
            
            if assets_total != 0:
                result['difference_percentage'] = result['difference'] / abs(assets_total)
            
            result['is_balanced'] = self._values_approximately_equal(assets_total, liabilities_plus_equity)
        
        return result
    
    def _validate_gross_profit_calculation(self, period_facts: List[FinancialFact], period: str) -> Optional[Dict[str, Any]]:
        """Validate Gross Profit = Revenue - Cost of Revenue"""
        revenue = self._find_concept_value(period_facts, ['Revenues', 'Revenue', 'TotalRevenues', 'SalesRevenueNet'])
        cost_of_revenue = self._find_concept_value(period_facts, ['CostOfRevenue', 'CostOfGoodsSold', 'CostOfSales'])
        gross_profit = self._find_concept_value(period_facts, ['GrossProfit'])
        
        if revenue is None or cost_of_revenue is None or gross_profit is None:
            return None
        
        calculated_gross_profit = revenue - cost_of_revenue
        is_valid = self._values_approximately_equal(gross_profit, calculated_gross_profit)
        
        return {
            'period': period,
            'is_valid': is_valid,
            'revenue': revenue,
            'cost_of_revenue': cost_of_revenue,
            'reported_gross_profit': gross_profit,
            'calculated_gross_profit': calculated_gross_profit,
            'difference': abs(gross_profit - calculated_gross_profit),
            'difference_percentage': abs((gross_profit - calculated_gross_profit) / gross_profit) if gross_profit != 0 else 0
        }
    
    def _validate_operating_income_calculation(self, period_facts: List[FinancialFact], period: str) -> Optional[Dict[str, Any]]:
        """Validate Operating Income calculations"""
        gross_profit = self._find_concept_value(period_facts, ['GrossProfit'])
        operating_expenses = self._find_concept_value(period_facts, ['OperatingExpenses', 'CostsAndExpenses'])
        operating_income = self._find_concept_value(period_facts, ['OperatingIncomeLoss', 'OperatingIncome'])
        
        if gross_profit is None or operating_expenses is None or operating_income is None:
            return None
        
        calculated_operating_income = gross_profit - operating_expenses
        is_valid = self._values_approximately_equal(operating_income, calculated_operating_income)
        
        return {
            'period': period,
            'is_valid': is_valid,
            'gross_profit': gross_profit,
            'operating_expenses': operating_expenses,
            'reported_operating_income': operating_income,
            'calculated_operating_income': calculated_operating_income,
            'difference': abs(operating_income - calculated_operating_income),
            'difference_percentage': abs((operating_income - calculated_operating_income) / operating_income) if operating_income != 0 else 0
        }
    
    def _validate_net_income_calculation(self, period_facts: List[FinancialFact], period: str) -> Optional[Dict[str, Any]]:
        """Validate Net Income calculations (simplified)"""
        operating_income = self._find_concept_value(period_facts, ['OperatingIncomeLoss', 'OperatingIncome'])
        net_income = self._find_concept_value(period_facts, ['NetIncomeLoss', 'NetIncome', 'ProfitLoss'])
        
        if operating_income is None or net_income is None:
            return None
        
        # This is a simplified validation - actual calculation would include
        # interest, taxes, and other non-operating items
        return {
            'period': period,
            'is_valid': True,  # Simplified - just check that both values exist
            'operating_income': operating_income,
            'net_income': net_income,
            'note': 'Simplified validation - full calculation requires interest and tax details'
        }
    
    def _validate_cash_change_calculation(self, period_facts: List[FinancialFact], period: str) -> Optional[Dict[str, Any]]:
        """Validate cash flow change calculation"""
        operating_cf = self._find_concept_value(
            period_facts, 
            ['NetCashProvidedByUsedInOperatingActivities', 'CashFlowFromOperatingActivities']
        )
        investing_cf = self._find_concept_value(
            period_facts,
            ['NetCashProvidedByUsedInInvestingActivities', 'CashFlowFromInvestingActivities']
        )
        financing_cf = self._find_concept_value(
            period_facts,
            ['NetCashProvidedByUsedInFinancingActivities', 'CashFlowFromFinancingActivities']
        )
        
        if operating_cf is None or investing_cf is None or financing_cf is None:
            return None
        
        calculated_change = operating_cf + investing_cf + financing_cf
        
        # Try to find reported cash change
        cash_change = self._find_concept_value(
            period_facts,
            ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
             'CashAndCashEquivalentsAtCarryingValuePeriodIncreaseDecrease']
        )
        
        if cash_change is None:
            return {
                'period': period,
                'is_valid': True,  # Can't validate without reported change
                'operating_cf': operating_cf,
                'investing_cf': investing_cf,
                'financing_cf': financing_cf,
                'calculated_change': calculated_change,
                'note': 'No reported cash change found for comparison'
            }
        
        is_valid = self._values_approximately_equal(cash_change, calculated_change)
        
        return {
            'period': period,
            'is_valid': is_valid,
            'operating_cf': operating_cf,
            'investing_cf': investing_cf,
            'financing_cf': financing_cf,
            'reported_change': cash_change,
            'calculated_change': calculated_change,
            'difference': abs(cash_change - calculated_change),
            'difference_percentage': abs((cash_change - calculated_change) / cash_change) if cash_change != 0 else 0
        }
    
    def _find_concept_value(self, facts: List[FinancialFact], concept_names: List[str]) -> Optional[float]:
        """Find the numeric value for any of the given concept names"""
        for fact in facts:
            for concept_name in concept_names:
                if concept_name.lower() in fact.concept.lower():
                    value = self._get_numeric_value(fact.value)
                    if value is not None:
                        return value
        return None
    
    def _get_numeric_value(self, value: Any) -> Optional[float]:
        """Convert value to numeric, handling various formats"""
        if value is None:
            return None
        
        try:
            # Handle string values with commas
            if isinstance(value, str):
                cleaned_value = value.replace(',', '').strip()
                if not cleaned_value:
                    return None
                return float(cleaned_value)
            
            return float(value)
            
        except (ValueError, TypeError):
            return None
    
    def _values_approximately_equal(self, val1: float, val2: float) -> bool:
        """Check if two values are approximately equal within tolerance"""
        if val1 == 0 and val2 == 0:
            return True
        
        if val1 == 0 or val2 == 0:
            return abs(val1 - val2) < 1000  # Allow small absolute difference for zero values
        
        return abs((val1 - val2) / max(abs(val1), abs(val2))) <= self.tolerance