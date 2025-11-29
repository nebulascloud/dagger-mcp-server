import dagger
from dagger import dag, function, object_type
from typing import List, Optional
import json

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
    ) -> str:
        """
        Run the test suite with coverage reporting.
        
        Args:
            source: Source directory to test
            test_filter: Optional test filter pattern
            coverage_threshold: Minimum coverage percentage required
            
        Returns:
            Test results summary
        """
        # Import our testing module using absolute import
        import sys
        import os
        # Add the current module path to sys.path if needed
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from testing import TestRunner
        
        # Create and run tests
        test_runner = TestRunner()
        results = await test_runner.run_tests(
            source=source,
            test_filter=test_filter,
            coverage_threshold=coverage_threshold
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
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from testing import TestRunner
        
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
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from testing import TestRunner
        
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
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from testing import TestRunner
        
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
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from testing import TestRunner
        
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
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from testing import TestRunner
        
        test_runner = TestRunner()
        results = await test_runner.run_mock_service_tests(source)
        
        return f"""=== Mock Service Test Results ===
Mock Services Created: {results.mock_services_created}
Service Tests Passed: {'✅' if results.service_tests_passed else '❌'}
Jira Mock Calls: {results.jira_mock_calls}
OpenAI Mock Calls: {results.openai_mock_calls}
"""

    # Building Stage Functions
    @function
    async def build_artifacts(
        self,
        source: dagger.Directory,
        environment: str = "production"
    ) -> str:
        """
        Build all artifacts for the MCP application.
        
        Args:
            source: Source directory containing demo_mcp_app
            environment: Target environment (production, staging, development)
            
        Returns:
            Build results summary
        """
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from building import Builder
        
        builder = Builder()
        results = await builder.build_artifacts(source, environment)
        
        return results.summary()

    @function
    async def build_production_image(
        self,
        source: dagger.Directory
    ) -> dagger.Container:
        """
        Build optimized production container image.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Production-ready container with security hardening
        """
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from building import Builder
        
        builder = Builder()
        return await builder.build_production_image(source)

    @function
    async def generate_python_packages(
        self,
        source: dagger.Directory
    ) -> dagger.Directory:
        """
        Generate Python wheel and source distribution packages.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Directory containing Python distribution packages
        """
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from building import Builder
        
        builder = Builder()
        return await builder.generate_python_packages(source)

    @function
    async def create_deployment_manifests(
        self,
        source: dagger.Directory,
        registry: str = "ghcr.io/nebulascloud"
    ) -> dagger.Directory:
        """
        Generate Docker Compose and Kubernetes deployment manifests.
        
        Args:
            source: Source directory containing demo_mcp_app
            registry: Container registry URL
            
        Returns:
            Directory containing deployment manifests
        """
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from building import Builder
        
        builder = Builder()
        return await builder.create_deployment_manifests(source, registry)

    @function
    async def generate_documentation(
        self,
        source: dagger.Directory
    ) -> dagger.Directory:
        """
        Generate API documentation from source code.
        
        Args:
            source: Source directory containing demo_mcp_app
            
        Returns:
            Directory containing generated documentation
        """
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from building import Builder
        
        builder = Builder()
        return await builder.generate_documentation(source)

    # Security Stage (MCP-379)
    @function
    async def security_scan(
        self,
        source: dagger.Directory,
        image_ref: Optional[str] = None,
        enable_image_scan: Optional[bool] = None,
        # Optional overrides for gating + secret scanning
        max_high: Optional[int] = None,
        fail_on_critical: Optional[bool] = None,
        severity_floor: Optional[str] = None,
        include_env_files: Optional[bool] = None,
        timeout_seconds: Optional[int] = None,
    docker_hub_token: Optional[str] = None,
    ) -> dagger.Directory:
        """Run security scanning stage (Bandit, pip-audit/safety, secrets, optional Trivy).

        Args:
            source: Source directory to scan.
            image_ref: Optional image reference for Trivy when SECURITY_ENABLE_IMAGE_SCAN=true.

        Returns:
            Directory containing security-report.json, summary.md, and raw tool outputs.
        """
        import sys, os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from security import SecurityStage
        stage = SecurityStage()
        return await stage.security_scan(
            source,
            image_ref,
            enable_image_scan=enable_image_scan,
            max_high=max_high,
            fail_on_critical=fail_on_critical,
            severity_floor=severity_floor,
            include_env_files=include_env_files,
            timeout_seconds=timeout_seconds,
            docker_hub_token=docker_hub_token,
        )

    @function
    async def security_scan_smoke(
        self,
        source: dagger.Directory,
        image_ref: Optional[str] = None,
        enable_image_scan: Optional[bool] = None,
        # Optional overrides for gating + secret scanning
        max_high: Optional[int] = None,
        fail_on_critical: Optional[bool] = None,
        severity_floor: Optional[str] = None,
        include_env_files: Optional[bool] = None,
        timeout_seconds: Optional[int] = None,
    docker_hub_token: Optional[str] = None,
    ) -> str:
        """Run a smoke test of the security scan and return a concise PASS/FAIL summary.

        Runs the full security_scan inside Dagger, reads the produced artifacts,
        and emits a short textual summary suitable for CI/CD logs.
        """
        artifacts = await self.security_scan(
            source,
            image_ref,
            enable_image_scan=enable_image_scan,
            max_high=max_high,
            fail_on_critical=fail_on_critical,
            severity_floor=severity_floor,
            include_env_files=include_env_files,
            timeout_seconds=timeout_seconds,
            docker_hub_token=docker_hub_token,
        )
        report_json = await artifacts.file("security-report.json").contents()
        report = json.loads(report_json)
        summ = report.get("summary", {})
        by_sev = summ.get("by_severity", {})
        gate_pass = summ.get("gate_pass", False)
        rationale = "; ".join(summ.get("gate_rationale", []))
        return (
            "Security Scan Smoke Result:\n"
            f"Gate: {'PASS' if gate_pass else 'FAIL'}\n"
            f"Total Findings: {summ.get('total', 0)} | "
            f"Critical:{by_sev.get('Critical',0)} High:{by_sev.get('High',0)} "
            f"Medium:{by_sev.get('Medium',0)} Low:{by_sev.get('Low',0)} Info:{by_sev.get('Info',0)}\n"
            f"Rationale: {rationale}\n"
        )

    @function
    async def build_and_security_scan(
        self,
        source: dagger.Directory,
        publish_address: str,
        enable_image_scan: Optional[bool] = None,
        # Optional overrides for gating + secret scanning
        max_high: Optional[int] = None,
        fail_on_critical: Optional[bool] = None,
        severity_floor: Optional[str] = None,
        include_env_files: Optional[bool] = None,
        timeout_seconds: Optional[int] = None,
    docker_hub_token: Optional[str] = None,
    ) -> dagger.Directory:
        """Build a production image, publish it, then run security scan (incl. image scan).

        Notes:
        - Requires registry access for the Dagger engine to publish and Trivy to pull.
        - Use a public registry or ensure you've logged in (e.g., GHCR) on the host.

        Returns:
            Directory with security-report.json, summary.md, and raw/* outputs.
        """
        import sys, os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Build image
        from building import Builder
        builder = Builder()
        container = await builder.build_production_image(source)

        # Publish to provided address (e.g., ghcr.io/org/repo:tag)
        image_ref = await container.publish(publish_address)

        # Run security scan including Trivy via image_ref (enable via env var)
        from security import SecurityStage
        stage = SecurityStage()
        return await stage.security_scan(
            source,
            image_ref=image_ref,
            enable_image_scan=enable_image_scan,
            max_high=max_high,
            fail_on_critical=fail_on_critical,
            severity_floor=severity_floor,
            include_env_files=include_env_files,
            timeout_seconds=timeout_seconds,
            docker_hub_token=docker_hub_token,
        )
