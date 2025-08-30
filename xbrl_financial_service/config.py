"""
Configuration management for XBRL Financial Service
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class Config:
    """Main configuration class for the XBRL Financial Service"""
    
    # Database configuration
    database_path: str = "financial_data.db"
    database_url: Optional[str] = None
    
    # Caching configuration
    cache_ttl: int = 3600  # 1 hour in seconds
    max_cache_size: int = 1000  # Maximum number of cached items
    
    # File processing configuration
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    parsing_timeout: int = 300  # 5 minutes
    
    # MCP server configuration
    mcp_port: int = 8000
    mcp_host: str = "localhost"
    max_concurrent_requests: int = 10
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Supported taxonomies
    supported_taxonomies: List[str] = field(default_factory=lambda: [
        "us-gaap", "dei", "srt", "country", "ecd"
    ])
    
    # Data validation settings
    strict_validation: bool = True
    allow_calculation_errors: bool = False
    
    # Performance settings
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4


def load_config() -> Config:
    """Load configuration from environment variables and config files"""
    config = Config()
    
    # Override with environment variables if present
    config.database_path = os.getenv("XBRL_DATABASE_PATH", config.database_path)
    config.database_url = os.getenv("XBRL_DATABASE_URL", config.database_url)
    
    config.cache_ttl = int(os.getenv("XBRL_CACHE_TTL", str(config.cache_ttl)))
    config.max_cache_size = int(os.getenv("XBRL_MAX_CACHE_SIZE", str(config.max_cache_size)))
    
    config.max_file_size = int(os.getenv("XBRL_MAX_FILE_SIZE", str(config.max_file_size)))
    config.parsing_timeout = int(os.getenv("XBRL_PARSING_TIMEOUT", str(config.parsing_timeout)))
    
    config.mcp_port = int(os.getenv("XBRL_MCP_PORT", str(config.mcp_port)))
    config.mcp_host = os.getenv("XBRL_MCP_HOST", config.mcp_host)
    config.max_concurrent_requests = int(os.getenv("XBRL_MAX_CONCURRENT_REQUESTS", str(config.max_concurrent_requests)))
    
    config.log_level = os.getenv("XBRL_LOG_LEVEL", config.log_level)
    config.log_file = os.getenv("XBRL_LOG_FILE", config.log_file)
    
    config.strict_validation = os.getenv("XBRL_STRICT_VALIDATION", "true").lower() == "true"
    config.allow_calculation_errors = os.getenv("XBRL_ALLOW_CALC_ERRORS", "false").lower() == "true"
    
    config.enable_parallel_processing = os.getenv("XBRL_ENABLE_PARALLEL", "true").lower() == "true"
    config.max_worker_threads = int(os.getenv("XBRL_MAX_WORKERS", str(config.max_worker_threads)))
    
    return config


def get_data_dir() -> Path:
    """Get the data directory for storing files and databases"""
    data_dir = Path(os.getenv("XBRL_DATA_DIR", "./data"))
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_cache_dir() -> Path:
    """Get the cache directory for temporary files"""
    cache_dir = Path(os.getenv("XBRL_CACHE_DIR", "./cache"))
    cache_dir.mkdir(exist_ok=True)
    return cache_dir