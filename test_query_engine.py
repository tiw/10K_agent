#!/usr/bin/env python3
"""
Test script for the query engine and data access layer
"""

import sys
import os
from datetime import date

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xbrl_financial_service.query_engine import (
    QueryEngine, FinancialQuery, QueryFilter, QuerySort, QueryAggregation,
    SortOrder, AggregationType, FilterBuilder
)
from xbrl_financial_service.search_engine import SearchEngine
from xbrl_financial_service.cache_manager import CacheManager
from xbrl_financial_service.database.operations import DatabaseManager
from xbrl_financial_service.models import StatementType, PeriodType
from xbrl_financial_service.config import Config


def test_query_engine():
    """Test the query engine functionality"""
    print("Testing Query Engine...")
    
    try:
        # Initialize components
        config = Config()
        db_manager = DatabaseManager(config)
        query_engine = QueryEngine(db_manager)
        
        # Test basic query
        query = FinancialQuery(
            concept_pattern="Revenue",
            limit=10
        )
        
        result = query_engine.execute_query(query)
        print(f"✓ Basic query executed successfully")
        print(f"  - Found {result.total_count} facts")
        print(f"  - Query time: {result.query_time_ms:.2f}ms")
        
        # Test filter builder
        filters = [
            FilterBuilder.concept_contains("Revenue"),
            FilterBuilder.value_greater_than(1000000)
        ]
        
        query_with_filters = FinancialQuery(
            filters=filters,
            limit=5
        )
        
        result_with_filters = query_engine.execute_query(query_with_filters)
        print(f"✓ Query with filters executed successfully")
        print(f"  - Found {result_with_filters.total_count} facts")
        
        # Test concept search
        concepts = query_engine.search_concepts("Revenue", limit=5)
        print(f"✓ Concept search executed successfully")
        print(f"  - Found {len(concepts)} concepts")
        
        # Test available periods
        periods = query_engine.get_available_periods()
        print(f"✓ Available periods retrieved successfully")
        print(f"  - Found {len(periods)} periods")
        
        return True
        
    except Exception as e:
        print(f"✗ Query engine test failed: {str(e)}")
        return False


def test_search_engine():
    """Test the search engine functionality"""
    print("\nTesting Search Engine...")
    
    try:
        # Initialize components
        config = Config()
        db_manager = DatabaseManager(config)
        query_engine = QueryEngine(db_manager)
        search_engine = SearchEngine(db_manager, query_engine)
        
        # Test basic search
        search_response = search_engine.search(
            query="revenue",
            limit=5,
            include_suggestions=True
        )
        
        print(f"✓ Basic search executed successfully")
        print(f"  - Found {search_response.total_count} results")
        print(f"  - Query time: {search_response.query_time_ms:.2f}ms")
        print(f"  - Suggestions: {len(search_response.suggestions)}")
        
        # Test concept suggestions
        suggestions = search_engine.suggest_concepts("rev", limit=5)
        print(f"✓ Concept suggestions retrieved successfully")
        print(f"  - Found {len(suggestions)} suggestions")
        
        # Test facets
        facets = search_engine.get_search_facets("revenue")
        print(f"✓ Search facets retrieved successfully")
        print(f"  - Facet categories: {list(facets.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ Search engine test failed: {str(e)}")
        return False


def test_cache_manager():
    """Test the cache manager functionality"""
    print("\nTesting Cache Manager...")
    
    try:
        # Initialize cache manager
        config = Config()
        cache_manager = CacheManager(config)
        
        # Test query result caching
        test_result = {"test": "data", "count": 42}
        cache_key = "test_query_123"
        
        # Cache the result
        cache_manager.cache_query_result(cache_key, test_result)
        
        # Retrieve from cache
        cached_result = cache_manager.get_query_result(cache_key)
        
        if cached_result == test_result:
            print("✓ Query result caching works correctly")
        else:
            print("✗ Query result caching failed")
            return False
        
        # Test cache statistics
        stats = cache_manager.get_cache_stats()
        print(f"✓ Cache statistics retrieved successfully")
        print(f"  - Query cache entries: {stats['query_cache']['entry_count']}")
        
        # Test cache invalidation
        invalidated = cache_manager.invalidate_company_data("test_cik")
        print(f"✓ Cache invalidation executed (invalidated {invalidated} entries)")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache manager test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("XBRL Financial Service - Query Engine Test Suite")
    print("=" * 60)
    
    tests = [
        test_query_engine,
        test_search_engine,
        test_cache_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())