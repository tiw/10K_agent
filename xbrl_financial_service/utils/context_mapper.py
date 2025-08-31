"""
Context ID Mapper

Analyzes XBRL context IDs to identify which contexts correspond to specific
fiscal years and period types, enabling accurate data retrieval.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import date, datetime
from dataclasses import dataclass
from collections import defaultdict

from ..models import FinancialFact, PeriodType
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContextInfo:
    """Information about a specific XBRL context"""
    context_id: str
    period_type: PeriodType
    period_start: Optional[date]
    period_end: Optional[date]
    fiscal_year: Optional[int]
    entity_cik: Optional[str]
    fact_count: int
    sample_concepts: List[str]  # Sample concepts using this context


@dataclass
class ContextMapping:
    """Mapping of fiscal years to their corresponding context IDs"""
    fiscal_year_contexts: Dict[int, Dict[PeriodType, List[str]]]  # year -> period_type -> context_ids
    context_details: Dict[str, ContextInfo]  # context_id -> details
    revenue_contexts: Dict[int, str]  # fiscal_year -> preferred_context_id for revenue
    balance_sheet_contexts: Dict[int, str]  # fiscal_year -> preferred_context_id for balance sheet


class ContextMapper:
    """
    Maps XBRL context IDs to fiscal years and identifies the correct contexts
    for different types of financial data
    """
    
    def __init__(self, facts: List[FinancialFact]):
        self.facts = facts
        self.context_mapping = self._analyze_contexts()
    
    def _analyze_contexts(self) -> ContextMapping:
        """Analyze all contexts and create mapping"""
        logger.info("Analyzing XBRL contexts...")
        
        # Group facts by context ID
        facts_by_context = defaultdict(list)
        for fact in self.facts:
            facts_by_context[fact.context_id].append(fact)
        
        # Analyze each context
        context_details = {}
        fiscal_year_contexts = defaultdict(lambda: defaultdict(list))
        
        for context_id, context_facts in facts_by_context.items():
            context_info = self._analyze_single_context(context_id, context_facts)
            context_details[context_id] = context_info
            
            # Map to fiscal year
            if context_info.fiscal_year:
                fiscal_year_contexts[context_info.fiscal_year][context_info.period_type].append(context_id)
        
        # Identify preferred contexts for revenue and balance sheet
        revenue_contexts = self._identify_revenue_contexts(fiscal_year_contexts, context_details)
        balance_sheet_contexts = self._identify_balance_sheet_contexts(fiscal_year_contexts, context_details)
        
        return ContextMapping(
            fiscal_year_contexts=dict(fiscal_year_contexts),
            context_details=context_details,
            revenue_contexts=revenue_contexts,
            balance_sheet_contexts=balance_sheet_contexts
        )
    
    def _analyze_single_context(self, context_id: str, context_facts: List[FinancialFact]) -> ContextInfo:
        """Analyze a single context to extract its characteristics"""
        if not context_facts:
            return ContextInfo(
                context_id=context_id,
                period_type=PeriodType.DURATION,
                period_start=None,
                period_end=None,
                fiscal_year=None,
                entity_cik=None,
                fact_count=0,
                sample_concepts=[]
            )
        
        # Get representative fact (most facts should have same context info)
        representative_fact = context_facts[0]
        
        # Determine fiscal year from period_end
        fiscal_year = None
        if representative_fact.period_end:
            fiscal_year = representative_fact.period_end.year
        
        # Get sample concepts (up to 5)
        sample_concepts = list(set(fact.concept for fact in context_facts[:5]))
        
        return ContextInfo(
            context_id=context_id,
            period_type=representative_fact.period_type,
            period_start=representative_fact.period_start,
            period_end=representative_fact.period_end,
            fiscal_year=fiscal_year,
            entity_cik=None,  # Would need to extract from context parsing
            fact_count=len(context_facts),
            sample_concepts=sample_concepts
        )
    
    def _identify_revenue_contexts(self, fiscal_year_contexts: Dict, context_details: Dict[str, ContextInfo]) -> Dict[int, str]:
        """Identify the best context ID for revenue data for each fiscal year"""
        revenue_contexts = {}
        
        for fiscal_year, period_contexts in fiscal_year_contexts.items():
            # For revenue, prefer duration contexts
            duration_contexts = period_contexts.get(PeriodType.DURATION, [])
            
            if duration_contexts:
                # Find the context with revenue-related facts
                best_context = None
                max_revenue_facts = 0
                
                for context_id in duration_contexts:
                    context_info = context_details[context_id]
                    
                    # Count revenue-related concepts in this context
                    revenue_concept_count = sum(1 for concept in context_info.sample_concepts 
                                             if any(rev_term in concept.lower() 
                                                   for rev_term in ['revenue', 'sales', 'income']))
                    
                    # Prefer contexts with more revenue-related facts and more total facts
                    score = revenue_concept_count * 10 + context_info.fact_count
                    
                    if score > max_revenue_facts:
                        max_revenue_facts = score
                        best_context = context_id
                
                if best_context:
                    revenue_contexts[fiscal_year] = best_context
                    logger.debug(f"Fiscal year {fiscal_year} revenue context: {best_context}")
        
        return revenue_contexts
    
    def _identify_balance_sheet_contexts(self, fiscal_year_contexts: Dict, context_details: Dict[str, ContextInfo]) -> Dict[int, str]:
        """Identify the best context ID for balance sheet data for each fiscal year"""
        balance_sheet_contexts = {}
        
        for fiscal_year, period_contexts in fiscal_year_contexts.items():
            # For balance sheet, prefer instant contexts
            instant_contexts = period_contexts.get(PeriodType.INSTANT, [])
            
            if instant_contexts:
                # Find the context with balance sheet-related facts
                best_context = None
                max_bs_facts = 0
                
                for context_id in instant_contexts:
                    context_info = context_details[context_id]
                    
                    # Count balance sheet-related concepts
                    bs_concept_count = sum(1 for concept in context_info.sample_concepts 
                                         if any(bs_term in concept.lower() 
                                               for bs_term in ['assets', 'liabilities', 'equity', 'cash', 'debt']))
                    
                    # Prefer contexts with more balance sheet facts and more total facts
                    score = bs_concept_count * 10 + context_info.fact_count
                    
                    if score > max_bs_facts:
                        max_bs_facts = score
                        best_context = context_id
                
                if best_context:
                    balance_sheet_contexts[fiscal_year] = best_context
                    logger.debug(f"Fiscal year {fiscal_year} balance sheet context: {best_context}")
        
        return balance_sheet_contexts
    
    def get_revenue_context_for_year(self, fiscal_year: int) -> Optional[str]:
        """Get the preferred context ID for revenue data for a specific fiscal year"""
        return self.context_mapping.revenue_contexts.get(fiscal_year)
    
    def get_balance_sheet_context_for_year(self, fiscal_year: int) -> Optional[str]:
        """Get the preferred context ID for balance sheet data for a specific fiscal year"""
        return self.context_mapping.balance_sheet_contexts.get(fiscal_year)
    
    def get_facts_by_context_id(self, context_id: str) -> List[FinancialFact]:
        """Get all facts for a specific context ID"""
        return [fact for fact in self.facts if fact.context_id == context_id]
    
    def get_revenue_for_year(self, fiscal_year: int) -> Optional[float]:
        """Get revenue for a specific fiscal year using the correct context"""
        revenue_context = self.get_revenue_context_for_year(fiscal_year)
        if not revenue_context:
            logger.warning(f"No revenue context found for fiscal year {fiscal_year}")
            return None
        
        # Get facts from the revenue context
        context_facts = self.get_facts_by_context_id(revenue_context)
        
        # Find revenue fact
        revenue_concepts = [
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'Revenues',
            'Revenue'
        ]
        
        for fact in context_facts:
            for revenue_concept in revenue_concepts:
                if revenue_concept.lower() in fact.concept.lower():
                    if isinstance(fact.value, (int, float)):
                        # Apply scaling
                        value = float(fact.value)
                        if fact.decimals is not None:
                            value *= (10 ** fact.decimals)
                        
                        logger.info(f"Found revenue for {fiscal_year}: ${value:,.0f} (context: {revenue_context})")
                        return value
        
        logger.warning(f"No revenue fact found in context {revenue_context} for fiscal year {fiscal_year}")
        return None
    
    def get_concept_value_for_year(self, concept: str, fiscal_year: int, 
                                  prefer_duration: bool = True) -> Optional[float]:
        """Get a specific concept value for a fiscal year using the appropriate context"""
        
        # Determine which context to use based on concept type
        if prefer_duration or any(term in concept.lower() for term in ['revenue', 'income', 'expense', 'cost']):
            # Use revenue context (duration)
            target_context = self.get_revenue_context_for_year(fiscal_year)
        else:
            # Use balance sheet context (instant)
            target_context = self.get_balance_sheet_context_for_year(fiscal_year)
        
        if not target_context:
            logger.warning(f"No appropriate context found for {concept} in fiscal year {fiscal_year}")
            return None
        
        # Get facts from the target context
        context_facts = self.get_facts_by_context_id(target_context)
        
        # Find the concept
        for fact in context_facts:
            if concept.lower() in fact.concept.lower() or fact.concept.lower().endswith(concept.lower()):
                if isinstance(fact.value, (int, float)):
                    # Apply scaling
                    value = float(fact.value)
                    if fact.decimals is not None:
                        value *= (10 ** fact.decimals)
                    
                    logger.debug(f"Found {concept} for {fiscal_year}: {value:,.0f} (context: {target_context})")
                    return value
        
        logger.debug(f"Concept {concept} not found in context {target_context} for fiscal year {fiscal_year}")
        return None
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the context mapping"""
        summary = {
            'total_contexts': len(self.context_mapping.context_details),
            'fiscal_years': sorted(self.context_mapping.fiscal_year_contexts.keys()),
            'revenue_contexts': self.context_mapping.revenue_contexts,
            'balance_sheet_contexts': self.context_mapping.balance_sheet_contexts,
            'context_details': {}
        }
        
        # Add details for key contexts
        for fiscal_year in summary['fiscal_years']:
            year_info = {
                'revenue_context': self.context_mapping.revenue_contexts.get(fiscal_year),
                'balance_sheet_context': self.context_mapping.balance_sheet_contexts.get(fiscal_year)
            }
            
            # Add context details
            if year_info['revenue_context']:
                rev_context = self.context_mapping.context_details[year_info['revenue_context']]
                year_info['revenue_context_info'] = {
                    'period_type': rev_context.period_type.value,
                    'period_start': rev_context.period_start.isoformat() if rev_context.period_start else None,
                    'period_end': rev_context.period_end.isoformat() if rev_context.period_end else None,
                    'fact_count': rev_context.fact_count
                }
            
            if year_info['balance_sheet_context']:
                bs_context = self.context_mapping.context_details[year_info['balance_sheet_context']]
                year_info['balance_sheet_context_info'] = {
                    'period_type': bs_context.period_type.value,
                    'period_start': bs_context.period_start.isoformat() if bs_context.period_start else None,
                    'period_end': bs_context.period_end.isoformat() if bs_context.period_end else None,
                    'fact_count': bs_context.fact_count
                }
            
            summary['context_details'][fiscal_year] = year_info
        
        return summary
    
    def print_context_analysis(self):
        """Print a detailed analysis of contexts"""
        print("📋 XBRL Context Analysis")
        print("=" * 50)
        
        summary = self.get_context_summary()
        
        print(f"Total Contexts: {summary['total_contexts']}")
        print(f"Fiscal Years: {summary['fiscal_years']}")
        
        for fiscal_year in summary['fiscal_years']:
            print(f"\n📅 Fiscal Year {fiscal_year}:")
            year_info = summary['context_details'][fiscal_year]
            
            if year_info['revenue_context']:
                rev_info = year_info['revenue_context_info']
                print(f"   💰 Revenue Context: {year_info['revenue_context']}")
                print(f"      Period: {rev_info['period_start']} to {rev_info['period_end']}")
                print(f"      Type: {rev_info['period_type']}")
                print(f"      Facts: {rev_info['fact_count']}")
            
            if year_info['balance_sheet_context']:
                bs_info = year_info['balance_sheet_context_info']
                print(f"   📊 Balance Sheet Context: {year_info['balance_sheet_context']}")
                print(f"      Date: {bs_info['period_end']}")
                print(f"      Type: {bs_info['period_type']}")
                print(f"      Facts: {bs_info['fact_count']}")