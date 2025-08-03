import dagger
from dagger import dag, function, object_type
from typing import List, Optional

@object_type
class DaggerMcpServer:
    @function
    def hello(self) -> str:
        """Returns a friendly greeting"""
        return "Hello, from Dagger MCP Server!"

    @function
    async def run_tests(
        self,
        source: dagger.Directory,
        test_filter: Optional[str] = None,
        coverage_threshold: int = 80,
        branch_coverage_threshold: int = 70,
        parallel: bool = True,
        export_artifacts: bool = True
    ) -> str:
        """
        Run comprehensive test suite for demo MCP application.
        
        Args:
            source: Source directory containing demo_mcp_app
            test_filter: Optional filter for specific tests (e.g., "test_core")
            coverage_threshold: Minimum line coverage percentage (default: 80%)
            branch_coverage_threshold: Minimum branch coverage percentage (default: 70%)
            parallel: Enable parallel test execution (default: True)
            export_artifacts: Export test artifacts and reports (default: True)
            
        Returns:
            Test execution summary as formatted string
        """
        # Import our testing module
        from .testing import TestRunner
        
        # Create test runner and execute tests
        test_runner = TestRunner()
        results = await test_runner.run_tests(
            source=source,
            test_filter=test_filter,
            coverage_threshold=coverage_threshold,
            branch_coverage_threshold=branch_coverage_threshold,
            parallel=parallel,
            export_artifacts=export_artifacts
        )
        
        return results.summary()

    @function
    async def run_unit_tests(self, source: dagger.Directory) -> str:
        """
        Run unit tests only for demo MCP application.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Unit test results summary
        """
        from .testing import TestRunner
        
        test_runner = TestRunner()
        results = await test_runner.run_unit_tests(source)
        
        return f"""=== Unit Test Results ===
Tests Run: {results.tests_run}
Tests Passed: {'✅' if results.tests_passed else '❌'}
Coverage: {results.coverage_percentage:.1f}%
Failed Tests: {', '.join(results.failed_tests) if results.failed_tests else 'None'}
"""

    @function
    async def run_integration_tests(self, source: dagger.Directory) -> str:
        """
        Run integration tests with mock services.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Integration test results summary
        """
        from .testing import TestRunner
        
        test_runner = TestRunner()
        results = await test_runner.run_integration_tests(source)
        
        return f"""=== Integration Test Results ===
Scenarios Tested: {results.scenarios_tested}
Scenarios Passed: {results.scenarios_passed}
Mock Services: {', '.join(results.mock_services_used)}
Workflow Tests: {'✅' if results.workflow_tests_passed else '❌'}
"""

    @function
    async def run_performance_tests(self, source: dagger.Directory) -> str:
        """
        Run performance benchmarks.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Performance test results summary
        """
        from .testing import TestRunner
        
        test_runner = TestRunner()
        results = await test_runner.run_performance_tests(source)
        
        return f"""=== Performance Test Results ===
Benchmarks Run: {results.benchmarks_run}
Benchmarks Passed: {results.benchmarks_passed}
Avg Response Time: {results.avg_response_time_ms:.1f}ms
Memory Usage: {results.memory_usage_mb:.1f}MB
Throughput: {results.throughput_ops_per_sec:.0f} ops/sec
"""

    @function
    async def generate_coverage_reports(
        self, 
        source: dagger.Directory,
        formats: List[str] = ["html", "xml", "json"]
    ) -> dagger.Directory:
        """
        Generate coverage reports in multiple formats.
        
        Args:
            source: Source directory containing demo_mcp_app
            formats: List of coverage report formats ("html", "xml", "json")
            
        Returns:
            Directory containing coverage reports
        """
        from .testing import TestRunner
        
        test_runner = TestRunner()
        return await test_runner.generate_coverage_reports(source, formats)

    @function
    async def test_with_mock_services(self, source: dagger.Directory) -> str:
        """
        Run tests with mock Jira and OpenAI services.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Mock service test results summary
        """
        from .testing import TestRunner
        
        test_runner = TestRunner()
        results = await test_runner.run_mock_service_tests(source)
        
        return f"""=== Mock Service Test Results ===
Mock Services Created: {results.mock_services_created}
Service Tests Passed: {'✅' if results.service_tests_passed else '❌'}
Jira Mock Calls: {results.jira_mock_calls}
OpenAI Mock Calls: {results.openai_mock_calls}
"""
