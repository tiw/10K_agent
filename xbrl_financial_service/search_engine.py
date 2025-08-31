"""
Search and discovery engine for financial data
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import math

from .models import FinancialFact, StatementType, CompanyInfo
from .database.operations import DatabaseManager
from .query_engine import QueryEngine, FinancialQuery
from .utils.logging import get_logger
from .utils.exceptions import QueryError

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """
    Individual search result with relevance scoring
    """
    fact: FinancialFact
    relevance_score: float
    match_type: str                    # 'exact', 'fuzzy', 'partial', 'semantic'
    matched_fields: List[str]          # Fields that matched the query
    highlights: Dict[str, str] = field(default_factory=dict)  # Highlighted text


@dataclass
class SearchResponse:
    """
    Complete search response with results and metadata
    """
    results: List[SearchResult] = field(default_factory=list)
    total_count: int = 0
    query_time_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class ConceptSuggestion:
    """
    Concept suggestion with metadata
    """
    concept: str
    label: str
    frequency: int
    statement_types: List[str]
    similarity_score: float = 0.0


class SearchEngine:
    """
    Advanced search and discovery engine for financial data
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, query_engine: Optional[QueryEngine] = None):
        self.db_manager = db_manager or DatabaseManager()
        self.query_engine = query_engine or QueryEngine(self.db_manager)
        
        # Search configuration
        self.min_fuzzy_similarity = 0.6
        self.max_suggestions = 10
        self.max_search_results = 100
        
        # Cached data for performance
        self._concept_cache: Dict[str, ConceptSuggestion] = {}
        self._label_index: Dict[str, List[str]] = defaultdict(list)
        self._concept_frequency: Counter = Counter()
        
        # Initialize search indexes
        self._build_search_indexes()
    
    def search(
        self, 
        query: str, 
        limit: int = 50,
        include_fuzzy: bool = True,
        include_suggestions: bool = True,
        statement_type: Optional[StatementType] = None,
        cik: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform comprehensive search across financial data
        
        Args:
            query: Search query string
            limit: Maximum results to return
            include_fuzzy: Whether to include fuzzy matching
            include_suggestions: Whether to include search suggestions
            statement_type: Optional statement type filter
            cik: Optional company filter
            
        Returns:
            SearchResponse with results and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Normalize query
            normalized_query = self._normalize_query(query)
            
            # Perform different types of searches
            exact_results = self._exact_search(normalized_query, statement_type, cik)
            partial_results = self._partial_search(normalized_query, statement_type, cik)
            
            fuzzy_results = []
            if include_fuzzy:
                fuzzy_results = self._fuzzy_search(normalized_query, statement_type, cik)
            
            # Combine and rank results
            all_results = self._combine_and_rank_results(
                exact_results, partial_results, fuzzy_results
            )
            
            # Apply limit
            limited_results = all_results[:limit]
            
            # Generate suggestions
            suggestions = []
            if include_suggestions:
                suggestions = self._generate_suggestions(normalized_query)
            
            # Generate facets
            facets = self._generate_facets(all_results)
            
            query_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                results=limited_results,
                total_count=len(all_results),
                query_time_ms=query_time,
                suggestions=suggestions,
                facets=facets
            )
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise QueryError(f"Search failed: {str(e)}")
    
    def suggest_concepts(self, partial_query: str, limit: int = 10) -> List[ConceptSuggestion]:
        """
        Get concept suggestions based on partial input
        
        Args:
            partial_query: Partial concept name or label
            limit: Maximum suggestions to return
            
        Returns:
            List of ConceptSuggestion objects
        """
        try:
            normalized_query = self._normalize_query(partial_query)
            suggestions = []
            
            # Search in cached concepts
            for concept, suggestion in self._concept_cache.items():
                # Calculate similarity
                concept_similarity = self._calculate_similarity(normalized_query, concept.lower())
                label_similarity = self._calculate_similarity(normalized_query, suggestion.label.lower())
                
                max_similarity = max(concept_similarity, label_similarity)
                
                if max_similarity >= self.min_fuzzy_similarity:
                    suggestion.similarity_score = max_similarity
                    suggestions.append(suggestion)
            
            # Sort by similarity and frequency
            suggestions.sort(key=lambda x: (x.similarity_score, x.frequency), reverse=True)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Concept suggestion failed: {str(e)}")
            return []
    
    def find_related_concepts(self, concept: str, limit: int = 10) -> List[ConceptSuggestion]:
        """
        Find concepts related to the given concept
        
        Args:
            concept: Base concept to find relations for
            limit: Maximum related concepts to return
            
        Returns:
            List of related ConceptSuggestion objects
        """
        try:
            # Get the base concept info
            base_concept = self._concept_cache.get(concept)
            if not base_concept:
                return []
            
            related_concepts = []
            base_words = set(self._extract_keywords(base_concept.label.lower()))
            
            for other_concept, suggestion in self._concept_cache.items():
                if other_concept == concept:
                    continue
                
                # Calculate semantic similarity based on shared keywords
                other_words = set(self._extract_keywords(suggestion.label.lower()))
                shared_words = base_words.intersection(other_words)
                
                if shared_words:
                    similarity = len(shared_words) / len(base_words.union(other_words))
                    if similarity > 0.2:  # Minimum similarity threshold
                        suggestion.similarity_score = similarity
                        related_concepts.append(suggestion)
            
            # Sort by similarity
            related_concepts.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return related_concepts[:limit]
            
        except Exception as e:
            logger.error(f"Related concept search failed: {str(e)}")
            return []
    
    def search_by_category(self, category: str, limit: int = 50) -> List[ConceptSuggestion]:
        """
        Search for concepts by financial category
        
        Args:
            category: Financial category (e.g., 'revenue', 'assets', 'liabilities')
            limit: Maximum results to return
            
        Returns:
            List of ConceptSuggestion objects
        """
        # Define category keywords
        category_keywords = {
            'revenue': ['revenue', 'sales', 'income', 'earnings'],
            'expenses': ['expense', 'cost', 'expenditure', 'charges'],
            'assets': ['assets', 'property', 'equipment', 'inventory', 'cash'],
            'liabilities': ['liabilities', 'debt', 'payable', 'obligations'],
            'equity': ['equity', 'capital', 'retained', 'stockholders'],
            'cash_flow': ['cash', 'flow', 'operating', 'investing', 'financing']
        }
        
        keywords = category_keywords.get(category.lower(), [category.lower()])
        
        matching_concepts = []
        for concept, suggestion in self._concept_cache.items():
            label_lower = suggestion.label.lower()
            concept_lower = concept.lower()
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword in label_lower or keyword in concept_lower:
                    matching_concepts.append(suggestion)
                    break
        
        # Sort by frequency
        matching_concepts.sort(key=lambda x: x.frequency, reverse=True)
        
        return matching_concepts[:limit]
    
    def get_search_facets(self, query: Optional[str] = None) -> Dict[str, Dict[str, int]]:
        """
        Get search facets for filtering
        
        Args:
            query: Optional query to filter facets
            
        Returns:
            Dictionary of facet categories and counts
        """
        try:
            # Get a sample of facts for facet generation
            facts = self.db_manager.search_facts(
                concept_pattern=query if query else None,
                limit=1000
            )
            
            return self._generate_facets([
                SearchResult(fact=fact, relevance_score=1.0, match_type='sample', matched_fields=[])
                for fact in facts
            ])
            
        except Exception as e:
            logger.error(f"Facet generation failed: {str(e)}")
            return {}
    
    def _build_search_indexes(self):
        """Build search indexes for performance"""
        try:
            # Get all unique concepts and labels
            facts = self.db_manager.search_facts(limit=10000)  # Large sample
            
            concept_info = defaultdict(lambda: {
                'labels': set(),
                'statement_types': set(),
                'frequency': 0
            })
            
            for fact in facts:
                concept_info[fact.concept]['labels'].add(fact.label)
                concept_info[fact.concept]['frequency'] += 1
                
                # Try to infer statement type from concept
                statement_type = self._infer_statement_type(fact.concept, fact.label)
                if statement_type:
                    concept_info[fact.concept]['statement_types'].add(statement_type)
            
            # Build concept cache
            for concept, info in concept_info.items():
                # Use the most common label
                primary_label = max(info['labels'], key=len) if info['labels'] else concept
                
                self._concept_cache[concept] = ConceptSuggestion(
                    concept=concept,
                    label=primary_label,
                    frequency=info['frequency'],
                    statement_types=list(info['statement_types'])
                )
                
                # Build label index
                words = self._extract_keywords(primary_label.lower())
                for word in words:
                    self._label_index[word].append(concept)
            
            # Update frequency counter
            self._concept_frequency.update({
                concept: info['frequency'] 
                for concept, info in concept_info.items()
            })
            
            logger.info(f"Built search indexes with {len(self._concept_cache)} concepts")
            
        except Exception as e:
            logger.error(f"Failed to build search indexes: {str(e)}")
    
    def _exact_search(self, query: str, statement_type: Optional[StatementType], cik: Optional[str]) -> List[SearchResult]:
        """Perform exact match search"""
        results = []
        
        # Search by exact concept match
        concept_facts = self.db_manager.search_facts(
            concept_pattern=query,
            statement_type=statement_type,
            cik=cik,
            limit=50
        )
        
        for fact in concept_facts:
            if query.lower() in fact.concept.lower():
                results.append(SearchResult(
                    fact=fact,
                    relevance_score=1.0,
                    match_type='exact',
                    matched_fields=['concept']
                ))
        
        # Search by exact label match
        label_facts = self.db_manager.search_facts(
            label_pattern=query,
            statement_type=statement_type,
            cik=cik,
            limit=50
        )
        
        for fact in label_facts:
            if query.lower() in fact.label.lower():
                results.append(SearchResult(
                    fact=fact,
                    relevance_score=0.9,
                    match_type='exact',
                    matched_fields=['label']
                ))
        
        return results
    
    def _partial_search(self, query: str, statement_type: Optional[StatementType], cik: Optional[str]) -> List[SearchResult]:
        """Perform partial match search"""
        results = []
        query_words = self._extract_keywords(query)
        
        # Search using query words
        for word in query_words:
            if len(word) >= 3:  # Skip very short words
                word_facts = self.db_manager.search_facts(
                    label_pattern=word,
                    statement_type=statement_type,
                    cik=cik,
                    limit=30
                )
                
                for fact in word_facts:
                    # Calculate relevance based on word matches
                    fact_words = set(self._extract_keywords(fact.label.lower()))
                    query_word_set = set(query_words)
                    
                    matches = fact_words.intersection(query_word_set)
                    relevance = len(matches) / len(query_word_set) if query_word_set else 0
                    
                    if relevance > 0.3:  # Minimum relevance threshold
                        results.append(SearchResult(
                            fact=fact,
                            relevance_score=relevance * 0.8,  # Lower than exact match
                            match_type='partial',
                            matched_fields=['label']
                        ))
        
        return results
    
    def _fuzzy_search(self, query: str, statement_type: Optional[StatementType], cik: Optional[str]) -> List[SearchResult]:
        """Perform fuzzy match search"""
        results = []
        
        # Search through cached concepts for fuzzy matches
        for concept, suggestion in self._concept_cache.items():
            concept_similarity = self._calculate_similarity(query, concept.lower())
            label_similarity = self._calculate_similarity(query, suggestion.label.lower())
            
            max_similarity = max(concept_similarity, label_similarity)
            
            if max_similarity >= self.min_fuzzy_similarity:
                # Get facts for this concept
                concept_facts = self.db_manager.search_facts(
                    concept_pattern=concept.split(':')[-1],  # Remove namespace
                    statement_type=statement_type,
                    cik=cik,
                    limit=5
                )
                
                for fact in concept_facts:
                    results.append(SearchResult(
                        fact=fact,
                        relevance_score=max_similarity * 0.7,  # Lower than partial match
                        match_type='fuzzy',
                        matched_fields=['concept' if concept_similarity > label_similarity else 'label']
                    ))
        
        return results
    
    def _combine_and_rank_results(self, *result_lists: List[SearchResult]) -> List[SearchResult]:
        """Combine and rank search results"""
        # Combine all results
        all_results = []
        seen_facts = set()
        
        for result_list in result_lists:
            for result in result_list:
                # Create unique key for deduplication
                fact_key = (result.fact.concept, result.fact.period, result.fact.context_id)
                
                if fact_key not in seen_facts:
                    seen_facts.add(fact_key)
                    all_results.append(result)
                else:
                    # Update existing result with higher relevance score
                    for existing_result in all_results:
                        existing_key = (existing_result.fact.concept, existing_result.fact.period, existing_result.fact.context_id)
                        if existing_key == fact_key and result.relevance_score > existing_result.relevance_score:
                            existing_result.relevance_score = result.relevance_score
                            existing_result.match_type = result.match_type
                            break
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return all_results
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions"""
        suggestions = []
        query_words = self._extract_keywords(query)
        
        # Find concepts with similar words
        word_concepts = defaultdict(int)
        
        for word in query_words:
            if word in self._label_index:
                for concept in self._label_index[word]:
                    word_concepts[concept] += 1
        
        # Get top concepts and extract meaningful suggestions
        top_concepts = sorted(word_concepts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        for concept, _ in top_concepts:
            if concept in self._concept_cache:
                suggestion = self._concept_cache[concept]
                # Extract meaningful phrases from labels
                label_words = self._extract_keywords(suggestion.label)
                if len(label_words) > 1:
                    suggestions.append(suggestion.label)
        
        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:self.max_suggestions]
    
    def _generate_facets(self, results: List[SearchResult]) -> Dict[str, Dict[str, int]]:
        """Generate facets from search results"""
        facets = {
            'statement_types': defaultdict(int),
            'units': defaultdict(int),
            'period_types': defaultdict(int),
            'concepts': defaultdict(int)
        }
        
        for result in results:
            fact = result.fact
            
            # Statement type facet (inferred)
            statement_type = self._infer_statement_type(fact.concept, fact.label)
            if statement_type:
                facets['statement_types'][statement_type] += 1
            
            # Unit facet
            if fact.unit:
                facets['units'][fact.unit] += 1
            
            # Period type facet
            facets['period_types'][fact.period_type.value] += 1
            
            # Concept facet (top-level concept)
            concept_parts = fact.concept.split(':')
            if len(concept_parts) > 1:
                top_concept = concept_parts[-1].split('_')[0]  # First word of concept
                facets['concepts'][top_concept] += 1
        
        # Convert to regular dicts and limit entries
        return {
            category: dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])
            for category, counts in facets.items()
        }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize search query"""
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query.lower().strip())
        
        # Remove special characters but keep alphanumeric and spaces
        normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
        
        return normalized
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'a', 'an'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) >= 3 and word not in stop_words]
        
        return keywords
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _infer_statement_type(self, concept: str, label: str) -> Optional[str]:
        """Infer statement type from concept and label"""
        concept_lower = concept.lower()
        label_lower = label.lower()
        
        # Income statement indicators
        if any(keyword in concept_lower or keyword in label_lower for keyword in 
               ['revenue', 'income', 'expense', 'cost', 'profit', 'loss', 'earnings']):
            return 'income_statement'
        
        # Balance sheet indicators
        if any(keyword in concept_lower or keyword in label_lower for keyword in 
               ['assets', 'liabilities', 'equity', 'capital', 'retained', 'stockholders']):
            return 'balance_sheet'
        
        # Cash flow indicators
        if any(keyword in concept_lower or keyword in label_lower for keyword in 
               ['cash', 'flow', 'operating', 'investing', 'financing']):
            return 'cash_flow_statement'
        
        return None


class SuggestionEngine:
    """
    Specialized engine for generating intelligent suggestions
    """
    
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine
    
    def suggest_next_queries(self, current_query: str, search_results: List[SearchResult]) -> List[str]:
        """
        Suggest follow-up queries based on current search
        
        Args:
            current_query: Current search query
            search_results: Current search results
            
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        if not search_results:
            return suggestions
        
        # Analyze result patterns
        common_concepts = Counter()
        common_labels = Counter()
        
        for result in search_results[:10]:  # Analyze top results
            # Extract concept keywords
            concept_words = self.search_engine._extract_keywords(result.fact.concept)
            for word in concept_words:
                common_concepts[word] += 1
            
            # Extract label keywords
            label_words = self.search_engine._extract_keywords(result.fact.label)
            for word in label_words:
                common_labels[word] += 1
        
        # Generate suggestions based on common terms
        for word, count in common_concepts.most_common(5):
            if word.lower() not in current_query.lower():
                suggestions.append(f"{current_query} {word}")
        
        for word, count in common_labels.most_common(3):
            if word.lower() not in current_query.lower() and len(word) > 4:
                suggestions.append(word)
        
        return suggestions[:5]
    
    def suggest_refinements(self, query: str, result_count: int) -> List[str]:
        """
        Suggest query refinements based on result count
        
        Args:
            query: Original query
            result_count: Number of results returned
            
        Returns:
            List of refinement suggestions
        """
        suggestions = []
        
        if result_count == 0:
            # Too restrictive - suggest broader terms
            suggestions.extend([
                f"Try broader terms related to '{query}'",
                "Check spelling and try synonyms",
                "Use fewer specific terms"
            ])
        elif result_count > 100:
            # Too broad - suggest narrowing
            suggestions.extend([
                f"Add more specific terms to '{query}'",
                "Filter by statement type or time period",
                "Use exact phrase matching"
            ])
        
        return suggestions