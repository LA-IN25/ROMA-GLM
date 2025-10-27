#!/usr/bin/env python3
"""Integration demo for Z.AI WebSearch MCP functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_zai_integration():
    """Demonstrate Z.AI WebSearch MCP integration setup."""
    
    print("🚀 ROMA-GLM Z.AI WebSearch MCP Integration Demo")
    print("=" * 60)
    
    # Test 1: Import verification
    print("\n1️⃣ Testing Import...")
    try:
        from roma_glm.tools.web_search.zai_websearch import ZAIWebSearchToolkit
        print("✅ ZAIWebSearchToolkit imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Configuration validation
    print("\n2️⃣ Testing Configuration Validation...")
    try:
        # This should fail gracefully without API key
        toolkit = ZAIWebSearchToolkit(enabled=True)
        print("❌ Should have failed without API key")
        return False
    except ValueError as e:
        if "API key" in str(e):
            print("✅ API key validation working correctly")
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error type: {e}")
        return False
    
    # Test 3: Configuration with mock API key
    print("\n3️⃣ Testing Configuration with Mock API Key...")
    try:
        toolkit = ZAIWebSearchToolkit(
            enabled=True,
            api_key="mock_api_key_for_testing",
            timeout=30.0
        )
        print("✅ Toolkit configuration successful")
        
        # Test method availability
        if hasattr(toolkit, 'web_search'):
            print("✅ web_search method available")
        else:
            print("❌ web_search method missing")
            return False
            
        if hasattr(toolkit, 'search_news'):
            print("✅ search_news method available")
        else:
            print("❌ search_news method missing")
            return False
            
        if hasattr(toolkit, 'search_real_time'):
            print("✅ search_real_time method available")
        else:
            print("❌ search_real_time method missing")
            return False
        
        # Test MCP tools availability (will be empty without real connection)
        tool_names = toolkit.get_available_tool_names()
        print(f"✅ Available tools check: {tool_names}")
        
        enabled_tools = toolkit.get_enabled_tools()
        print(f"✅ Enabled tools check: {list(enabled_tools.keys())}")
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    # Test 4: Configuration file examples
    print("\n4️⃣ Testing Configuration Examples...")
    config_files = [
        "config/examples/basic/zai_websearch.yaml",
        "config/examples/zai/zai_glm_example.yaml"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ Configuration file exists: {config_file}")
        else:
            print(f"❌ Configuration file missing: {config_file}")
    
    print("\n🎉 Integration Demo Completed Successfully!")
    print("\n📋 Next Steps:")
    print("1. Get Z.AI API key from: https://z.ai/manage-apikey/apikey-list")
    print("2. Set environment variable: export Z_AI_API_KEY=your_api_key")
    print("3. Run: uv run python -m roma_glm.cli solve 'search for latest AI news' --config config/examples/basic/zai_websearch.yaml")
    
    return True

if __name__ == "__main__":
    success = demo_zai_integration()
    
    if success:
        print("\n✨ Z.AI WebSearch MCP integration is ready!")
        sys.exit(0)
    else:
        print("\n💥 Integration demo failed!")
        sys.exit(1)