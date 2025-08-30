#!/usr/bin/env python3
"""
Check if all required dependencies are installed and compatible
"""

import sys
import importlib
import subprocess
from typing import List, Tuple, Optional


def check_python_version() -> bool:
    """Check Python version compatibility"""
    version = sys.version_info
    min_version = (3, 9)
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if (version.major, version.minor) >= min_version:
        print("✅ Python version is compatible")
        return True
    else:
        print(f"⚠️  Python {min_version[0]}.{min_version[1]}+ recommended (current: {version.major}.{version.minor})")
        return False


def check_package(package_name: str, import_name: Optional[str] = None) -> bool:
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: Not installed")
        return False


def get_installed_packages() -> List[str]:
    """Get list of installed packages"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.split('\n')
    except subprocess.CalledProcessError:
        return []


def main():
    """Main check function"""
    print("🔍 XBRL Financial Service - Dependency Check")
    print("=" * 50)
    
    # Check Python version
    python_ok = check_python_version()
    print()
    
    # Core dependencies to check
    core_deps = [
        ("lxml", "lxml"),
        ("python-dateutil", "dateutil"),
        ("SQLAlchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("typing-extensions", "typing_extensions"),
    ]
    
    optional_deps = [
        ("ujson", "ujson"),
        ("pytest", "pytest"),
        ("black", "black"),
        ("mypy", "mypy"),
    ]
    
    print("Core Dependencies:")
    core_ok = True
    for package_name, import_name in core_deps:
        if not check_package(package_name, import_name):
            core_ok = False
    
    print("\nOptional Dependencies:")
    for package_name, import_name in optional_deps:
        check_package(package_name, import_name)
    
    print("\n" + "=" * 50)
    
    if core_ok and python_ok:
        print("✅ All core dependencies are satisfied!")
        print("🚀 Ready to run XBRL Financial Service")
    else:
        print("❌ Some core dependencies are missing")
        print("📦 Run: pip install -r requirements-prod.txt")
        return 1
    
    # Check if package is installed
    print("\nPackage Installation:")
    try:
        import xbrl_financial_service
        print(f"✅ xbrl-financial-service: {getattr(xbrl_financial_service, '__version__', 'dev')}")
    except ImportError:
        print("❌ xbrl-financial-service: Not installed")
        print("📦 Run: pip install -e .")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())