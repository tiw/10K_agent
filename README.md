# XBRL Financial Data Service

A comprehensive Python service for parsing XBRL financial documents and providing structured financial data through Model Context Protocol (MCP).

## Features

- **XBRL Parsing**: Complete parsing of XBRL taxonomy files including schema, linkbases, and instance documents
- **Financial Data Extraction**: Extract structured financial statements (Income Statement, Balance Sheet, Cash Flow)
- **MCP Integration**: Expose financial data through standardized MCP protocol for LLM agents
- **Data Validation**: Comprehensive validation of financial calculations and data integrity
- **Performance Optimized**: Caching and optimization for handling large XBRL files
- **Extensible**: Support for multiple XBRL taxonomies and custom financial metrics
- **CLI Interface**: Command-line tools for parsing and serving financial data
- **Database Storage**: SQLite-based caching for parsed financial data

## Quick Start

### Installation

#### Quick Install (Recommended)
```bash
# Run the automated installer
python install.py
```

#### Manual Installation

**Production (minimal dependencies):**
```bash
pip install -r requirements-prod.txt
pip install -e .
```

**Development (includes testing tools):**
```bash
pip install -r requirements-dev.txt
pip install -e .
```

**Using Make (if available):**
```bash
# Production
make install

# Development
make install-dev
```

#### Verify Installation
```bash
# Check all dependencies
python check_requirements.py

# Run basic tests
python -m pytest tests/test_basic_functionality.py
```

### Basic Usage

```python
from xbrl_financial_service import XBRLParser, FinancialService

# Parse XBRL files
parser = XBRLParser()
filing_data = parser.parse_filing({
    'schema': 'aapl-20240928.xsd',
    'calculation': 'aapl-20240928_cal.xml',
    'definition': 'aapl-20240928_def.xml',
    'label': 'aapl-20240928_lab.xml',
    'presentation': 'aapl-20240928_pre.xml',
    'instance': 'aapl-20240928_htm.xml'
})

# Create financial service
service = FinancialService(filing_data)

# Get financial statements
income_statement = service.get_income_statement()
balance_sheet = service.get_balance_sheet()
cash_flow = service.get_cash_flow_statement()

# Calculate financial ratios
ratios = service.get_financial_ratios()

# Search for specific financial data
revenue_facts = service.search_facts("revenue")
```

### Command Line Interface

```bash
# Parse XBRL files from directory
xbrl-service parse-xbrl --directory ./apple-10k-files/

# Parse specific XBRL files with ratio calculation
xbrl-service parse-xbrl --instance data.xml --schema schema.xsd --ratios

# Start MCP server
xbrl-service serve-mcp --port 8000
```

### MCP Server

Start the MCP server to expose financial data tools:

```bash
# Using CLI
xbrl-service serve-mcp

# Or directly
python -m xbrl_financial_service.mcp_server
```

Available MCP tools:
- `load_xbrl_filing`: Load XBRL filing data from file paths
- `get_income_statement`: Retrieve income statement data
- `get_balance_sheet`: Retrieve balance sheet data  
- `get_cash_flow`: Retrieve cash flow statement data
- `calculate_ratios`: Calculate financial ratios
- `search_financial_data`: Search for specific financial information
- `get_company_info`: Get basic company information
- `get_summary`: Get summary of loaded financial data

## Project Structure

```
xbrl_financial_service/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── models.py                # Data models
├── xbrl_parser.py          # XBRL parsing engine
├── financial_service.py    # Main financial service
├── query_engine.py         # Query and filtering engine
├── calculation_engine.py   # Financial calculations
├── mcp_server.py           # MCP server implementation
├── database/               # Database layer
│   ├── __init__.py
│   ├── models.py          # Database models
│   └── operations.py      # Database operations
└── utils/                  # Utility modules
    ├── __init__.py
    ├── logging.py         # Logging utilities
    └── exceptions.py      # Custom exceptions
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xbrl_financial_service

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m performance
```

### Code Quality

```bash
# Format code
black xbrl_financial_service/
isort xbrl_financial_service/

# Type checking
mypy xbrl_financial_service/

# Linting
flake8 xbrl_financial_service/
```

## Configuration

The service can be configured through environment variables:

```bash
# Database configuration
export XBRL_DATABASE_PATH="./data/financial_data.db"
export XBRL_CACHE_TTL=3600

# MCP server configuration  
export XBRL_MCP_PORT=8000
export XBRL_MCP_HOST="localhost"

# Performance settings
export XBRL_MAX_FILE_SIZE=104857600  # 100MB
export XBRL_ENABLE_PARALLEL=true
export XBRL_MAX_WORKERS=4

# Logging
export XBRL_LOG_LEVEL="INFO"
export XBRL_LOG_FILE="./logs/xbrl_service.log"
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## Support

For questions and support, please open an issue on GitHub.
## Dem
o

Run the comprehensive demo to see all features:

```bash
python demo.py
```

This will demonstrate:
- XBRL file parsing
- Financial statement extraction
- Ratio calculations
- MCP server capabilities
- CLI usage examples

## Working with Apple's 10-K Files

To test with Apple's actual XBRL files:

1. Download Apple's latest 10-K filing from [SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch.html)
2. Search for "Apple Inc" and download the XBRL files
3. Place the files in your working directory:
   - `aapl-YYYYMMDD.xsd` (schema)
   - `aapl-YYYYMMDD_cal.xml` (calculation linkbase)
   - `aapl-YYYYMMDD_def.xml` (definition linkbase)
   - `aapl-YYYYMMDD_lab.xml` (label linkbase)
   - `aapl-YYYYMMDD_pre.xml` (presentation linkbase)
   - `aapl-YYYYMMDD_htm.xml` (instance document)

4. Run the parser:
```bash
xbrl-service parse-xbrl --directory . --ratios
```

## API Reference

### XBRLParser

Main parser for XBRL documents:

```python
parser = XBRLParser(config=None)

# Parse from file paths
filing_data = parser.parse_filing(file_paths)

# Parse from directory (auto-detect files)
filing_data = parser.parse_filing_from_directory("./xbrl-files/")
```

### FinancialService

High-level financial data interface:

```python
service = FinancialService(filing_data, config=None)

# Get financial statements
income_stmt = service.get_income_statement()
balance_sheet = service.get_balance_sheet()
cash_flow = service.get_cash_flow_statement()

# Calculate ratios
ratios = service.get_financial_ratios()

# Search facts
facts = service.search_facts("revenue", limit=10)

# Get company info
company = service.get_company_info()
```

### Data Models

Key data structures:

- `FilingData`: Complete XBRL filing information
- `FinancialStatement`: Individual financial statement
- `FinancialFact`: Single financial data point
- `FinancialRatios`: Calculated financial ratios
- `CompanyInfo`: Basic company information

## Architecture

The service is built with a layered architecture:

```
┌─────────────────┐
│   MCP Server    │  ← Exposes tools via MCP protocol
├─────────────────┤
│ Financial Service│  ← High-level financial operations
├─────────────────┤
│  Query Engine   │  ← Data filtering and search
├─────────────────┤
│  XBRL Parser    │  ← Parses XBRL files
├─────────────────┤
│ Database Layer  │  ← SQLite storage and caching
└─────────────────┘
```

## Supported XBRL Elements

The parser supports standard US-GAAP taxonomy elements including:

- **Financial Statements**: Income Statement, Balance Sheet, Cash Flow, Shareholders' Equity
- **Financial Concepts**: Revenue, Assets, Liabilities, Equity, Expenses
- **Calculation Relationships**: Automatic validation of financial calculations
- **Presentation Hierarchy**: Proper ordering and grouping of financial line items
- **Dimensional Data**: Segment and other dimensional breakdowns

## Performance

- **Parallel Processing**: Multi-threaded parsing of linkbase files
- **Database Caching**: SQLite-based storage for parsed data
- **Memory Optimization**: Efficient handling of large XBRL files
- **Configurable Limits**: File size and processing time limits

## Error Handling

Comprehensive error handling with specific exception types:

- `XBRLParsingError`: XBRL file parsing issues
- `DataValidationError`: Data integrity problems
- `CalculationError`: Financial calculation inconsistencies
- `QueryError`: Data query failures
- `MCPError`: MCP protocol errors

## Logging

Configurable logging with multiple levels:

```python
from xbrl_financial_service.utils.logging import setup_logging

setup_logging(level="INFO", log_file="xbrl_service.log")
```