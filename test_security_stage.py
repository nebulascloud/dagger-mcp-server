#!/usr/bin/env python3
"""Basic validation tests for Security Stage (MVP MCP-379).

Focus:
- Module import & function availability
- security_scan returns expected artifact files
- JSON schema basic shape and deterministic ordering
- Gate logic fields present

This is a lightweight test (does not assert real vulnerabilities).
"""
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dagger_mcp_server.security import SecurityStage  # type: ignore
from dagger_mcp_server import DaggerMcpServer  # type: ignore
import dagger  # type: ignore


async def run_security_scan():
    async with dagger.Connection(dagger.Config()) as client:
        src = client.host().directory("src", include=["**/*.py", "pyproject.toml"])  # narrow scope
        stage = SecurityStage()
        artifacts = await stage.security_scan(src)
        # Read produced files
        report_file = await artifacts.file("security-report.json").contents()
        summary_md = await artifacts.file("summary.md").contents()
        data = json.loads(report_file)
        assert "summary" in data and "findings" in data, "Report missing required keys"
        # Deterministic ordering: fingerprints sorted
        fingerprints = [f["fingerprint"] for f in data["findings"]]
        assert fingerprints == sorted(fingerprints, key=lambda x: x), "Findings not deterministically ordered"
        assert "Gate" in summary_md or "Security Summary" in summary_md
        print("✅ Security scan basic validation passed")


def main():
    print("🧪 Running Security Stage basic tests...")
    asyncio.run(run_security_scan())
    print("🎉 Tests completed")


if __name__ == "__main__":
    main()
