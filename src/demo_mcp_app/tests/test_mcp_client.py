"""
Unit tests for OpenAI MCP Demo application.

Tests the core functionality of the OptimizedMCPClient, configuration classes,
and utility functions without external dependencies.
"""

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List, Dict, Any
import sys
import os

# Add the demo app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openai_mcp_demo import (
    MCPConfig,
    AgentConfig,
    OptimizedMCPClient,
    _format_issue_list,
    _format_dependency_suggestions,
    _format_link_confirmation,
    _format_default_response,
    _format_single_issue
)


class TestMCPConfig(unittest.TestCase):
    """Test cases for MCPConfig class."""

    def test_default_initialization(self):
        """Test MCPConfig with default values."""
        config = MCPConfig()
        self.assertEqual(config.command, "docker")
        self.assertEqual(config.container_name, "mcp-server-atlassian")
        self.assertEqual(config.mcp_command, "mcp-atlassian")
        self.assertEqual(config.args, ["exec", "-i", "mcp-server-atlassian", "mcp-atlassian"])

    def test_custom_initialization(self):
        """Test MCPConfig with custom values."""
        config = MCPConfig(
            command="podman",
            container_name="custom-mcp",
            mcp_command="custom-command"
        )
        self.assertEqual(config.command, "podman")
        self.assertEqual(config.container_name, "custom-mcp")
        self.assertEqual(config.mcp_command, "custom-command")
        self.assertEqual(config.args, ["exec", "-i", "custom-mcp", "custom-command"])

    def test_custom_args(self):
        """Test MCPConfig with custom args."""
        custom_args = ["run", "--rm", "test-container"]
        config = MCPConfig(args=custom_args)
        self.assertEqual(config.args, custom_args)

    @patch.dict(os.environ, {'MCP_CONTAINER_NAME': 'env-container'})
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        config = MCPConfig()
        self.assertEqual(config.container_name, 'env-container')


class TestAgentConfig(unittest.TestCase):
    """Test cases for AgentConfig class."""

    def test_default_initialization(self):
        """Test AgentConfig with default values."""
        config = AgentConfig()
        self.assertEqual(config.name, "jira-assistant")
        self.assertEqual(config.model, "gpt-4o-mini")
        self.assertIn("helpful Jira assistant", config.instructions)

    def test_custom_initialization(self):
        """Test AgentConfig with custom values."""
        config = AgentConfig(
            name="custom-agent",
            model="gpt-4",
            instructions="Custom instructions"
        )
        self.assertEqual(config.name, "custom-agent")
        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.instructions, "Custom instructions")


class TestOptimizedMCPClient(unittest.TestCase):
    """Test cases for OptimizedMCPClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mcp_config = MCPConfig()
        self.agent_config = AgentConfig()
        self.client = OptimizedMCPClient(self.mcp_config, self.agent_config)

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.mcp_config, self.mcp_config)
        self.assertEqual(self.client.agent_config, self.agent_config)
        self.assertIsNone(self.client._server)
        self.assertIsNone(self.client._agent)
        self.assertFalse(self.client._connected)
        self.assertEqual(self.client._conversation_history, [])
        self.assertIsNone(self.client._last_response_id)

    def test_default_config_initialization(self):
        """Test client with default configs."""
        client = OptimizedMCPClient()
        self.assertIsInstance(client.mcp_config, MCPConfig)
        self.assertIsInstance(client.agent_config, AgentConfig)

    def test_get_conversation_history(self):
        """Test conversation history retrieval."""
        history = self.client.get_conversation_history()
        self.assertEqual(history, [])
        self.assertIsNot(history, self.client._conversation_history)  # Should be a copy

    def test_clear_conversation_context(self):
        """Test clearing conversation context."""
        # Add some fake history
        self.client._conversation_history = [{"q": "test", "r": "response"}]
        self.client._last_response_id = "test-id"

        self.client.clear_conversation_context()

        self.assertEqual(self.client._conversation_history, [])
        self.assertIsNone(self.client._last_response_id)

    def test_get_last_response_id(self):
        """Test last response ID retrieval."""
        self.assertIsNone(self.client.get_last_response_id())

        self.client._last_response_id = "test-id"
        self.assertEqual(self.client.get_last_response_id(), "test-id")

    @patch('openai_mcp_demo.Runner')
    @patch('openai_mcp_demo.Agent')
    @patch('openai_mcp_demo.MCPServerStdio')
    async def test_query_without_connection(self, mock_server, mock_agent, mock_runner):
        """Test query raises error when not connected."""
        with self.assertRaises(RuntimeError) as context:
            await self.client.query("test question")
        
        self.assertIn("not connected", str(context.exception))


class TestFormattingFunctions(unittest.TestCase):
    """Test cases for response formatting functions."""

    def test_format_single_issue_with_complete_data(self):
        """Test formatting a single issue with complete information."""
        issue_lines = ["**[MCP-123]**: Implement Testing Stage - Description: Add comprehensive tests - Status: In Progress - Priority: High"]
        result = _format_single_issue(issue_lines)
        
        self.assertIsInstance(result, list)
        self.assertTrue(any("MCP-123" in line for line in result))
        self.assertTrue(any("Implement Testing Stage" in line for line in result))

    def test_format_single_issue_empty(self):
        """Test formatting empty issue list."""
        result = _format_single_issue([])
        self.assertEqual(result, [])

    def test_format_issue_list(self):
        """Test formatting an issue list response."""
        response = """Here are some issues in the MCP project:

1. **[MCP-374]**: Epic Implementation
2. **[MCP-376]**: Code Quality Stage  
3. **[MCP-377]**: Testing Stage Implementation"""
        
        result = _format_issue_list(response)
        self.assertIsInstance(result, str)
        self.assertIn("MCP-374", result)
        self.assertIn("MCP-376", result)
        self.assertIn("MCP-377", result)

    def test_format_dependency_suggestions(self):
        """Test formatting dependency suggestions."""
        response = """Based on analysis, here's a suggested dependency:

MCP-377 should depend on MCP-376 before implementation."""
        
        result = _format_dependency_suggestions(response)
        self.assertIsInstance(result, str)
        self.assertIn("MCP-377", result)
        self.assertIn("MCP-376", result)

    def test_format_link_confirmation_success(self):
        """Test formatting successful link creation."""
        response = "Link has been successfully created between MCP-377 and MCP-376 with link type 'Depends on'"
        
        result = _format_link_confirmation(response)
        self.assertIsInstance(result, str)
        self.assertIn("SUCCESSFULLY", result)
        self.assertIn("MCP-377", result)
        self.assertIn("MCP-376", result)

    def test_format_link_confirmation_error(self):
        """Test formatting link creation error."""
        response = "Error: Failed to create link due to invalid link type"
        
        result = _format_link_confirmation(response)
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    def test_format_default_response(self):
        """Test default response formatting."""
        response = "This is a simple response with some text that should be formatted nicely for display."
        
        result = _format_default_response(response)
        self.assertIsInstance(result, str)
        self.assertEqual(result.strip(), response.strip())

    def test_format_default_response_long_text(self):
        """Test default formatting with long text that should be wrapped."""
        long_text = "This is a very long response " * 10
        
        result = _format_default_response(long_text)
        self.assertIsInstance(result, str)
        # Should contain the original text
        self.assertIn("very long response", result)


class TestAsyncMethods(unittest.IsolatedAsyncioTestCase):
    """Test async methods of OptimizedMCPClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = OptimizedMCPClient()

    @patch('openai_mcp_demo.MCPServerStdio')
    @patch('openai_mcp_demo.Agent')
    async def test_establish_connection_success(self, mock_agent_class, mock_server_class):
        """Test successful connection establishment."""
        # Setup mocks
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        # Test connection
        await self.client._establish_connection()

        # Verify connection state
        self.assertTrue(self.client._connected)
        self.assertIsNotNone(self.client._server)
        self.assertIsNotNone(self.client._agent)

        # Verify server connection was called
        mock_server.connect.assert_called_once()

    @patch('openai_mcp_demo.MCPServerStdio')
    async def test_establish_connection_failure(self, mock_server_class):
        """Test connection establishment failure."""
        # Setup mock to fail
        mock_server = AsyncMock()
        mock_server.connect.side_effect = Exception("Connection failed")
        mock_server_class.return_value = mock_server

        # Test connection failure
        with self.assertRaises(Exception):
            await self.client._establish_connection()

        # Verify cleanup occurred
        self.assertFalse(self.client._connected)

    async def test_cleanup_connection(self):
        """Test connection cleanup."""
        # Setup fake connection state
        mock_server = AsyncMock()
        self.client._server = mock_server
        self.client._agent = Mock()
        self.client._connected = True
        self.client._conversation_history = [{"test": "data"}]
        self.client._last_response_id = "test-id"

        # Test cleanup
        await self.client._cleanup_connection()

        # Verify cleanup
        self.assertFalse(self.client._connected)
        self.assertIsNone(self.client._server)
        self.assertIsNone(self.client._agent)
        self.assertEqual(self.client._conversation_history, [])
        self.assertIsNone(self.client._last_response_id)

        # Verify server cleanup was called
        mock_server.cleanup.assert_called_once()

    @patch('openai_mcp_demo.Runner')
    async def test_batch_query(self, mock_runner):
        """Test batch query processing."""
        # Setup mock
        mock_result = Mock()  # Use regular Mock, not AsyncMock
        mock_result.final_output_as = Mock(return_value="Test response")
        mock_result.last_response_id = "test-id"
        
        # Make run async
        async def async_run(*args, **kwargs):
            return mock_result
        mock_runner.run = async_run

        # Setup client as connected
        self.client._connected = True
        self.client._agent = Mock()

        # Test batch query
        questions = ["Question 1", "Question 2"]
        results = await self.client.batch_query(questions)

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertIn("Question 1", results)
        self.assertIn("Question 2", results)
        self.assertEqual(results["Question 1"], "Test response")
        self.assertEqual(results["Question 2"], "Test response")


if __name__ == '__main__':
    unittest.main()