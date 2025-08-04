"""
Performance tests and benchmarks for OpenAI MCP Demo application.

Tests performance characteristics, resource usage, and scalability
of critical application functions.
"""

import unittest
import asyncio
import time
import tracemalloc
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the demo app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openai_mcp_demo import (
    OptimizedMCPClient,
    MCPConfig,
    AgentConfig,
    _format_issue_list,
    _format_dependency_suggestions,
    _format_link_confirmation
)


class PerformanceBenchmark:
    """Performance measurement utilities."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        
    def __enter__(self):
        tracemalloc.start()
        self.start_memory = tracemalloc.get_traced_memory()[0]
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.end_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
        
    @property
    def memory_delta(self) -> int:
        """Get memory usage change in bytes."""
        if self.start_memory is not None and self.end_memory is not None:
            return self.end_memory - self.start_memory
        return 0


class TestConfigurationPerformance(unittest.TestCase):
    """Performance tests for configuration classes."""

    def test_mcp_config_creation_performance(self):
        """Test MCPConfig creation performance."""
        with PerformanceBenchmark("MCPConfig creation") as bench:
            configs = [MCPConfig() for _ in range(1000)]
        
        # Should create 1000 configs in under 100ms
        self.assertLess(bench.duration, 0.1)
        self.assertEqual(len(configs), 1000)

    def test_agent_config_creation_performance(self):
        """Test AgentConfig creation performance."""
        with PerformanceBenchmark("AgentConfig creation") as bench:
            configs = [AgentConfig() for _ in range(1000)]
        
        # Should create 1000 configs in under 100ms
        self.assertLess(bench.duration, 0.1)
        self.assertEqual(len(configs), 1000)

    def test_client_initialization_performance(self):
        """Test OptimizedMCPClient initialization performance."""
        with PerformanceBenchmark("Client initialization") as bench:
            clients = [OptimizedMCPClient() for _ in range(100)]
        
        # Should create 100 clients in under 50ms
        self.assertLess(bench.duration, 0.05)
        self.assertEqual(len(clients), 100)


class TestFormattingPerformance(unittest.TestCase):
    """Performance tests for response formatting functions."""

    def setUp(self):
        """Set up test data."""
        # Large issue list response
        self.large_issue_response = """Here are some issues in the MCP project:

""" + "\n".join([f"**[MCP-{i}]**: Issue Title {i} - Description: This is issue number {i} with detailed description" 
                 for i in range(1, 101)])

        # Large dependency response
        self.large_dependency_response = """Based on analysis, here are suggested dependencies:

""" + "\n".join([f"MCP-{i} should depend on MCP-{i-1} before implementation" 
                 for i in range(2, 101)])

    def test_format_issue_list_performance(self):
        """Test issue list formatting performance with large data."""
        with PerformanceBenchmark("Format large issue list") as bench:
            result = _format_issue_list(self.large_issue_response)
        
        # Should format 100 issues in under 100ms
        self.assertLess(bench.duration, 0.1)
        self.assertIsInstance(result, str)
        self.assertIn("MCP-1", result)
        self.assertIn("MCP-100", result)

    def test_format_dependency_suggestions_performance(self):
        """Test dependency suggestions formatting performance."""
        with PerformanceBenchmark("Format dependency suggestions") as bench:
            result = _format_dependency_suggestions(self.large_dependency_response)
        
        # Should format 100 dependencies in under 50ms
        self.assertLess(bench.duration, 0.05)
        self.assertIsInstance(result, str)

    def test_format_link_confirmation_performance(self):
        """Test link confirmation formatting performance."""
        confirmations = [
            f"Link has been successfully created between MCP-{i} and MCP-{i+1}"
            for i in range(1, 101)
        ]
        
        with PerformanceBenchmark("Format link confirmations") as bench:
            results = [_format_link_confirmation(conf) for conf in confirmations]
        
        # Should format 100 confirmations in under 50ms
        self.assertLess(bench.duration, 0.05)
        self.assertEqual(len(results), 100)

    def test_formatting_memory_usage(self):
        """Test memory usage of formatting functions."""
        # Test with large data
        large_text = "MCP-123: " + "x" * 10000  # 10KB of text
        
        with PerformanceBenchmark("Memory usage test") as bench:
            # Run formatting functions multiple times
            for _ in range(100):
                _format_issue_list(large_text)
                _format_dependency_suggestions(large_text)
                _format_link_confirmation(large_text)
        
        # Memory delta should be reasonable (less than 10MB)
        self.assertLess(bench.memory_delta, 10 * 1024 * 1024)


class TestClientPerformance(unittest.IsolatedAsyncioTestCase):
    """Performance tests for OptimizedMCPClient."""

    async def test_connection_establishment_performance(self):
        """Test connection establishment performance."""
        client = OptimizedMCPClient()
        
        with patch('openai_mcp_demo.MCPServerStdio') as mock_server_class:
            with patch('openai_mcp_demo.Agent') as mock_agent_class:
                mock_server = AsyncMock()
                mock_server_class.return_value = mock_server
                mock_agent_class.return_value = Mock()
                
                with PerformanceBenchmark("Connection establishment") as bench:
                    await client._establish_connection()
                    await client._cleanup_connection()
                
                # Connection should be established quickly (under 100ms)
                self.assertLess(bench.duration, 0.1)

    async def test_conversation_history_performance(self):
        """Test conversation history operations performance."""
        client = OptimizedMCPClient()
        
        # Add large conversation history
        large_history = [
            {
                "question": f"Question {i}",
                "response": f"Response {i} with detailed text: " + "x" * 1000,
                "response_id": f"id-{i}"
            }
            for i in range(1000)
        ]
        
        client._conversation_history = large_history
        
        with PerformanceBenchmark("History operations") as bench:
            # Test history retrieval
            for _ in range(100):
                history = client.get_conversation_history()
                self.assertEqual(len(history), 1000)
            
            # Test context clearing
            client.clear_conversation_context()
            self.assertEqual(len(client.get_conversation_history()), 0)
        
        # Operations should be fast even with large history
        self.assertLess(bench.duration, 0.1)

    async def test_batch_query_performance(self):
        """Test batch query performance."""
        client = OptimizedMCPClient()
        
        with patch('openai_mcp_demo.Runner') as mock_runner:
            # Setup fast mock responses
            mock_result = Mock()  # Use regular Mock, not AsyncMock
            mock_result.final_output_as = Mock(return_value="Quick response")
            mock_result.last_response_id = "test-id"
            
            # Make run async
            async def async_run(*args, **kwargs):
                return mock_result
            mock_runner.run = async_run
            
            # Setup connected client
            client._connected = True
            client._agent = Mock()
            
            questions = [f"Question {i}" for i in range(10)]
            
            with PerformanceBenchmark("Batch query processing") as bench:
                results = await client.batch_query(questions)
            
            # Should process 10 questions quickly
            self.assertLess(bench.duration, 0.1)
            self.assertEqual(len(results), 10)

    async def test_concurrent_query_performance(self):
        """Test concurrent query handling performance."""
        client = OptimizedMCPClient()
        
        with patch('openai_mcp_demo.Runner') as mock_runner:
            # Add realistic delay to simulate network
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(0.01)  # 10ms delay
                result = Mock()  # Use regular Mock, not AsyncMock
                result.final_output_as = Mock(return_value="Concurrent response")
                result.last_response_id = "concurrent-id"
                return result
            
            mock_runner.run = delayed_response
            
            # Setup connected client
            client._connected = True
            client._agent = Mock()
            
            # Run multiple queries concurrently
            questions = [f"Concurrent question {i}" for i in range(5)]
            
            with PerformanceBenchmark("Concurrent queries") as bench:
                # Sequential execution for comparison
                tasks = []
                for question in questions:
                    task = client.query(question, use_conversation_context=False)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
            
            # With 10ms delay per query, 5 queries should take around 50ms total
            # (since they should run concurrently in gather)
            self.assertLess(bench.duration, 0.1)
            self.assertEqual(len(results), 5)


class TestScalabilityBenchmarks(unittest.TestCase):
    """Scalability and stress tests."""

    def test_large_response_handling(self):
        """Test handling of very large responses."""
        # Generate large response (1MB)
        large_response = "MCP-123: Issue with large description - " + "x" * (1024 * 1024)
        
        with PerformanceBenchmark("Large response formatting") as bench:
            result = _format_issue_list(large_response)
        
        # Should handle large responses efficiently
        self.assertLess(bench.duration, 0.5)
        self.assertIsInstance(result, str)

    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations."""
        initial_memory = None
        final_memory = None
        
        # Run many operations to detect leaks
        for iteration in range(10):
            if iteration == 1:  # Measure after warmup
                tracemalloc.start()
                initial_memory = tracemalloc.get_traced_memory()[0]
            
            # Perform operations that could leak memory
            client = OptimizedMCPClient()
            config = MCPConfig()
            agent_config = AgentConfig()
            
            # Format responses
            for i in range(100):
                response = f"Issue MCP-{i}: Test issue with description"
                _format_issue_list(response)
                _format_dependency_suggestions(response)
                _format_link_confirmation(response)
            
            if iteration == 9:  # Measure at end
                final_memory = tracemalloc.get_traced_memory()[0]
                tracemalloc.stop()
        
        # Memory growth should be minimal (less than 1MB)
        if initial_memory and final_memory:
            memory_growth = final_memory - initial_memory
            self.assertLess(memory_growth, 1024 * 1024)

    def test_rapid_client_creation_destruction(self):
        """Test rapid creation and destruction of clients."""
        with PerformanceBenchmark("Rapid client lifecycle") as bench:
            for _ in range(1000):
                client = OptimizedMCPClient()
                # Simulate some usage
                client.clear_conversation_context()
                client.get_conversation_history()
                # Client will be garbage collected
        
        # Should handle rapid lifecycle efficiently
        self.assertLess(bench.duration, 1.0)


class TestPerformanceRegression(unittest.TestCase):
    """Performance regression tests with baseline measurements."""

    def test_configuration_performance_baseline(self):
        """Baseline performance test for configuration creation."""
        iterations = 10000
        
        with PerformanceBenchmark(f"Config creation baseline ({iterations} iterations)") as bench:
            for _ in range(iterations):
                mcp_config = MCPConfig()
                agent_config = AgentConfig()
                client = OptimizedMCPClient(mcp_config, agent_config)
        
        # Record baseline: should create 10k objects in under 1 second
        print(f"Baseline: {iterations} configs created in {bench.duration:.4f}s")
        print(f"Rate: {iterations / bench.duration:.0f} configs/second")
        print(f"Memory delta: {bench.memory_delta / 1024:.1f} KB")
        
        # Assert reasonable performance
        self.assertLess(bench.duration, 1.0)
        self.assertGreater(iterations / bench.duration, 5000)  # At least 5k/sec

    def test_formatting_performance_baseline(self):
        """Baseline performance test for formatting functions."""
        # Generate test data
        issue_response = "Here are issues:\n" + "\n".join([
            f"**[MCP-{i}]**: Issue {i} - Description: Test issue {i}"
            for i in range(100)
        ])
        
        iterations = 1000
        
        with PerformanceBenchmark(f"Formatting baseline ({iterations} iterations)") as bench:
            for _ in range(iterations):
                _format_issue_list(issue_response)
                _format_dependency_suggestions(issue_response)
                _format_link_confirmation(issue_response)
        
        # Record baseline
        operations = iterations * 3  # 3 formatting operations per iteration
        print(f"Baseline: {operations} formatting operations in {bench.duration:.4f}s")
        print(f"Rate: {operations / bench.duration:.0f} operations/second")
        print(f"Memory delta: {bench.memory_delta / 1024:.1f} KB")
        
        # Assert reasonable performance
        self.assertLess(bench.duration, 1.0)
        self.assertGreater(operations / bench.duration, 1000)  # At least 1k ops/sec


if __name__ == '__main__':
    # Run with verbose output to see benchmark results
    unittest.main(verbosity=2)