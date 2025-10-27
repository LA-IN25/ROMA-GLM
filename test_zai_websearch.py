#!/usr/bin/env python3
"""Test script for Z.AI WebSearch MCP integration."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from roma_glm.tools.web_search.zai_websearch import ZAIWebSearchToolkit


async def test_zai_websearch():
    """Test Z.AI WebSearch toolkit functionality."""
    
    # Check for API key
    api_key = os.getenv('Z_AI_API_KEY')
    if not api_key:
        print("❌ Z_AI_API_KEY environment variable not set")
        print("Get API key from: https://z.ai/manage-apikey/apikey-list")
        return False
    
    print("🔧 Initializing Z.AI WebSearch toolkit...")
    
    try:
        # Initialize toolkit
        toolkit = ZAIWebSearchToolkit(
            enabled=True,
            api_key=api_key,
            timeout=30.0
        )
        
        print("✅ Toolkit initialized successfully")
        
        # Test basic web search
        print("\n🔍 Testing basic web search...")
        result = toolkit.web_search("latest AI developments", max_results=3)
        print(f"Search result: {result[:200]}...")
        
        # Test news search
        print("\n📰 Testing news search...")
        news_result = toolkit.search_news("artificial intelligence", max_results=2)
        print(f"News result: {news_result[:200]}...")
        
        # Test real-time search
        print("\n⚡ Testing real-time search...")
        realtime_result = toolkit.search_real_time("Python programming")
        print(f"Real-time result: {realtime_result[:200]}...")
        
        # Test MCP tools availability
        print("\n🛠️ Testing MCP tools availability...")
        tool_names = toolkit.get_available_tool_names()
        print(f"Available tools: {tool_names}")
        
        enabled_tools = toolkit.get_enabled_tools()
        print(f"Enabled tools: {list(enabled_tools.keys())}")
        
        # Cleanup
        await toolkit.cleanup()
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing Z.AI WebSearch MCP Integration")
    print("=" * 50)
    
    success = asyncio.run(test_zai_websearch())
    
    if success:
        print("\n🎉 Z.AI WebSearch MCP integration is working!")
        sys.exit(0)
    else:
        print("\n💥 Z.AI WebSearch MCP integration failed!")
        sys.exit(1)