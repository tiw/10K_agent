"""
Context Validator

Utilities for validating and filtering XBRL facts based on their context information
to ensure we get the correct data for specific periods and entities.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from dataclasses import dataclass

from ..models import FinancialFact, PeriodType
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContextFilter:
    """Filter criteria for XBRL contexts"""
    fiscal_year: Optional[int] = None
    period_type: Optional[PeriodType] = None
    entity_cik: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    context_pattern: Optional[str] = None


class ContextValidator:
    """
    Validates and filters financial facts based on their XBRL context information
    """
    
    @staticmethod
    def filter_facts_by_context(facts: List[FinancialFact], 
                               context_filter: ContextFilter) -> List[FinancialFact]:
        """
        Filter facts based on context criteria
        
        Args:
            facts: List of financial facts to filter
            context_filter: Filter criteria
            
        Returns:
            Filtered list of facts
        """
        filtered_facts = []
        
        for fact in facts:
            if ContextValidator._matches_context_filter(fact, context_filter):
                filtered_facts.append(fact)
        
        logger.debug(f"Filtered {len(facts)} facts to {len(filtered_facts)} based on context")
        return filtered_facts
    
    @staticmethod
    def _matches_context_filter(fact: FinancialFact, context_filter: ContextFilter) -> bool:
        """Check if a fact matches the context filter"""
        
        # Check fiscal year
        if context_filter.fiscal_year is not None:
            if not fact.period_end or fact.period_end.year != context_filter.fiscal_year:
                return False
        
        # Check period type
        if context_filter.period_type is not None:
            if fact.period_type != context_filter.period_type:
                return False
        
        # Check entity CIK (would need to be extracted from context)
        if context_filter.entity_cik is not None:
            # This would require parsing the context_id or having entity info in the fact
            # For now, we'll skip this check
            pass
        
        # Check period start
        if context_filter.period_start is not None:
            if not fact.period_start or fact.period_start < context_filter.period_start:
                return False
        
        # Check period end
        if context_filter.period_end is not None:
            if not fact.period_end or fact.period_end > context_filter.period_end:
                return False
        
        # Check context pattern
        if context_filter.context_pattern is not None:
            if context_filter.context_pattern not in fact.context_id:
                return False
        
        return True
    
    @staticmethod
    def get_best_fact_for_concept(facts: List[FinancialFact], 
                                 concept: str,
                                 fiscal_year: Optional[int] = None,
                                 prefer_duration: bool = True) -> Optional[FinancialFact]:
        """
        Get the best fact for a concept based on context validation
        
        Args:
            facts: List of facts to choose from
            concept: Concept name to match
            fiscal_year: Preferred fiscal year
            prefer_duration: Whether to prefer duration over instant periods
            
        Returns:
            Best matching fact or None
        """
        # Filter by concept
        concept_facts = [f for f in facts if f.concept.endswith(concept) or concept in f.concept]
        
        if not concept_facts:
            return None
        
        # Filter by fiscal year if specified
        if fiscal_year is not None:
            year_facts = [f for f in concept_facts if f.period_end and f.period_end.year == fiscal_year]
            if year_facts:
                concept_facts = year_facts
        
        # Prefer duration or instant based on concept type
        if prefer_duration:
            duration_facts = [f for f in concept_facts if f.period_type == PeriodType.DURATION]
            if duration_facts:
                concept_facts = duration_facts
        else:
            instant_facts = [f for f in concept_facts if f.period_type == PeriodType.INSTANT]
            if instant_facts:
                concept_facts = instant_facts
        
        # Return the most recent fact
        if concept_facts:
            return max(concept_facts, key=lambda f: f.period_end or date.min)
        
        return None
    
    @staticmethod
    def validate_revenue_context(fact: FinancialFact) -> Dict[str, Any]:
        """
        Validate that a revenue fact has the correct context
        
        Args:
            fact: Revenue fact to validate
            
        Returns:
            Validation result with details
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'context_info': {
                'context_id': fact.context_id,
                'period_type': fact.period_type.value,
                'period_start': fact.period_start.isoformat() if fact.period_start else None,
                'period_end': fact.period_end.isoformat() if fact.period_end else None,
                'fiscal_year': fact.period_end.year if fact.period_end else None
            }
        }
        
        # Revenue should typically be duration type
        if fact.period_type != PeriodType.DURATION:
            validation_result['warnings'].append(
                f"Revenue fact has period_type '{fact.period_type.value}' but 'duration' is expected"
            )
        
        # Should have both start and end dates for duration
        if fact.period_type == PeriodType.DURATION:
            if not fact.period_start:
                validation_result['warnings'].append("Duration period missing start date")
            if not fact.period_end:
                validation_result['warnings'].append("Duration period missing end date")
        
        # Check for reasonable fiscal year period (typically 12 months)
        if fact.period_start and fact.period_end:
            period_days = (fact.period_end - fact.period_start).days
            if period_days < 350 or period_days > 380:  # Allow some flexibility
                validation_result['warnings'].append(
                    f"Period length is {period_days} days, expected ~365 days for annual revenue"
                )
        
        # Mark as invalid if there are critical issues
        if any('missing' in warning for warning in validation_result['warnings']):
            validation_result['is_valid'] = False
        
        return validation_result
    
    @staticmethod
    def get_context_summary(facts: List[FinancialFact]) -> Dict[str, Any]:
        """
        Get a summary of contexts in the facts
        
        Args:
            facts: List of facts to analyze
            
        Returns:
            Context summary information
        """
        context_summary = {
            'total_facts': len(facts),
            'unique_contexts': len(set(f.context_id for f in facts)),
            'fiscal_years': sorted(set(f.period_end.year for f in facts if f.period_end)),
            'period_types': {
                'duration': len([f for f in facts if f.period_type == PeriodType.DURATION]),
                'instant': len([f for f in facts if f.period_type == PeriodType.INSTANT])
            },
            'context_patterns': {}
        }
        
        # Analyze context ID patterns
        context_ids = [f.context_id for f in facts]
        for context_id in set(context_ids):
            count = context_ids.count(context_id)
            context_summary['context_patterns'][context_id] = count
        
        return context_summary
    
    @staticmethod
    def find_revenue_contexts(facts: List[FinancialFact]) -> List[Dict[str, Any]]:
        """
        Find all contexts that contain revenue data
        
        Args:
            facts: List of all facts
            
        Returns:
            List of revenue context information
        """
        revenue_concepts = [
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'Revenues',
            'Revenue'
        ]
        
        revenue_contexts = []
        
        for fact in facts:
            # Check if this is a revenue fact
            if any(concept.lower() in fact.concept.lower() for concept in revenue_concepts):
                context_info = {
                    'context_id': fact.context_id,
                    'concept': fact.concept,
                    'value': fact.value,
                    'scaled_value': fact.get_scaled_value(),
                    'period_type': fact.period_type.value,
                    'period_start': fact.period_start.isoformat() if fact.period_start else None,
                    'period_end': fact.period_end.isoformat() if fact.period_end else None,
                    'fiscal_year': fact.period_end.year if fact.period_end else None,
                    'validation': ContextValidator.validate_revenue_context(fact)
                }
                revenue_contexts.append(context_info)
        
        # Sort by fiscal year and period end
        revenue_contexts.sort(key=lambda x: (x['fiscal_year'] or 0, x['period_end'] or ''))
        
        return revenue_contexts