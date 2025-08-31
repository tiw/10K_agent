#!/usr/bin/env python3
"""
Test script for comprehensive error handling and validation system
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from xbrl_financial_service.validators import XBRLValidator, DataValidator, CalculationValidator
from xbrl_financial_service.error_handler import error_handler, handle_errors, error_context
from xbrl_financial_service.xbrl_parser import XBRLParser
from xbrl_financial_service.financial_service import FinancialService
from xbrl_financial_service.config import Config
from xbrl_financial_service.utils.exceptions import *


def test_xbrl_file_validation():
    """Test XBRL file validation"""
    print("Testing XBRL file validation...")
    
    # Test with Apple XBRL files
    file_paths = {
        'schema': 'aapl-20240928.xsd',
        'calculation': 'aapl-20240928_cal.xml',
        'definition': 'aapl-20240928_def.xml',
        'label': 'aapl-20240928_lab.xml',
        'presentation': 'aapl-20240928_pre.xml',
        'instance': 'aapl-20240928_htm.xml'
    }
    
    validator = XBRLValidator()
    
    try:
        # Test file completeness validation
        print("  ✓ Testing file completeness...")
        validator.validate_filing_completeness(file_paths)
        print("    File completeness validation passed")
        
        # Test XML structure validation
        print("  ✓ Testing XML structure...")
        for file_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                validator.validate_xml_structure(file_path)
                print(f"    XML structure validation passed for {file_type}")
        
        # Test namespace validation
        print("  ✓ Testing XBRL namespaces...")
        for file_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                validator.validate_xbrl_namespaces(file_path)
                print(f"    Namespace validation passed for {file_type}")
        
        # Test data type validation for instance document
        print("  ✓ Testing data types...")
        if os.path.exists(file_paths['instance']):
            validator.validate_data_types(file_paths['instance'])
            print("    Data type validation passed")
        
        # Get validation report
        report = validator.get_validation_report()
        print(f"  ✓ Validation report: {report['error_count']} errors, {report['warning_count']} warnings")
        
        return True
        
    except Exception as e:
        print(f"  ✗ XBRL validation failed: {e}")
        return False


def test_data_quality_validation():
    """Test data quality validation"""
    print("Testing data quality validation...")
    
    try:
        # Parse Apple XBRL files first
        config = Config()
        parser = XBRLParser(config)
        
        file_paths = {
            'schema': 'aapl-20240928.xsd',
            'calculation': 'aapl-20240928_cal.xml',
            'definition': 'aapl-20240928_def.xml',
            'label': 'aapl-20240928_lab.xml',
            'presentation': 'aapl-20240928_pre.xml',
            'instance': 'aapl-20240928_htm.xml'
        }
        
        # Check if files exist
        existing_files = {k: v for k, v in file_paths.items() if os.path.exists(v)}
        
        if not existing_files:
            print("  ⚠ No XBRL files found, skipping data quality validation")
            return True
        
        print(f"  ✓ Found {len(existing_files)} XBRL files")
        
        # Parse filing data
        filing_data = parser.parse_filing(existing_files)
        print(f"  ✓ Parsed filing with {len(filing_data.all_facts)} facts")
        
        # Test data quality validation
        data_validator = DataValidator()
        
        # Test completeness validation
        print("  ✓ Testing data completeness...")
        completeness_report = data_validator.validate_data_completeness(filing_data)
        print(f"    Completeness score: {completeness_report['completeness_score']:.2%}")
        
        # Test consistency validation
        print("  ✓ Testing data consistency...")
        consistency_report = data_validator.validate_data_consistency(filing_data)
        print(f"    Cross-statement issues: {len(consistency_report['cross_statement_issues'])}")
        
        # Test overall quality
        print("  ✓ Testing overall data quality...")
        quality_report = data_validator.validate_data_quality(filing_data)
        print(f"    Quality score: {quality_report['data_quality_score']:.2%}")
        
        # Generate comprehensive report
        print("  ✓ Generating comprehensive quality report...")
        comprehensive_report = data_validator.generate_data_quality_report(filing_data)
        print(f"    Overall score: {comprehensive_report['overall_score']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Data quality validation failed: {e}")
        return False


def test_calculation_validation():
    """Test calculation validation"""
    print("Testing calculation validation...")
    
    try:
        # Parse Apple XBRL files first
        config = Config()
        parser = XBRLParser(config)
        
        file_paths = {
            'schema': 'aapl-20240928.xsd',
            'calculation': 'aapl-20240928_cal.xml',
            'definition': 'aapl-20240928_def.xml',
            'label': 'aapl-20240928_lab.xml',
            'presentation': 'aapl-20240928_pre.xml',
            'instance': 'aapl-20240928_htm.xml'
        }
        
        # Check if files exist
        existing_files = {k: v for k, v in file_paths.items() if os.path.exists(v)}
        
        if not existing_files:
            print("  ⚠ No XBRL files found, skipping calculation validation")
            return True
        
        # Parse filing data
        filing_data = parser.parse_filing(existing_files)
        
        # Test calculation validation
        calc_validator = CalculationValidator()
        
        # Test overall calculation validation
        print("  ✓ Testing calculation relationships...")
        calc_report = calc_validator.validate_calculations(filing_data)
        print(f"    Calculation accuracy: {calc_report['calculation_accuracy']:.2%}")
        print(f"    Validated calculations: {calc_report['validated_calculations']}")
        print(f"    Failed calculations: {calc_report['failed_calculations']}")
        
        # Test balance sheet equation
        if filing_data.balance_sheet and filing_data.balance_sheet.facts:
            print("  ✓ Testing balance sheet equation...")
            balance_report = calc_validator.validate_balance_sheet_equation(
                filing_data.balance_sheet.facts
            )
            print(f"    Balance sheet balanced: {balance_report['is_balanced']}")
            if balance_report['difference_percentage']:
                print(f"    Difference: {balance_report['difference_percentage']:.2%}")
        
        # Test income statement calculations
        if filing_data.income_statement and filing_data.income_statement.facts:
            print("  ✓ Testing income statement calculations...")
            income_report = calc_validator.validate_income_statement_calculations(
                filing_data.income_statement.facts
            )
            print(f"    Income statement accuracy: {income_report['overall_accuracy']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Calculation validation failed: {e}")
        return False


def test_error_handling_system():
    """Test comprehensive error handling system"""
    print("Testing error handling system...")
    
    try:
        # Test error handler initialization
        print("  ✓ Testing error handler initialization...")
        print(f"    Error handler initialized with {len(error_handler.error_counts)} error types")
        
        # Test structured error responses
        print("  ✓ Testing structured error responses...")
        
        # Create a test error
        test_error = DataValidationError(
            "Test validation error",
            validation_type="test",
            details={"test_field": "test_value"},
            suggestions=["This is a test suggestion"]
        )
        
        # Handle the error
        error_response = error_handler.handle_error(
            test_error,
            context={"test_context": "test_value"},
            user_friendly=True
        )
        
        print(f"    Error response structure: {list(error_response.keys())}")
        if 'error' in error_response and error_response['error']:
            print(f"    Error type: {error_response['error'].get('type', 'unknown')}")
            print(f"    Has suggestions: {len(error_response['error'].get('suggestions', [])) > 0}")
        else:
            print("    Error response format unexpected")
        
        # Test error statistics
        print("  ✓ Testing error statistics...")
        stats = error_handler.get_error_statistics()
        print(f"    Health status: {stats['health_status']}")
        print(f"    Total errors tracked: {stats['total_errors']}")
        
        # Test error decorator
        print("  ✓ Testing error decorator...")
        
        @handle_errors(return_response=True, user_friendly=True)
        def test_function_with_error():
            raise QueryError("Test query error")
        
        result = test_function_with_error()
        print(f"    Decorator handled error: {not result['success']}")
        
        # Test error context manager
        print("  ✓ Testing error context manager...")
        
        try:
            with error_context({"operation": "test_context"}):
                raise DataValidationError("Test context error")
        except DataValidationError as e:
            print(f"    Context added to error: {'operation' in e.details}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error handling system test failed: {e}")
        return False


def test_integration_with_financial_service():
    """Test integration with financial service"""
    print("Testing integration with financial service...")
    
    try:
        # Test financial service with error handling
        config = Config()
        service = FinancialService(config=config)
        
        # Test error handling for missing data
        print("  ✓ Testing error handling for missing data...")
        
        try:
            service.get_income_statement()
            print("    ✗ Expected error for missing data")
            return False
        except QueryError as e:
            print(f"    ✓ Correctly raised QueryError: {e.error_type}")
        
        # Test with actual data if available
        file_paths = {
            'schema': 'aapl-20240928.xsd',
            'calculation': 'aapl-20240928_cal.xml',
            'definition': 'aapl-20240928_def.xml',
            'label': 'aapl-20240928_lab.xml',
            'presentation': 'aapl-20240928_pre.xml',
            'instance': 'aapl-20240928_htm.xml'
        }
        
        existing_files = {k: v for k, v in file_paths.items() if os.path.exists(v)}
        
        if existing_files:
            print("  ✓ Testing with actual XBRL data...")
            
            # Parse the filing data first
            parser = XBRLParser(config)
            filing_data = parser.parse_filing(existing_files)
            service.filing_data = filing_data
            
            # Test successful operations
            income_statement = service.get_income_statement()
            if income_statement:
                print(f"    ✓ Successfully retrieved income statement with {len(income_statement.facts)} facts")
            else:
                print("    ⚠ Income statement not available")
            
            balance_sheet = service.get_balance_sheet()
            if balance_sheet:
                print(f"    ✓ Successfully retrieved balance sheet with {len(balance_sheet.facts)} facts")
            else:
                print("    ⚠ Balance sheet not available")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Financial service integration test failed: {e}")
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("XBRL Financial Service - Validation System Test")
    print("=" * 60)
    
    tests = [
        ("XBRL File Validation", test_xbrl_file_validation),
        ("Data Quality Validation", test_data_quality_validation),
        ("Calculation Validation", test_calculation_validation),
        ("Error Handling System", test_error_handling_system),
        ("Financial Service Integration", test_integration_with_financial_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
                
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:4} | {test_name}")
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        return 0
    else:
        print("⚠️  Some validation tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)