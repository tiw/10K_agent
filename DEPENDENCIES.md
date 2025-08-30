# XBRL Financial Service - Dependencies

## Overview

This document outlines all dependencies required for the XBRL Financial Service.

## Python Version Requirements

- **Minimum**: Python 3.9
- **Recommended**: Python 3.11+
- **Tested**: Python 3.9, 3.10, 3.11, 3.12

## Core Dependencies (Production)

These are the minimal dependencies required to run the service:

### XML Processing
- **lxml >= 4.9.0**
  - Purpose: Parse XBRL XML files (schema, linkbases, instances)
  - Why: Fast, feature-complete XML parser with XPath support
  - License: BSD

### Date/Time Handling
- **python-dateutil >= 2.8.0**
  - Purpose: Parse and handle financial reporting periods
  - Why: Robust date parsing for various XBRL date formats
  - License: Apache 2.0

### Database ORM
- **SQLAlchemy >= 2.0.0**
  - Purpose: Database abstraction and ORM for caching parsed data
  - Why: Mature, flexible ORM with SQLite support
  - License: MIT

### Data Validation
- **pydantic >= 2.0.0**
  - Purpose: Data validation and serialization for financial models
  - Why: Type-safe data models with automatic validation
  - License: MIT

### Type Hints (Compatibility)
- **typing-extensions >= 4.0.0**
  - Purpose: Enhanced type hints for older Python versions
  - Why: Ensures compatibility across Python versions
  - License: PSF

## Optional Dependencies (Performance)

These dependencies improve performance but are not required:

### JSON Processing
- **ujson >= 5.7.0**
  - Purpose: Fast JSON serialization for MCP responses
  - Why: 2-3x faster than built-in json module
  - License: BSD

## Development Dependencies

Required only for development, testing, and code quality:

### Testing Framework
- **pytest >= 7.0.0** - Test runner
- **pytest-asyncio >= 0.21.0** - Async test support
- **pytest-cov >= 4.0.0** - Coverage reporting
- **pytest-mock >= 3.10.0** - Mocking utilities

### Code Quality
- **black >= 23.0.0** - Code formatter
- **isort >= 5.12.0** - Import sorter
- **mypy >= 1.0.0** - Static type checker
- **flake8 >= 6.0.0** - Linter
- **pre-commit >= 3.0.0** - Git hooks

### Documentation
- **sphinx >= 5.0.0** - Documentation generator
- **sphinx-rtd-theme >= 1.2.0** - Documentation theme

### Build Tools
- **setuptools >= 65.0.0** - Package building
- **wheel >= 0.38.0** - Wheel format support
- **build >= 0.10.0** - Build backend
- **twine >= 4.0.0** - Package uploading

## Installation Files

The project provides multiple requirements files for different use cases:

### requirements-prod.txt
Minimal production dependencies only. Use for:
- Production deployments
- Docker containers
- Minimal installations

### requirements-dev.txt
All dependencies including development tools. Use for:
- Local development
- CI/CD pipelines
- Contributing to the project

### requirements.txt
Comprehensive list with comments. Use for:
- Understanding all dependencies
- Reference documentation

## System Dependencies

The service requires no external system dependencies beyond Python. All functionality is provided by Python packages.

### Database
- Uses SQLite (included with Python)
- No external database server required
- PostgreSQL support can be added by installing `psycopg2`

### XML Libraries
- Uses lxml (pure Python with C extensions)
- No external XML libraries required

## Installation Methods

### 1. Automated Installer (Recommended)
```bash
python install.py
```
- Interactive installation
- Checks Python version
- Creates necessary directories
- Runs basic tests

### 2. Make Commands
```bash
make install      # Production
make install-dev  # Development
```

### 3. Manual pip Install
```bash
# Production
pip install -r requirements-prod.txt
pip install -e .

# Development  
pip install -r requirements-dev.txt
pip install -e .
```

### 4. Dependency Verification
```bash
python check_requirements.py
```
- Verifies all dependencies are installed
- Checks version compatibility
- Reports missing packages

## Dependency Management

### Version Pinning Strategy
- **Minimum versions specified**: Ensures compatibility
- **No maximum versions**: Allows updates for security/performance
- **Major version constraints**: Prevents breaking changes

### Security Updates
- Dependencies are regularly updated for security patches
- Use `pip-audit` to check for known vulnerabilities
- Monitor GitHub security advisories

### Compatibility Testing
- Tested against multiple Python versions
- CI/CD pipeline validates all dependency combinations
- Regular dependency updates with automated testing

## Troubleshooting

### Common Issues

1. **lxml installation fails**
   - Install system XML libraries: `apt-get install libxml2-dev libxslt-dev`
   - Or use conda: `conda install lxml`

2. **SQLAlchemy version conflicts**
   - Ensure SQLAlchemy >= 2.0.0
   - Some older packages may require SQLAlchemy 1.x

3. **Python version too old**
   - Upgrade to Python 3.9+
   - Use pyenv for version management

### Platform-Specific Notes

#### Windows
- All dependencies have Windows wheels available
- No additional system packages required

#### macOS
- May need Xcode command line tools for lxml
- Use Homebrew for Python installation

#### Linux
- May need development headers for lxml
- Use system package manager for Python

## License Compatibility

All dependencies use permissive licenses compatible with commercial use:
- MIT License: SQLAlchemy, pydantic
- BSD License: lxml, ujson
- Apache 2.0: python-dateutil
- PSF License: typing-extensions

No GPL or copyleft dependencies are used.