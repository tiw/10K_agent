#!/usr/bin/env python3
"""
Simple test to verify the query engine implementation
"""

print("Testing query engine implementation...")

try:
    from xbrl_financial_service.query_engine import QueryEngine, FinancialQuery
    from xbrl_financial_service.search_engine import SearchEngine
    from xbrl_financial_service.cache_manager import CacheManager
    print("✓ All modules imported successfully")
    
    # Test basic instantiation
    cache_manager = CacheManager()
    print("✓ CacheManager created")
    
    query = FinancialQuery(concept_pattern="test", limit=5)
    print("✓ FinancialQuery created")
    
    print("✅ Implementation test passed!")
    
except Exception as e:
    print(f"❌ Implementation test failed: {str(e)}")
    import traceback
    traceback.print_exc()