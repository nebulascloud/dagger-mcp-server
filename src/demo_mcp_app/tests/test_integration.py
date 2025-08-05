"""
Simplified integration tests for OpenAI MCP Demo application.

Focuses on core functionality rather than internal implementation details.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the demo app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openai_mcp_demo import (
    OptimizedMCPClient,
    demo_optimized_client
)


class TestOptimizedMCPClient(unittest.IsolatedAsyncioTestCase):
    """Simple tests for the core MCP client functionality."""
    
    @patch('openai_mcp_demo.MCPServerStdio')
    @patch('openai_mcp_demo.Agent') 
    @patch('openai_mcp_demo.Runner')
    async def test_basic_query(self, mock_runner, mock_agent, mock_server):
        """Test basic query functionality."""
        # Simple mock setup
        mock_server_instance = AsyncMock()
        mock_server.return_value = mock_server_instance
        
        mock_result = Mock()
        mock_result.final_output_as = Mock(return_value="Test response")
        mock_result.last_response_id = "test-123"
        mock_runner.run = AsyncMock(return_value=mock_result)
        
        client = OptimizedMCPClient()
        async with client.connect():
            response = await client.query("Test question")
            
        self.assertEqual(response, "Test response")
        mock_runner.run.assert_called_once()
    
    @patch('openai_mcp_demo.MCPServerStdio')
    async def test_connection_error_handling(self, mock_server_class):
        """Test connection error handling."""
        mock_server = AsyncMock()
        mock_server.connect.side_effect = Exception("Connection failed")
        mock_server_class.return_value = mock_server
        
        client = OptimizedMCPClient()
        with self.assertRaises(Exception) as context:
            async with client.connect():
                pass
                
        self.assertIn("Connection failed", str(context.exception))

    @patch('openai_mcp_demo.load_dotenv')
    @patch('openai_mcp_demo.OptimizedMCPClient')
    async def test_demo_function(self, mock_client_class, mock_load_dotenv):
        """Test the demo function runs without errors."""
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.query = AsyncMock(return_value="Mock response")
        mock_client.get_conversation_history = AsyncMock(return_value=[])
        mock_client.get_last_response_id = AsyncMock(return_value="mock-id")
        mock_client._last_response_id = "mock-id"
        
        # Create an async context manager
        async def mock_connect():
            yield mock_client
        mock_client.connect.return_value = mock_connect()
        
        mock_client_class.return_value = mock_client
        
        await demo_optimized_client()  # Should not raise
        
        mock_load_dotenv.assert_called_once()


if __name__ == '__main__':
    unittest.main()