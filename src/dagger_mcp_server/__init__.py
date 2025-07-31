import dagger
from dagger import dag, function, object_type
import asyncio
from typing import Dict, Any


@object_type
class DaggerMcpServer:
    @function
    def hello(self) -> str:
        """Returns a friendly greeting"""
        return "Hello, from Dagger MCP Server!"

    @function
    async def code_quality(self) -> str:
        """
        Run comprehensive code quality checks including linting, formatting,
        and security scanning.

        This function performs:
        - Linting: flake8, pylint, mypy, isort
        - Formatting: black validation
        - Security: bandit, safety

        Returns a comprehensive quality report with pass/fail status.
        """
        # Create base container with Python and tools
        container = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip"])
        )

        # Copy source code
        source_dir = dag.host().directory(".")
        container = container.with_directory("/app", source_dir).with_workdir(
            "/app"
        )

        # Install dependencies including dev tools
        container = container.with_exec(["pip", "install", "-e", ".[dev]"])

        # Run all quality checks
        results = await self._run_quality_checks(container)

        # Generate comprehensive report
        report = self._generate_quality_report(results)
        return report

    async def _run_quality_checks(
        self, container: dagger.Container
    ) -> Dict[str, Any]:
        """Run all quality checks and collect results"""
        results = {}

        # Run checks in parallel for better performance
        tasks = [
            self._run_flake8(container),
            self._run_black_check(container),
            self._run_mypy(container),
            self._run_isort_check(container),
            self._run_pylint(container),
            self._run_bandit(container),
            self._run_safety(container),
        ]

        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        check_names = [
            "flake8",
            "black",
            "mypy",
            "isort",
            "pylint",
            "bandit",
            "safety",
        ]

        for name, result in zip(check_names, check_results):
            if isinstance(result, Exception):
                results[name] = {
                    "status": "error",
                    "output": str(result),
                    "exit_code": 1,
                }
            else:
                results[name] = result

        return results

    async def _run_flake8(self, container: dagger.Container) -> Dict[str, Any]:
        """Run flake8 linting"""
        try:
            await container.with_exec([
                "flake8",
                "src/",
                "--max-line-length=88",
                "--extend-ignore=E203,W503",
            ]).stdout()
            return {"status": "pass", "output": "No flake8 issues found", "exit_code": 0}
        except dagger.ExecError as e:
            return {
                "status": "fail",
                "output": e.stdout.strip() if e.stdout else "Flake8 found issues",
                "exit_code": e.exit_code,
            }

    async def _run_black_check(self, container: dagger.Container) -> Dict[str, Any]:
        """Run black formatting check"""
        try:
            await container.with_exec(["black", "--check", "--diff", "src/"]).stdout()
            return {
                "status": "pass",
                "output": "Code formatting is compliant with Black",
                "exit_code": 0,
            }
        except dagger.ExecError as e:
            return {
                "status": "fail",
                "output": e.stdout.strip()
                if e.stdout
                else "Black formatting issues found",
                "exit_code": e.exit_code,
            }

    async def _run_mypy(self, container: dagger.Container) -> Dict[str, Any]:
        """Run mypy type checking"""
        try:
            output = await container.with_exec([
                "mypy", "src/", "--ignore-missing-imports"
            ]).stdout()
            return {"status": "pass", "output": output.strip(), "exit_code": 0}
        except dagger.ExecError as e:
            return {
                "status": "fail",
                "output": e.stdout.strip()
                if e.stdout
                else "MyPy type checking issues found",
                "exit_code": e.exit_code,
            }

    async def _run_isort_check(self, container: dagger.Container) -> Dict[str, Any]:
        """Run isort import sorting check"""
        try:
            await container.with_exec([
                "isort", "--check-only", "--diff", "src/"
            ]).stdout()
            return {
                "status": "pass",
                "output": "Import sorting is compliant",
                "exit_code": 0,
            }
        except dagger.ExecError as e:
            return {
                "status": "fail",
                "output": e.stdout.strip()
                if e.stdout
                else "Import sorting issues found",
                "exit_code": e.exit_code,
            }

    async def _run_pylint(self, container: dagger.Container) -> Dict[str, Any]:
        """Run pylint advanced static analysis"""
        try:
            output = await container.with_exec([
                "pylint",
                "src/",
                "--max-line-length=88",
                "--disable=missing-docstring,too-few-public-methods",
            ]).stdout()
            return {"status": "pass", "output": output.strip(), "exit_code": 0}
        except dagger.ExecError as e:
            return {
                "status": "warning",  # Pylint often has warnings, not failures
                "output": e.stdout.strip()
                if e.stdout
                else "Pylint analysis completed with issues",
                "exit_code": e.exit_code,
            }

    async def _run_bandit(self, container: dagger.Container) -> Dict[str, Any]:
        """Run bandit security scanning"""
        try:
            output = await container.with_exec([
                "bandit", "-r", "src/", "-f", "txt", "--skip", "B101"
            ]).stdout()
            return {"status": "pass", "output": output.strip(), "exit_code": 0}
        except dagger.ExecError as e:
            return {
                "status": "fail",
                "output": e.stdout.strip()
                if e.stdout
                else "Security vulnerabilities found",
                "exit_code": e.exit_code,
            }

    async def _run_safety(self, container: dagger.Container) -> Dict[str, Any]:
        """Run safety dependency vulnerability check"""
        try:
            output = await container.with_exec(["safety", "check"]).stdout()
            return {"status": "pass", "output": output.strip(), "exit_code": 0}
        except dagger.ExecError as e:
            return {
                "status": "fail",
                "output": e.stdout.strip()
                if e.stdout
                else "Vulnerable dependencies found",
                "exit_code": e.exit_code,
            }

    def _generate_quality_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive quality report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CODE QUALITY REPORT")
        report_lines.append("=" * 80)

        # Summary
        total_checks = len(results)
        passed = sum(1 for r in results.values() if r["status"] == "pass")
        failed = sum(1 for r in results.values() if r["status"] == "fail")
        warnings = sum(1 for r in results.values() if r["status"] == "warning")
        errors = sum(1 for r in results.values() if r["status"] == "error")

        report_lines.append(f"SUMMARY: {passed}/{total_checks} checks passed")
        report_lines.append(f"- Passed: {passed}")
        report_lines.append(f"- Failed: {failed}")
        report_lines.append(f"- Warnings: {warnings}")
        report_lines.append(f"- Errors: {errors}")
        report_lines.append("")

        # Overall status
        if failed > 0 or errors > 0:
            report_lines.append("🔴 OVERALL STATUS: FAILED")
        elif warnings > 0:
            report_lines.append("🟡 OVERALL STATUS: PASSED WITH WARNINGS")
        else:
            report_lines.append("🟢 OVERALL STATUS: PASSED")

        report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED RESULTS:")
        report_lines.append("-" * 40)

        for check_name, result in results.items():
            status_icon = {
                "pass": "🟢",
                "fail": "🔴",
                "warning": "🟡",
                "error": "❌",
            }.get(result["status"], "❓")

            report_lines.append(
                f"{status_icon} {check_name.upper()}: {result['status'].upper()}"
            )
            if result["output"]:
                # Indent output
                output_lines = result["output"].split("\n")
                for line in output_lines[:10]:  # Limit output lines
                    report_lines.append(f"  {line}")
                if len(output_lines) > 10:
                    report_lines.append(
                        f"  ... (truncated {len(output_lines) - 10} more lines)"
                    )
            report_lines.append("")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    @function
    async def lint_with_flake8(self) -> str:
        """Run only flake8 linting"""
        container = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip"])
            .with_directory("/app", dag.host().directory("."))
            .with_workdir("/app")
            .with_exec(["pip", "install", "-e", ".[dev]"])
        )

        result = await self._run_flake8(container)
        return f"Flake8 Status: {result['status']}\n{result['output']}"

    @function
    async def format_with_black(self) -> str:
        """Check code formatting with Black"""
        container = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip"])
            .with_directory("/app", dag.host().directory("."))
            .with_workdir("/app")
            .with_exec(["pip", "install", "-e", ".[dev]"])
        )

        result = await self._run_black_check(container)
        return f"Black Status: {result['status']}\n{result['output']}"

    @function
    async def security_scan(self) -> str:
        """Run security scanning with Bandit and Safety"""
        container = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip"])
            .with_directory("/app", dag.host().directory("."))
            .with_workdir("/app")
            .with_exec(["pip", "install", "-e", ".[dev]"])
        )

        bandit_result = await self._run_bandit(container)
        safety_result = await self._run_safety(container)

        report = []
        report.append("SECURITY SCAN RESULTS")
        report.append("=" * 30)
        report.append(f"Bandit: {bandit_result['status']}")
        report.append(f"Safety: {safety_result['status']}")
        report.append("")
        report.append("Bandit Output:")
        report.append(bandit_result["output"])
        report.append("")
        report.append("Safety Output:")
        report.append(safety_result["output"])

        return "\n".join(report)
