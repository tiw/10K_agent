#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
from pathlib import Path

def test_imports():
    """Test all main imports"""
    print("🧪 Testing XBRL Financial Service Imports")
    print("=" * 50)
    
    try:
        # Test main package imports
        print("📦 Testing main package imports...")
        from xbrl_financial_service import XBRLParser, FinancialService, Config
        from xbrl_financial_service import FinancialFact, FinancialStatement, FilingData
        print("✅ Main package imports successful")
        
        # Test utility imports
        print("🔧 Testing utility imports...")
        from xbrl_financial_service.utils.logging import setup_logging
        from xbrl_financial_service.utils.exceptions import XBRLParsingError
        print("✅ Utility imports successful")
        
        # Test MCP server import
        print("🌐 Testing MCP server import...")
        from xbrl_financial_service.mcp_server import FinancialMCPServer
        print("✅ MCP server import successful")
        
        # Test parser imports
        print("🔍 Testing parser imports...")
        from xbrl_financial_service.parsers import SchemaParser, LinkbaseParser, InstanceParser
        print("✅ Parser imports successful")
        
        # Test database imports
        print("💾 Testing database imports...")
        from xbrl_financial_service.database import DatabaseManager
        print("✅ Database imports successful")
        
        # Test basic functionality
        print("⚙️  Testing basic functionality...")
        config = Config()
        parser = XBRLParser(config)
        service = FinancialService(config=config)
        print("✅ Basic functionality test successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_demo_imports():
    """Test demo-specific imports"""
    print("\n🎯 Testing demo script imports...")
    
    try:
        # Test all imports used in demo.py
        from xbrl_financial_service import XBRLParser, FinancialService, Config
        from xbrl_financial_service.utils.logging import setup_logging
        from xbrl_financial_service.mcp_server import FinancialMCPServer
        
        print("✅ Demo imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Demo import error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_imports()
    demo_success = test_demo_imports()
    
    if success and demo_success:
        print("\n✅ All tests passed! You can now run demo.py")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)