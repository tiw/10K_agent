#!/usr/bin/env python3
"""
Installation script for XBRL Financial Service
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"⚠️  Warning: Python {version.major}.{version.minor} detected.")
        print(f"   Recommended: Python 3.9 or higher")
        print(f"   Some features may not work correctly.")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor} is compatible")
        return True


def install_dependencies(dev_mode=False):
    """Install dependencies"""
    if dev_mode:
        print("🔧 Installing development dependencies...")
        success = run_command("pip install -r requirements-dev.txt", "Installing development dependencies")
    else:
        print("📦 Installing production dependencies...")
        success = run_command("pip install -r requirements-prod.txt", "Installing production dependencies")
    
    return success


def install_package(dev_mode=False):
    """Install the package"""
    if dev_mode:
        return run_command("pip install -e .", "Installing package in development mode")
    else:
        return run_command("pip install .", "Installing package")


def create_data_directories():
    """Create necessary data directories"""
    directories = ["data", "cache", "logs"]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")


def main():
    """Main installation function"""
    print("🚀 XBRL Financial Service Installation")
    print("=" * 50)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check if we're in the right directory
    if not Path("setup.py").exists():
        print("❌ Error: setup.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Ask for installation type
    print("\nInstallation options:")
    print("1. Production (minimal dependencies)")
    print("2. Development (includes testing and dev tools)")
    
    while True:
        choice = input("\nSelect installation type (1 or 2): ").strip()
        if choice in ["1", "2"]:
            break
        print("Please enter 1 or 2")
    
    dev_mode = choice == "2"
    
    print(f"\n🔧 Starting {'development' if dev_mode else 'production'} installation...")
    
    # Upgrade pip first
    run_command("pip install --upgrade pip", "Upgrading pip")
    
    # Install dependencies
    if not install_dependencies(dev_mode):
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Install the package
    if not install_package(dev_mode):
        print("❌ Failed to install package")
        sys.exit(1)
    
    # Create data directories
    create_data_directories()
    
    # Run basic tests if in dev mode
    if dev_mode:
        print("\n🧪 Running basic tests...")
        if run_command("python -m pytest tests/test_basic_functionality.py -v", "Running tests"):
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed, but installation completed")
    
    print("\n🎉 Installation completed successfully!")
    print("\nNext steps:")
    print("1. Download Apple's XBRL files from SEC EDGAR")
    print("2. Run the demo: python demo.py")
    print("3. Try the CLI: xbrl-service --help")
    print("4. Start MCP server: xbrl-service serve-mcp")
    
    if not python_ok:
        print("\n⚠️  Note: Consider upgrading to Python 3.9+ for best compatibility")


if __name__ == "__main__":
    main()