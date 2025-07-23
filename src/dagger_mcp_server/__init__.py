import dagger
from dagger import dag, function, object_type

@object_type
class DaggerMcpServer:
    @function
    def hello(self) -> str:
        """Returns a friendly greeting"""
        return "Hello, from Dagger MCP Server!"
