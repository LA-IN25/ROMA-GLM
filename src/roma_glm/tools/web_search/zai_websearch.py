"""Z.AI Web Search MCP toolkit integration.

This toolkit provides access to Z.AI's web search capabilities through the Model Context Protocol (MCP).
It connects to the remote Z.AI websearch MCP server to provide real-time web search functionality.
"""

import os
from typing import Optional, Dict, Any

from roma_glm.tools.base.base import BaseToolkit


class ZAIWebSearchToolkit(BaseToolkit):
    """
    Z.AI Web Search toolkit providing real-time web search capabilities via MCP.
    
    This toolkit connects to Z.AI's remote MCP server to provide web search functionality.
    It requires a valid Z.AI API key for authentication.
    
    Features:
    - Real-time web search
    - Latest information retrieval
    - News, stock prices, weather data
    - Remote HTTP-based MCP service
    
    Authentication:
    Requires Z.AI_API_KEY environment variable or api_key in configuration.
    Get API key from: https://z.ai/manage-apikey/apikey-list
    """

    def _setup_dependencies(self) -> None:
        """Setup Z.AI WebSearch toolkit dependencies."""
        # Check if MCP dependencies are available
        try:
            from roma_glm.tools.mcp.toolkit import MCPToolkit
            self._MCPToolkit = MCPToolkit
        except ImportError as e:
            raise ImportError(
                f"MCP dependencies missing: {e}. "
                "Install with: pip install 'roma-glm[mcp]'"
            )

        # Get API key from config, environment, or .env file
        self.api_key = self.config.get('api_key') or os.getenv('Z_AI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Z.AI API key is required. Set Z_AI_API_KEY in your .env file, "
                "as environment variable, or provide 'api_key' in toolkit_config. "
                "Get API key from: https://z.ai/manage-apikey/apikey-list\n\n"
                "To set up .env file:\n"
                "1. Copy .env.example to .env\n"
                "2. Add: Z_AI_API_KEY=your_actual_api_key_here"
            )

    def _initialize_tools(self) -> None:
        """Initialize Z.AI WebSearch MCP connection."""
        # Create MCP toolkit instance for Z.AI websearch
        self.mcp_toolkit = self._MCPToolkit(
            server_name="zai-websearch",
            server_type="http",
            url="https://api.z.ai/api/mcp/web_search_prime/mcp",
            headers={
                "Authorization": f"Bearer {self.api_key}"
            },
            transport_type="streamable",  # Use streamable HTTP transport
            tool_timeout=self.config.get('timeout', 30.0),
            enabled=self.enabled,
            include_tools=self.include_tools,
            exclude_tools=self.exclude_tools,
            file_storage=getattr(self, 'file_storage', None),
            **self.config
        )

        # Store the MCP tools for access
        self._mcp_tools = {}

    def get_available_tool_names(self) -> set:
        """Get available web search tool names."""
        if not hasattr(self, 'mcp_toolkit'):
            return set()
        return self.mcp_toolkit.get_available_tool_names()

    def get_enabled_tools(self) -> Dict[str, Any]:
        """Get enabled web search tools."""
        if not hasattr(self, 'mcp_toolkit'):
            return {}
        return self.mcp_toolkit.get_enabled_tools()

    async def cleanup(self) -> None:
        """Cleanup MCP connection."""
        if hasattr(self, 'mcp_toolkit'):
            await self.mcp_toolkit.cleanup()

    def web_search(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Perform web search using Z.AI's webSearchPrime tool.
        
        Search the web for real-time information including news, articles,
        and other web content. Returns comprehensive search results with
        titles, URLs, summaries, site names, and icons.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (optional)
            
        Returns:
            JSON string containing search results with metadata
            
        Examples:
            web_search("latest AI developments") - Search for AI news
            web_search("Python tutorials", max_results=5) - Get 5 Python tutorials
            web_search("weather forecast New York") - Get weather information
        """
        try:
            # Get the webSearchPrime tool from MCP toolkit
            tools = self.get_enabled_tools()
            websearch_tool = tools.get('webSearchPrime')
            
            if not websearch_tool:
                return '{"success": false, "error": "webSearchPrime tool not available"}'
            
            # Prepare arguments for the search
            args = {"query": str(query)}
            if max_results is not None:
                args["max_results"] = str(max_results)
            
            # Execute the search
            import asyncio
            result = asyncio.run(websearch_tool.acall(**args))
            
            self.log_debug(f"Z.AI web search completed for query: '{query}'")
            return result
            
        except Exception as e:
            error_msg = f"Error in Z.AI web search: {str(e)}"
            self.log_error(error_msg)
            return f'{{"success": false, "error": "{error_msg}"}}'

    def search_news(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Search for news articles using Z.AI's web search.
        
        Search for recent news articles and current events. The web search
        will prioritize news sources and recent content.
        
        Args:
            query: News search query string
            max_results: Maximum number of results to return (optional)
            
        Returns:
            JSON string containing news search results
            
        Examples:
            search_news("artificial intelligence") - Get AI news
            search_news("climate change", max_results=10) - Get climate news
            search_news("technology stocks") - Get tech stock news
        """
        # Add news-specific terms to improve news search results
        news_query = f"{query} news latest"
        return self.web_search(news_query, max_results)

    def search_real_time(self, query: str) -> str:
        """
        Search for real-time information using Z.AI's web search.
        
        This method is optimized for finding real-time data such as:
        - Current weather conditions
        - Live stock prices
        - Recent sports scores
        - Breaking news
        
        Args:
            query: Real-time search query string
            
        Returns:
            JSON string containing real-time search results
            
        Examples:
            search_real_time("AAPL stock price") - Get current Apple stock price
            search_real_time("weather London") - Get London weather
            search_real_time("Bitcoin price") - Get current Bitcoin price
        """
        # Add real-time indicators to the query
        realtime_query = f"{query} current now today"
        return self.web_search(realtime_query, max_results=5)