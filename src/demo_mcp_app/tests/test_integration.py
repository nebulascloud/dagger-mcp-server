"""
Integration tests for OpenAI MCP Demo application.

Tests end-to-end workflows and integration between components,
using mocked external services.
"""

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys
import os

# Add the demo app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openai_mcp_demo import (
    OptimizedMCPClient,
    MCPConfig,
    AgentConfig,
    demo_optimized_client
)


class MockAsyncContextManager:
    """Mock async context manager for testing."""
    def __init__(self, client):
        self.client = client
    
    async def __aenter__(self):
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class MockMCPServer:
    """Mock MCP server for integration testing."""
    
    def __init__(self, server_params=None):
        self.connected = False
        self.server_params = server_params
    
    async def connect(self):
        self.connected = True
    
    async def cleanup(self):
        self.connected = False
    
    # Add async context manager support
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


class MockAgent:
    """Mock OpenAI agent for integration testing."""
    
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'test-agent')
        self.model = kwargs.get('model', 'gpt-4o-mini')


class MockRunner:
    """Mock runner for integration testing."""
    
    @staticmethod
    async def run(agent, question, previous_response_id=None):
        """Mock runner that simulates OpenAI responses."""
        result = Mock()  # Use regular Mock, not AsyncMock
        
        # Simulate different types of responses based on question
        if "projects" in question.lower():
            result.final_output_as = Mock(return_value="Here are your Jira projects: MCP, DEMO, TEST")
        elif "issues" in question.lower():
            result.final_output_as = Mock(return_value="""Here are some issues in the MCP project:

1. **[MCP-374]**: Epic Implementation - Description: Main epic for CI pipeline
2. **[MCP-376]**: Code Quality Stage - Status: Done 
3. **[MCP-377]**: Testing Stage Implementation - Status: In Progress""")
        elif "dependencies" in question.lower():
            result.final_output_as = Mock(return_value="""Based on analysis, here are suggested dependencies:

MCP-377 should depend on MCP-376 before implementation can begin.
MCP-376 provides the foundation for MCP-377.""")
        elif "link" in question.lower():
            result.final_output_as = Mock(return_value="Link has been successfully created between MCP-377 and MCP-376")
        else:
            result.final_output_as = Mock(return_value=f"Processed: {question}")
        
        result.last_response_id = f"response-{hash(question) % 10000}"
        return result


class TestIntegrationWorkflows(unittest.IsolatedAsyncioTestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.mcp_config = MCPConfig(container_name="test-mcp-container")
        self.agent_config = AgentConfig(name="test-agent")

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_complete_jira_analysis_workflow(self):
        """Test complete Jira dependency analysis workflow."""
        client = OptimizedMCPClient(self.mcp_config, self.agent_config)
        
        async with client.connect():
            # Step 1: Query for issues
            issues_response = await client.query("Show me issues in the MCP project")
            self.assertIn("MCP-374", issues_response)
            self.assertIn("MCP-376", issues_response)
            self.assertIn("MCP-377", issues_response)
            
            # Step 2: Analyze dependencies
            deps_response = await client.query("Based on the issues, suggest dependencies")
            self.assertIn("MCP-377", deps_response)
            self.assertIn("MCP-376", deps_response)
            self.assertIn("depend", deps_response)
            
            # Step 3: Create link
            link_response = await client.query("Create the suggested dependency link")
            self.assertIn("successfully created", link_response)
            
            # Verify conversation context is maintained
            history = client.get_conversation_history()
            self.assertEqual(len(history), 3)
            self.assertIsNotNone(client.get_last_response_id())

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_batch_processing_workflow(self):
        """Test batch processing of multiple queries."""
        client = OptimizedMCPClient(self.mcp_config, self.agent_config)
        
        questions = [
            "What projects are available?",
            "Show me issues in MCP project",
            "Suggest dependencies for these issues"
        ]
        
        async with client.connect():
            results = await client.batch_query(questions)
            
            # Verify all questions were processed
            self.assertEqual(len(results), 3)
            for question in questions:
                self.assertIn(question, results)
                self.assertIsInstance(results[question], str)
                self.assertTrue(len(results[question]) > 0)

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_conversation_context_persistence(self):
        """Test that conversation context is maintained across queries."""
        client = OptimizedMCPClient(self.mcp_config, self.agent_config)
        
        async with client.connect():
            # First query
            response1 = await client.query("Show me issues")
            first_response_id = client.get_last_response_id()
            
            # Second query should use context
            response2 = await client.query("Create dependencies for these")
            second_response_id = client.get_last_response_id()
            
            # Verify context progression
            self.assertIsNotNone(first_response_id)
            self.assertIsNotNone(second_response_id)
            self.assertNotEqual(first_response_id, second_response_id)
            
            # Verify conversation history
            history = client.get_conversation_history()
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]['question'], "Show me issues")
            self.assertEqual(history[1]['question'], "Create dependencies for these")

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_connection_cleanup_on_error(self):
        """Test that connections are properly cleaned up on errors."""
        client = OptimizedMCPClient(self.mcp_config, self.agent_config)
        
        # Simulate error during query
        with patch.object(MockRunner, 'run', side_effect=Exception("Simulated error")):
            try:
                async with client.connect():
                    await client.query("This will fail")
            except Exception:
                pass  # Expected
        
        # Verify cleanup occurred
        self.assertFalse(client._connected)
        self.assertIsNone(client._server)
        self.assertIsNone(client._agent)

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_retry_mechanism(self):
        """Test query retry mechanism on failures."""
        client = OptimizedMCPClient(self.mcp_config, self.agent_config)
        
        call_count = 0
        
        async def failing_run(agent, question, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times
                raise Exception("Temporary failure")
            # Succeed on 3rd attempt
            result = Mock()
            result.final_output_as = Mock(return_value="Success after retries")
            result.last_response_id = "retry-success"
            return result
        
        async with client.connect():
            with patch.object(MockRunner, 'run', side_effect=failing_run):
                response = await client.query("Test retry", max_retries=3)
                
                self.assertEqual(response, "Success after retries")
                self.assertEqual(call_count, 3)

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_context_clearing(self):
        """Test conversation context clearing."""
        client = OptimizedMCPClient(self.mcp_config, self.agent_config)
        
        async with client.connect():
            # Build up some context
            await client.query("First question")
            await client.query("Second question")
            
            # Verify context exists
            self.assertEqual(len(client.get_conversation_history()), 2)
            self.assertIsNotNone(client.get_last_response_id())
            
            # Clear context
            client.clear_conversation_context()
            
            # Verify context is cleared
            self.assertEqual(len(client.get_conversation_history()), 0)
            self.assertIsNone(client.get_last_response_id())
            
            # Verify we can still make queries
            response = await client.query("New question after clear")
            self.assertIsInstance(response, str)


class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test error handling in integration scenarios."""

    @patch('openai_mcp_demo.MCPServerStdio')
    async def test_connection_failure(self, mock_server_class):
        """Test handling of connection failures."""
        # Setup mock to fail connection
        mock_server = AsyncMock()
        mock_server.connect.side_effect = Exception("Connection failed")
        mock_server_class.return_value = mock_server
        
        client = OptimizedMCPClient()
        
        with self.assertRaises(Exception) as context:
            async with client.connect():
                pass
        
        self.assertIn("Connection failed", str(context.exception))

    @patch('openai_mcp_demo.MCPServerStdio', MockMCPServer)
    @patch('openai_mcp_demo.Agent', MockAgent)
    @patch('openai_mcp_demo.Runner', MockRunner)
    async def test_graceful_degradation(self):
        """Test graceful handling of partial failures."""
        client = OptimizedMCPClient()
        
        # Mock runner that fails on specific questions
        async def selective_failure(agent, question, **kwargs):
            if "fail" in question.lower():
                raise Exception("Intentional failure")
            result = Mock()
            result.final_output_as = Mock(return_value=f"Success: {question}")
            result.last_response_id = "success-id"
            return result
        
        questions = [
            "This will succeed",
            "This will fail intentionally", 
            "This will also succeed"
        ]
        
        async with client.connect():
            with patch.object(MockRunner, 'run', side_effect=selective_failure):
                results = await client.batch_query(questions)
                
                # Verify partial success
                self.assertEqual(len(results), 3)
                self.assertIn("Success:", results["This will succeed"])
                self.assertIn("Error:", results["This will fail intentionally"])
                self.assertIn("Success:", results["This will also succeed"])


class TestDemoFunction(unittest.IsolatedAsyncioTestCase):
    """Test the main demo function."""

    @patch('openai_mcp_demo.load_dotenv')
    @patch('openai_mcp_demo.OptimizedMCPClient')
    async def test_demo_execution(self, mock_client_class, mock_load_dotenv):
        """Test demo function execution."""
        # Setup mocks
        mock_client = AsyncMock()
        
        # Create simple async context manager mock
        mock_client.connect = Mock(return_value=MockAsyncContextManager(mock_client))
        mock_client.query = AsyncMock(return_value="Mock response")
        mock_client.get_conversation_history = Mock(return_value=[])
        mock_client.get_last_response_id = Mock(return_value="mock-id")
        mock_client._last_response_id = "mock-id"
        
        mock_client_class.return_value = mock_client
        
        # Test demo execution
        await demo_optimized_client()
        
        # Verify environment loading
        mock_load_dotenv.assert_called_once()
        
        # Verify client usage
        mock_client_class.assert_called_once()
        mock_client.connect.assert_called_once()


if __name__ == '__main__':
    unittest.main()