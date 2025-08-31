"""
Query engine for flexible financial data queries
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Union, Any, Callable
from enum import Enum
import re
from collections import defaultdict

from .models import (
    FinancialFact, StatementType, PeriodType, FinancialStatement,
    FilingData, CompanyInfo
)
from .database.operations import DatabaseManager
from .utils.logging import get_logger
from .utils.exceptions import QueryError, DataValidationError

logger = get_logger(__name__)


class SortOrder(Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


class AggregationType(Enum):
    """Aggregation types"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    FIRST = "first"
    LAST = "last"


@dataclass
class QueryFilter:
    """
    Represents a single query filter
    """
    field: str                          # Field to filter on
    operator: str                       # Operator: eq, ne, gt, lt, gte, lte, in, like, ilike
    value: Union[str, int, float, List, date]  # Filter value
    
    def __post_init__(self):
        """Validate filter parameters"""
        valid_operators = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'like', 'ilike', 'contains']
        if self.operator not in valid_operators:
            raise QueryError(f"Invalid operator '{self.operator}'. Valid operators: {valid_operators}")


@dataclass
class QuerySort:
    """
    Represents sorting criteria
    """
    field: str
    order: SortOrder = SortOrder.ASC


@dataclass
class QueryAggregation:
    """
    Represents aggregation criteria
    """
    field: str                          # Field to aggregate
    type: AggregationType              # Aggregation type
    group_by: Optional[List[str]] = None  # Fields to group by


@dataclass
class FinancialQuery:
    """
    Comprehensive query specification for financial data
    """
    # Basic filters
    concept_pattern: Optional[str] = None
    label_pattern: Optional[str] = None
    statement_types: Optional[List[StatementType]] = None
    period_types: Optional[List[PeriodType]] = None
    
    # Date filters
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    filing_date_start: Optional[date] = None
    filing_date_end: Optional[date] = None
    
    # Company filters
    cik: Optional[str] = None
    company_name_pattern: Optional[str] = None
    ticker: Optional[str] = None
    
    # Value filters
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    units: Optional[List[str]] = None
    
    # Advanced filters
    filters: List[QueryFilter] = field(default_factory=list)
    
    # Sorting and pagination
    sort_by: List[QuerySort] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    # Aggregation
    aggregations: List[QueryAggregation] = field(default_factory=list)
    
    # Include related data
    include_calculations: bool = False
    include_presentations: bool = False
    include_taxonomy: bool = False


@dataclass
class QueryResult:
    """
    Query result with metadata
    """
    facts: List[FinancialFact] = field(default_factory=list)
    total_count: int = 0
    aggregations: Dict[str, Any] = field(default_factory=dict)
    query_time_ms: float = 0.0
    
    # Additional data if requested
    calculations: List[Any] = field(default_factory=list)
    presentations: List[Any] = field(default_factory=list)
    taxonomy_elements: List[Any] = field(default_factory=list)


class QueryEngine:
    """
    Main query engine for financial data
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()
        self._filter_functions = self._build_filter_functions()
        self._aggregation_functions = self._build_aggregation_functions()
    
    def execute_query(self, query: FinancialQuery) -> QueryResult:
        """
        Execute a comprehensive financial data query
        
        Args:
            query: FinancialQuery specification
            
        Returns:
            QueryResult with facts and metadata
            
        Raises:
            QueryError: If query execution fails
        """
        start_time = datetime.now()
        
        try:
            # Get facts from database using basic filters
            facts = self._get_facts_from_db(query)
            
            # Apply in-memory filters
            filtered_facts = self._apply_filters(facts, query.filters)
            
            # Apply value filters
            filtered_facts = self._apply_value_filters(filtered_facts, query)
            
            # Apply sorting
            sorted_facts = self._apply_sorting(filtered_facts, query.sort_by)
            
            # Calculate total count before pagination
            total_count = len(sorted_facts)
            
            # Apply pagination
            paginated_facts = self._apply_pagination(sorted_facts, query.limit, query.offset)
            
            # Calculate aggregations
            aggregations = self._calculate_aggregations(filtered_facts, query.aggregations)
            
            # Calculate query time
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                facts=paginated_facts,
                total_count=total_count,
                aggregations=aggregations,
                query_time_ms=query_time
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise QueryError(f"Query execution failed: {str(e)}")
    
    def search_concepts(self, pattern: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        Search for financial concepts by pattern
        
        Args:
            pattern: Search pattern
            limit: Maximum results
            
        Returns:
            List of concept information
        """
        try:
            facts = self.db_manager.search_facts(
                concept_pattern=pattern,
                limit=limit
            )
            
            # Group by concept to avoid duplicates
            concepts = {}
            for fact in facts:
                if fact.concept not in concepts:
                    concepts[fact.concept] = {
                        'concept': fact.concept,
                        'label': fact.label,
                        'unit': fact.unit,
                        'period_type': fact.period_type.value
                    }
            
            return list(concepts.values())
            
        except Exception as e:
            logger.error(f"Concept search failed: {str(e)}")
            raise QueryError(f"Concept search failed: {str(e)}")
    
    def get_available_periods(self, cik: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available reporting periods
        
        Args:
            cik: Optional company filter
            
        Returns:
            List of period information
        """
        try:
            # Use a broad search to get period information
            facts = self.db_manager.search_facts(cik=cik, limit=1000)
            
            # Group by period
            periods = {}
            for fact in facts:
                if fact.period_end:
                    period_key = fact.period_end.isoformat()
                    if period_key not in periods:
                        periods[period_key] = {
                            'period_end': fact.period_end.isoformat(),
                            'period_start': fact.period_start.isoformat() if fact.period_start else None,
                            'period_type': fact.period_type.value,
                            'fact_count': 0
                        }
                    periods[period_key]['fact_count'] += 1
            
            # Sort by period end date
            return sorted(periods.values(), key=lambda x: x['period_end'], reverse=True)
            
        except Exception as e:
            logger.error(f"Period retrieval failed: {str(e)}")
            raise QueryError(f"Period retrieval failed: {str(e)}")
    
    def get_statement_facts(
        self, 
        statement_type: StatementType, 
        cik: Optional[str] = None,
        period_end: Optional[date] = None
    ) -> List[FinancialFact]:
        """
        Get facts for a specific financial statement
        
        Args:
            statement_type: Type of financial statement
            cik: Optional company filter
            period_end: Optional period filter
            
        Returns:
            List of FinancialFact objects
        """
        query = FinancialQuery(
            statement_types=[statement_type],
            cik=cik,
            period_end=period_end,
            sort_by=[QuerySort('concept', SortOrder.ASC)]
        )
        
        result = self.execute_query(query)
        return result.facts
    
    def _get_facts_from_db(self, query: FinancialQuery) -> List[FinancialFact]:
        """Get facts from database using basic filters"""
        # Convert statement types to database format
        statement_type = None
        if query.statement_types and len(query.statement_types) == 1:
            statement_type = query.statement_types[0]
        
        return self.db_manager.search_facts(
            concept_pattern=query.concept_pattern,
            label_pattern=query.label_pattern,
            statement_type=statement_type,
            period_start=query.period_start,
            period_end=query.period_end,
            cik=query.cik,
            limit=query.limit or 1000
        )
    
    def _apply_filters(self, facts: List[FinancialFact], filters: List[QueryFilter]) -> List[FinancialFact]:
        """Apply custom filters to facts"""
        if not filters:
            return facts
        
        filtered_facts = []
        for fact in facts:
            if self._fact_matches_filters(fact, filters):
                filtered_facts.append(fact)
        
        return filtered_facts
    
    def _fact_matches_filters(self, fact: FinancialFact, filters: List[QueryFilter]) -> bool:
        """Check if a fact matches all filters"""
        for filter_obj in filters:
            if not self._apply_single_filter(fact, filter_obj):
                return False
        return True
    
    def _apply_single_filter(self, fact: FinancialFact, filter_obj: QueryFilter) -> bool:
        """Apply a single filter to a fact"""
        # Get field value from fact
        field_value = getattr(fact, filter_obj.field, None)
        
        if field_value is None:
            return filter_obj.operator == 'ne'  # Only 'not equal' matches None
        
        # Get filter function
        filter_func = self._filter_functions.get(filter_obj.operator)
        if not filter_func:
            raise QueryError(f"Unknown filter operator: {filter_obj.operator}")
        
        return filter_func(field_value, filter_obj.value)
    
    def _apply_value_filters(self, facts: List[FinancialFact], query: FinancialQuery) -> List[FinancialFact]:
        """Apply value-based filters"""
        filtered_facts = facts
        
        # Filter by value range
        if query.min_value is not None or query.max_value is not None:
            filtered_facts = [
                fact for fact in filtered_facts
                if self._value_in_range(fact.value, query.min_value, query.max_value)
            ]
        
        # Filter by units
        if query.units:
            filtered_facts = [
                fact for fact in filtered_facts
                if fact.unit in query.units
            ]
        
        # Filter by statement types (if multiple)
        if query.statement_types and len(query.statement_types) > 1:
            # This would require statement type classification logic
            # For now, we'll skip this advanced filtering
            pass
        
        return filtered_facts
    
    def _value_in_range(self, value: Any, min_val: Optional[float], max_val: Optional[float]) -> bool:
        """Check if value is in specified range"""
        try:
            numeric_value = float(value)
            if min_val is not None and numeric_value < min_val:
                return False
            if max_val is not None and numeric_value > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    def _apply_sorting(self, facts: List[FinancialFact], sort_criteria: List[QuerySort]) -> List[FinancialFact]:
        """Apply sorting to facts"""
        if not sort_criteria:
            return facts
        
        # Apply sorts in reverse order (last sort is primary)
        sorted_facts = facts.copy()
        for sort_obj in reversed(sort_criteria):
            reverse = sort_obj.order == SortOrder.DESC
            
            try:
                sorted_facts.sort(
                    key=lambda fact: getattr(fact, sort_obj.field, ''),
                    reverse=reverse
                )
            except Exception as e:
                logger.warning(f"Sort failed for field {sort_obj.field}: {str(e)}")
        
        return sorted_facts
    
    def _apply_pagination(self, facts: List[FinancialFact], limit: Optional[int], offset: Optional[int]) -> List[FinancialFact]:
        """Apply pagination to facts"""
        start_idx = offset or 0
        end_idx = start_idx + (limit or len(facts))
        
        return facts[start_idx:end_idx]
    
    def _calculate_aggregations(self, facts: List[FinancialFact], aggregations: List[QueryAggregation]) -> Dict[str, Any]:
        """Calculate aggregations on facts"""
        if not aggregations:
            return {}
        
        results = {}
        
        for agg in aggregations:
            if agg.group_by:
                # Group by specified fields
                grouped_results = self._calculate_grouped_aggregation(facts, agg)
                results[f"{agg.field}_{agg.type.value}_by_{'+'.join(agg.group_by)}"] = grouped_results
            else:
                # Simple aggregation
                result = self._calculate_simple_aggregation(facts, agg)
                results[f"{agg.field}_{agg.type.value}"] = result
        
        return results
    
    def _calculate_simple_aggregation(self, facts: List[FinancialFact], agg: QueryAggregation) -> Any:
        """Calculate simple aggregation without grouping"""
        values = []
        for fact in facts:
            field_value = getattr(fact, agg.field, None)
            if field_value is not None:
                values.append(field_value)
        
        if not values:
            return None
        
        agg_func = self._aggregation_functions.get(agg.type)
        if not agg_func:
            raise QueryError(f"Unknown aggregation type: {agg.type}")
        
        return agg_func(values)
    
    def _calculate_grouped_aggregation(self, facts: List[FinancialFact], agg: QueryAggregation) -> Dict[str, Any]:
        """Calculate aggregation with grouping"""
        groups = defaultdict(list)
        
        # Group facts by specified fields
        for fact in facts:
            group_key = tuple(str(getattr(fact, field, '')) for field in agg.group_by)
            field_value = getattr(fact, agg.field, None)
            if field_value is not None:
                groups[group_key].append(field_value)
        
        # Calculate aggregation for each group
        results = {}
        agg_func = self._aggregation_functions.get(agg.type)
        if not agg_func:
            raise QueryError(f"Unknown aggregation type: {agg.type}")
        
        for group_key, values in groups.items():
            group_name = '+'.join(group_key)
            results[group_name] = agg_func(values)
        
        return results
    
    def _build_filter_functions(self) -> Dict[str, Callable]:
        """Build dictionary of filter functions"""
        return {
            'eq': lambda field_val, filter_val: field_val == filter_val,
            'ne': lambda field_val, filter_val: field_val != filter_val,
            'gt': lambda field_val, filter_val: self._safe_compare(field_val, filter_val, lambda a, b: a > b),
            'lt': lambda field_val, filter_val: self._safe_compare(field_val, filter_val, lambda a, b: a < b),
            'gte': lambda field_val, filter_val: self._safe_compare(field_val, filter_val, lambda a, b: a >= b),
            'lte': lambda field_val, filter_val: self._safe_compare(field_val, filter_val, lambda a, b: a <= b),
            'in': lambda field_val, filter_val: field_val in filter_val if isinstance(filter_val, (list, tuple)) else False,
            'like': lambda field_val, filter_val: self._pattern_match(str(field_val), str(filter_val), case_sensitive=True),
            'ilike': lambda field_val, filter_val: self._pattern_match(str(field_val), str(filter_val), case_sensitive=False),
            'contains': lambda field_val, filter_val: str(filter_val).lower() in str(field_val).lower()
        }
    
    def _build_aggregation_functions(self) -> Dict[AggregationType, Callable]:
        """Build dictionary of aggregation functions"""
        return {
            AggregationType.SUM: lambda values: sum(self._to_numeric(v) for v in values if self._is_numeric(v)),
            AggregationType.AVG: lambda values: sum(self._to_numeric(v) for v in values if self._is_numeric(v)) / len([v for v in values if self._is_numeric(v)]) if any(self._is_numeric(v) for v in values) else None,
            AggregationType.COUNT: lambda values: len(values),
            AggregationType.MIN: lambda values: min(values) if values else None,
            AggregationType.MAX: lambda values: max(values) if values else None,
            AggregationType.FIRST: lambda values: values[0] if values else None,
            AggregationType.LAST: lambda values: values[-1] if values else None
        }
    
    def _safe_compare(self, field_val: Any, filter_val: Any, compare_func: Callable) -> bool:
        """Safely compare values with type conversion"""
        try:
            # Try numeric comparison first
            if self._is_numeric(field_val) and self._is_numeric(filter_val):
                return compare_func(self._to_numeric(field_val), self._to_numeric(filter_val))
            
            # Fall back to string comparison
            return compare_func(str(field_val), str(filter_val))
        except (ValueError, TypeError):
            return False
    
    def _pattern_match(self, field_val: str, pattern: str, case_sensitive: bool = True) -> bool:
        """Pattern matching with SQL-like wildcards"""
        # Convert SQL wildcards to regex
        regex_pattern = pattern.replace('%', '.*').replace('_', '.')
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            return bool(re.match(regex_pattern, field_val, flags))
        except re.error:
            # If regex fails, fall back to simple contains
            if case_sensitive:
                return pattern in field_val
            else:
                return pattern.lower() in field_val.lower()
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _to_numeric(self, value: Any) -> float:
        """Convert value to numeric"""
        return float(value)


class FilterBuilder:
    """
    Helper class to build query filters
    """
    
    @staticmethod
    def concept_equals(concept: str) -> QueryFilter:
        """Filter by exact concept match"""
        return QueryFilter(field='concept', operator='eq', value=concept)
    
    @staticmethod
    def concept_contains(pattern: str) -> QueryFilter:
        """Filter by concept containing pattern"""
        return QueryFilter(field='concept', operator='contains', value=pattern)
    
    @staticmethod
    def label_contains(pattern: str) -> QueryFilter:
        """Filter by label containing pattern"""
        return QueryFilter(field='label', operator='contains', value=pattern)
    
    @staticmethod
    def value_greater_than(value: float) -> QueryFilter:
        """Filter by value greater than threshold"""
        return QueryFilter(field='value', operator='gt', value=value)
    
    @staticmethod
    def value_between(min_val: float, max_val: float) -> List[QueryFilter]:
        """Filter by value in range"""
        return [
            QueryFilter(field='value', operator='gte', value=min_val),
            QueryFilter(field='value', operator='lte', value=max_val)
        ]
    
    @staticmethod
    def period_equals(period: str) -> QueryFilter:
        """Filter by exact period match"""
        return QueryFilter(field='period', operator='eq', value=period)
    
    @staticmethod
    def unit_in(units: List[str]) -> QueryFilter:
        """Filter by unit in list"""
        return QueryFilter(field='unit', operator='in', value=units)