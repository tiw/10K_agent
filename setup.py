"""
Setup script for XBRL Financial Service
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read production requirements
requirements_path = Path(__file__).parent / "requirements-prod.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#") and not line.startswith("-r")]
else:
    # Fallback to minimal requirements
    requirements = [
        "lxml>=4.9.0",
        "python-dateutil>=2.8.0", 
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0"
    ]

setup(
    name="xbrl-financial-service",
    version="0.1.0",
    description="A comprehensive Python service for parsing XBRL financial documents and providing structured financial data through MCP protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="XBRL Financial Service Team",
    author_email="team@xbrl-service.com",
    url="https://github.com/xbrl-financial-service/xbrl-financial-service",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
        "performance": [
            "ujson>=5.7.0",
            "orjson>=3.8.0",
        ]
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="xbrl financial data parsing mcp protocol",
    entry_points={
        "console_scripts": [
            "xbrl-service=xbrl_financial_service.cli:main",
        ],
    },
)