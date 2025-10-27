#!/usr/bin/env python3
"""Test .env file configuration for Z.AI websearch."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_env_setup():
    """Test .env file configuration."""
    
    print("🔧 Testing .env Configuration for Z.AI WebSearch")
    print("=" * 55)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Run: cp .env.example .env")
        return False
    
    print("✅ .env file found")
    
    # Load .env file manually to test
    env_vars = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    # Check for Z_AI_API_KEY
    if 'Z_AI_API_KEY' not in env_vars:
        print("❌ Z_AI_API_KEY not found in .env file")
        print("Add: Z_AI_API_KEY=your_api_key_here")
        return False
    
    api_key = env_vars['Z_AI_API_KEY']
    if not api_key or 'your_' in api_key or api_key == 'your_zai_api_key':
        print("❌ Z_AI_API_KEY is not set with a real value")
        print("Get API key from: https://z.ai/manage-apikey/apikey-list")
        print("Update .env file with: Z_AI_API_KEY=your_actual_api_key")
        return False
    
    print(f"✅ Z_AI_API_KEY found: {'*' * 10}{api_key[-4:] if len(api_key) > 14 else ''}")
    
    # Test toolkit initialization with .env variable
    print("\n🧪 Testing ZAIWebSearchToolkit initialization...")
    
    # Set environment variable from .env
    os.environ['Z_AI_API_KEY'] = api_key
    
    try:
        from roma_glm.tools.web_search.zai_websearch import ZAIWebSearchToolkit
        
        # This should work without errors (though may fail at MCP connection)
        toolkit = ZAIWebSearchToolkit(
            enabled=True,
            api_key=api_key,
            timeout=30.0
        )
        print("✅ ZAIWebSearchToolkit initialized successfully")
        
        # Test method availability
        methods = ['web_search', 'search_news', 'search_real_time']
        for method in methods:
            if hasattr(toolkit, method):
                print(f"✅ {method}() method available")
            else:
                print(f"❌ {method}() method missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Toolkit initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_env_setup()
    
    if success:
        print("\n🎉 .env configuration test passed!")
        print("\n🚀 Ready to use Z.AI web search:")
        print("   uv run python -m roma_glm.cli solve 'search for AI news' --config config/examples/basic/zai_websearch.yaml")
        sys.exit(0)
    else:
        print("\n💥 .env configuration test failed!")
        print("\n🔧 Setup instructions:")
        print("1. cp .env.example .env")
        print("2. Get API key: https://z.ai/manage-apikey/apikey-list")
        print("3. Add to .env: Z_AI_API_KEY=your_actual_api_key")
        sys.exit(1)