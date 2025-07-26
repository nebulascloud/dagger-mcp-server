#!/usr/bin/env python3
"""
The simplest possible Dagger pipeline to test our MCP server.
"""

import subprocess
import sys

# Install dagger-io if not available
try:
    import dagger
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dagger-io"])
    import dagger

import asyncio

async def main():
    async with dagger.Connection() as client:
        # Create a simple container and test our function
        result = await (
            client.container()
            .from_("python:3.10-slim")
            .with_directory("/app", client.host().directory("."))
            .with_workdir("/app")
            .with_exec(["pip", "install", "-e", "."])
            .with_exec(["python", "-c", "from __init__ import DaggerMcpServer; print(DaggerMcpServer().hello())"])
            .stdout()
        )
        
        print(f"Result: {result.strip()}")

if __name__ == "__main__":
    asyncio.run(main())
