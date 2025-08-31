#!/usr/bin/env python3
"""
Demo script showcasing the query engine and data access layer functionality
"""

import sys
import os
from datetime import date, datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xbrl_financial_service.query_engine import (
    QueryEngine, FinancialQuery, QueryFilter, QuerySort, QueryAggregation,
    SortOrder, AggregationType, FilterBuilder
)
from xbrl_financial_service.search_engine import SearchEngine
from xbrl_financial_service.cache_manager import CacheManager
from xbrl_financial_service.financial_service import FinancialService
from xbrl_financial_service.database.operations import DatabaseManager
from xbrl_financial_service.models import StatementType, PeriodType
from xbrl_financial_service.config import Config


def demo_basic_queries():
    """Demonstrate basic query functionality"""
    print("=" * 60)
    print("1. BASIC QUERY FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize components
    config = Config()
    db_manager = DatabaseManager(config)
    query_engine = QueryEngine(db_manager)
    
    # Demo 1: Simple concept search
    print("\n📊 Demo 1: Simple Concept Search")
    print("-" * 40)
    
    query = FinancialQuery(
        concept_pattern="Revenue",
        limit=5
    )
    
    result = query_engine.execute_query(query)
    print(f"Query: Search for 'Revenue' concepts")
    print(f"Results: {result.total_count} facts found in {result.query_time_ms:.2f}ms")
    
    for i, fact in enumerate(result.facts[:3], 1):
        print(f"  {i}. {fact.concept}: {fact.label}")
        print(f"     Value: {fact.value} {fact.unit or ''}")


def main():
    """Run demo"""
    print("🎯 XBRL Financial Service - Query Engine & Data Access Layer Demo")
    
    try:
        demo_basic_queries()
        
        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())