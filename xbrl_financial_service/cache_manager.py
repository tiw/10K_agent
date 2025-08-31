"""
Caching and performance optimization for financial data service
"""

import json
import pickle
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
from threading import Lock, RLock
from functools import wraps
import weakref

from .models import FinancialFact, FilingData, FinancialStatement
from .config import Config
from .utils.logging import get_logger
from .utils.exceptions import CacheError

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """
    Individual cache entry with metadata
    """
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl_seconds is None:
            return False
        
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds
    
    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """
    Cache performance statistics
    """
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'total_size_bytes': self.total_size_bytes,
            'entry_count': self.entry_count,
            'hit_rate': self.hit_rate
        }


class LRUCache(Generic[T]):
    """
    Thread-safe LRU (Least Recently Used) cache implementation
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._stats = CacheStats()
    
    def get(self, key: str) -> Optional[T]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired():
                self._remove_entry(key)
                self._stats.misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats.hits += 1
            
            return entry.value
    
    def put(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Put value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (overrides default)
        """
        with self._lock:
            now = datetime.now()
            ttl_to_use = ttl if ttl is not None else self.default_ttl
            
            # Calculate size
            size_bytes = self._calculate_size(value)
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                ttl_seconds=ttl_to_use,
                size_bytes=size_bytes
            )
            
            # Add to cache
            self._cache[key] = entry
            self._stats.entry_count += 1
            self._stats.total_size_bytes += size_bytes
            
            # Evict if necessary
            self._evict_if_necessary()
    
    def remove(self, key: str) -> bool:
        """
        Remove entry from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was removed, False if not found
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                total_size_bytes=self._stats.total_size_bytes,
                entry_count=self._stats.entry_count
            )
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
            
            return len(expired_keys)
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry and update stats"""
        entry = self._cache.pop(key, None)
        if entry:
            self._stats.entry_count -= 1
            self._stats.total_size_bytes -= entry.size_bytes
    
    def _evict_if_necessary(self) -> None:
        """Evict least recently used entries if cache is full"""
        while len(self._cache) > self.max_size:
            # Remove least recently used (first item)
            oldest_key = next(iter(self._cache))
            self._remove_entry(oldest_key)
            self._stats.evictions += 1
    
    def _calculate_size(self, value: Any) -> int:
        """Estimate size of cached value in bytes"""
        try:
            # Use pickle to estimate size
            return len(pickle.dumps(value))
        except Exception:
            # Fallback to string representation
            return len(str(value).encode('utf-8'))


class QueryCache:
    """
    Specialized cache for query results
    """
    
    def __init__(self, max_size: int = 500, default_ttl: int = 3600):
        self._cache = LRUCache[Any](max_size=max_size, default_ttl=default_ttl)
        self._lock = Lock()
    
    def get_query_result(self, query_hash: str) -> Optional[Any]:
        """Get cached query result"""
        return self._cache.get(query_hash)
    
    def cache_query_result(self, query_hash: str, result: Any, ttl: Optional[int] = None) -> None:
        """Cache query result"""
        self._cache.put(query_hash, result, ttl)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Pattern to match against keys
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = []
            
            for key in self._cache._cache.keys():
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._cache.remove(key)
            
            return len(keys_to_remove)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self._cache.get_stats()


class FactCache:
    """
    Specialized cache for financial facts
    """
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 7200):
        self._cache = LRUCache[List[FinancialFact]](max_size=max_size, default_ttl=default_ttl)
        self._concept_index: Dict[str, List[str]] = {}
        self._lock = Lock()
    
    def get_facts_by_concept(self, concept: str) -> Optional[List[FinancialFact]]:
        """Get cached facts by concept"""
        return self._cache.get(f"concept:{concept}")
    
    def cache_facts_by_concept(self, concept: str, facts: List[FinancialFact], ttl: Optional[int] = None) -> None:
        """Cache facts by concept"""
        key = f"concept:{concept}"
        self._cache.put(key, facts, ttl)
        
        # Update concept index
        with self._lock:
            if concept not in self._concept_index:
                self._concept_index[concept] = []
            self._concept_index[concept].append(key)
    
    def get_facts_by_period(self, period: str) -> Optional[List[FinancialFact]]:
        """Get cached facts by period"""
        return self._cache.get(f"period:{period}")
    
    def cache_facts_by_period(self, period: str, facts: List[FinancialFact], ttl: Optional[int] = None) -> None:
        """Cache facts by period"""
        self._cache.put(f"period:{period}", facts, ttl)
    
    def invalidate_concept(self, concept: str) -> int:
        """Invalidate all cache entries for a concept"""
        with self._lock:
            keys_to_remove = self._concept_index.get(concept, [])
            
            for key in keys_to_remove:
                self._cache.remove(key)
            
            if concept in self._concept_index:
                del self._concept_index[concept]
            
            return len(keys_to_remove)


class CacheManager:
    """
    Main cache manager coordinating different cache types
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Initialize different cache types
        self.query_cache = QueryCache(
            max_size=getattr(config, 'query_cache_size', 500),
            default_ttl=getattr(config, 'query_cache_ttl', 3600)
        )
        
        self.fact_cache = FactCache(
            max_size=getattr(config, 'fact_cache_size', 10000),
            default_ttl=getattr(config, 'fact_cache_ttl', 7200)
        )
        
        self.statement_cache = LRUCache[FinancialStatement](
            max_size=getattr(config, 'statement_cache_size', 100),
            default_ttl=getattr(config, 'statement_cache_ttl', 3600)
        )
        
        self.filing_cache = LRUCache[FilingData](
            max_size=getattr(config, 'filing_cache_size', 50),
            default_ttl=getattr(config, 'filing_cache_ttl', 7200)
        )
        
        # Cleanup timer
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=30)
    
    def get_query_result(self, query_key: str) -> Optional[Any]:
        """Get cached query result"""
        self._maybe_cleanup()
        return self.query_cache.get_query_result(query_key)
    
    def cache_query_result(self, query_key: str, result: Any, ttl: Optional[int] = None) -> None:
        """Cache query result"""
        self.query_cache.cache_query_result(query_key, result, ttl)
    
    def get_facts(self, cache_key: str) -> Optional[List[FinancialFact]]:
        """Get cached facts"""
        self._maybe_cleanup()
        
        if cache_key.startswith('concept:'):
            concept = cache_key[8:]  # Remove 'concept:' prefix
            return self.fact_cache.get_facts_by_concept(concept)
        elif cache_key.startswith('period:'):
            period = cache_key[7:]  # Remove 'period:' prefix
            return self.fact_cache.get_facts_by_period(period)
        
        return None
    
    def cache_facts(self, cache_key: str, facts: List[FinancialFact], ttl: Optional[int] = None) -> None:
        """Cache facts"""
        if cache_key.startswith('concept:'):
            concept = cache_key[8:]
            self.fact_cache.cache_facts_by_concept(concept, facts, ttl)
        elif cache_key.startswith('period:'):
            period = cache_key[7:]
            self.fact_cache.cache_facts_by_period(period, facts, ttl)
    
    def get_statement(self, statement_key: str) -> Optional[FinancialStatement]:
        """Get cached financial statement"""
        self._maybe_cleanup()
        return self.statement_cache.get(statement_key)
    
    def cache_statement(self, statement_key: str, statement: FinancialStatement, ttl: Optional[int] = None) -> None:
        """Cache financial statement"""
        self.statement_cache.put(statement_key, statement, ttl)
    
    def get_filing(self, filing_key: str) -> Optional[FilingData]:
        """Get cached filing data"""
        self._maybe_cleanup()
        return self.filing_cache.get(filing_key)
    
    def cache_filing(self, filing_key: str, filing: FilingData, ttl: Optional[int] = None) -> None:
        """Cache filing data"""
        self.filing_cache.put(filing_key, filing, ttl)
    
    def invalidate_company_data(self, cik: str) -> int:
        """Invalidate all cached data for a company"""
        total_invalidated = 0
        
        # Invalidate query cache entries containing the CIK
        total_invalidated += self.query_cache.invalidate_pattern(cik)
        
        # Invalidate filing cache
        filing_keys_to_remove = []
        for key in self.filing_cache._cache.keys():
            if cik in key:
                filing_keys_to_remove.append(key)
        
        for key in filing_keys_to_remove:
            self.filing_cache.remove(key)
            total_invalidated += 1
        
        # Invalidate statement cache
        statement_keys_to_remove = []
        for key in self.statement_cache._cache.keys():
            if cik in key:
                statement_keys_to_remove.append(key)
        
        for key in statement_keys_to_remove:
            self.statement_cache.remove(key)
            total_invalidated += 1
        
        logger.info(f"Invalidated {total_invalidated} cache entries for company {cik}")
        return total_invalidated
    
    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive cache statistics"""
        return {
            'query_cache': self.query_cache.get_stats().to_dict(),
            'fact_cache': self.fact_cache._cache.get_stats().to_dict(),
            'statement_cache': self.statement_cache.get_stats().to_dict(),
            'filing_cache': self.filing_cache.get_stats().to_dict()
        }
    
    def clear_all_caches(self) -> None:
        """Clear all caches"""
        self.query_cache._cache.clear()
        self.fact_cache._cache.clear()
        self.statement_cache.clear()
        self.filing_cache.clear()
        logger.info("All caches cleared")
    
    def _maybe_cleanup(self) -> None:
        """Perform cleanup if interval has passed"""
        now = datetime.now()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired_entries()
            self._last_cleanup = now
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired entries from all caches"""
        total_cleaned = 0
        
        total_cleaned += self.query_cache._cache.cleanup_expired()
        total_cleaned += self.fact_cache._cache.cleanup_expired()
        total_cleaned += self.statement_cache.cleanup_expired()
        total_cleaned += self.filing_cache.cleanup_expired()
        
        if total_cleaned > 0:
            logger.info(f"Cleaned up {total_cleaned} expired cache entries")


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        SHA-256 hash of the arguments
    """
    # Create a string representation of all arguments
    key_parts = []
    
    for arg in args:
        if hasattr(arg, '__dict__'):
            # For objects, use their dict representation
            key_parts.append(str(sorted(arg.__dict__.items())))
        else:
            key_parts.append(str(arg))
    
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")
    
    key_string = '|'.join(key_parts)
    
    # Generate SHA-256 hash
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


def cached(cache_manager: CacheManager, ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        cache_manager: CacheManager instance
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            func_key = f"{key_prefix}{func.__name__}"
            cache_key_str = cache_key(func_key, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get_query_result(cache_key_str)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.cache_query_result(cache_key_str, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class LazyLoader:
    """
    Lazy loading utility for large datasets
    """
    
    def __init__(self, loader_func: Callable[[], T], cache_manager: Optional[CacheManager] = None):
        self.loader_func = loader_func
        self.cache_manager = cache_manager
        self._loaded = False
        self._data: Optional[T] = None
        self._lock = Lock()
    
    def get(self) -> T:
        """Get the data, loading if necessary"""
        if not self._loaded:
            with self._lock:
                if not self._loaded:  # Double-check locking
                    self._data = self.loader_func()
                    self._loaded = True
        
        return self._data
    
    def reset(self) -> None:
        """Reset the lazy loader"""
        with self._lock:
            self._loaded = False
            self._data = None


class BatchLoader:
    """
    Batch loading utility for efficient data retrieval
    """
    
    def __init__(self, batch_size: int = 100, cache_manager: Optional[CacheManager] = None):
        self.batch_size = batch_size
        self.cache_manager = cache_manager
        self._pending_keys: List[str] = []
        self._lock = Lock()
    
    def add_key(self, key: str) -> None:
        """Add a key to the batch"""
        with self._lock:
            self._pending_keys.append(key)
    
    def load_batch(self, loader_func: Callable[[List[str]], Dict[str, T]]) -> Dict[str, T]:
        """
        Load a batch of data
        
        Args:
            loader_func: Function that takes a list of keys and returns a dict of key->value
            
        Returns:
            Dictionary of loaded data
        """
        with self._lock:
            if not self._pending_keys:
                return {}
            
            # Process in batches
            results = {}
            
            for i in range(0, len(self._pending_keys), self.batch_size):
                batch_keys = self._pending_keys[i:i + self.batch_size]
                batch_results = loader_func(batch_keys)
                results.update(batch_results)
                
                # Cache individual results if cache manager is available
                if self.cache_manager:
                    for key, value in batch_results.items():
                        self.cache_manager.cache_query_result(key, value)
            
            # Clear pending keys
            self._pending_keys.clear()
            
            return results