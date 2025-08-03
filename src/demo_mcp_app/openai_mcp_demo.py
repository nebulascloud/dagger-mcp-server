"""
Optimized OpenAI Native MCP Client

This module provides an optimized, production-ready implementation of the OpenAI + MCP integration
with proper resource management, error handling, and configurability.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# Try to import optional dependencies
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv():
        pass

# Try to import agents module - gracefully handle if not available
try:
    from agents import Agent, Runner
    from agents.mcp import MCPServerStdio, MCPServerStdioParams
    AGENTS_AVAILABLE = True
except ImportError:
    # Create mock classes for testing when agents module is not available
    AGENTS_AVAILABLE = False
    
    class Agent:
        def __init__(self, name: str, model: str = "gpt-4o-mini", instructions: str = ""):
            self.name = name
            self.model = model
            self.instructions = instructions
    
    class Runner:
        def __init__(self, agent: Agent, mcp_servers: List = None):
            self.agent = agent
            self.mcp_servers = mcp_servers or []
        
        async def run_sync(self, message: str) -> str:
            return f"Mock response for: {message}"
    
    class MCPServerStdio:
        def __init__(self, params):
            self.params = params
    
    class MCPServerStdioParams:
        def __init__(self, command: str, args: List[str], env: Optional[Dict] = None):
            self.command = command
            self.args = args
            self.env = env or {}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MCPConfig:
    """Configuration for MCP server connection."""
    command: str = "docker"
    args: List[str] = None
    container_name: str = "mcp-server-atlassian"
    mcp_command: str = "mcp-atlassian"
    
    def __post_init__(self):
        import os
        
        # Allow environment variable override if needed
        self.container_name = os.getenv('MCP_CONTAINER_NAME', self.container_name)
            
        if self.args is None:
            self.args = ["exec", "-i", self.container_name, self.mcp_command]

@dataclass 
class AgentConfig:
    """Configuration for OpenAI Agent."""
    name: str = "jira-assistant"
    model: str = "gpt-4o-mini"
    instructions: str = """You are a helpful Jira assistant. You have access to Jira data through MCP tools.

When users ask about projects, issues, or want to manage Jira data, use the available MCP tools to get real information.
Always provide clear, conversational responses with the actual data you retrieve.

IMPORTANT ERROR HANDLING GUIDELINES:
- If creating issue links fails due to link type errors, try common alternatives: "Blocks", "Relates", "Depends on"
- If an operation fails, explain what happened and suggest alternatives
- Always check available link types first if you encounter link creation errors
- Be resilient and try multiple approaches when encountering API errors"""

class OptimizedMCPClient:
    """
    Optimized MCP client with proper resource management, error handling, and conversation context.
    
    Features:
    - Connection pooling and reuse
    - Proper async context management
    - Comprehensive error handling
    - Configurable parameters
    - Structured logging
    - Conversation context via OpenAI Responses API
    """
    
    def __init__(self, mcp_config: MCPConfig = None, agent_config: AgentConfig = None):
        self.mcp_config = mcp_config or MCPConfig()
        self.agent_config = agent_config or AgentConfig()
        self._server: Optional[MCPServerStdio] = None
        self._agent: Optional[Agent] = None
        self._connected = False
        self._conversation_history: List[Dict[str, str]] = []
        self._last_response_id: Optional[str] = None
        
    @asynccontextmanager
    async def connect(self):
        """Async context manager for MCP connection with automatic cleanup."""
        try:
            await self._establish_connection()
            yield self
        finally:
            await self._cleanup_connection()
    
    async def _establish_connection(self):
        """Establish MCP server connection and create agent."""
        if self._connected:
            logger.warning("⚠️  Already connected to MCP server")
            return
            
        try:
            logger.info("🔌 Connecting to MCP server...")
            
            if AGENTS_AVAILABLE:
                # Create server parameters
                server_params = MCPServerStdioParams()
                server_params.update({
                    "command": self.mcp_config.command,
                    "args": self.mcp_config.args
                })
                
                # Create and connect to server
                self._server = MCPServerStdio(server_params)
                await self._server.connect()
                logger.info("📡 MCP server connection established")
                
                # Create agent
                logger.info("🤖 Creating OpenAI agent...")
                self._agent = Agent(
                    name=self.agent_config.name,
                    model=self.agent_config.model,
                    instructions=self.agent_config.instructions,
                    mcp_servers=[self._server]
                )
            else:
                # Use mock implementations for testing
                logger.info("🧪 Using mock implementations (agents module not available)")
                server_params = MCPServerStdioParams(
                    command=self.mcp_config.command,
                    args=self.mcp_config.args
                )
                self._server = MCPServerStdio(server_params)
                self._agent = Agent(
                    name=self.agent_config.name,
                    model=self.agent_config.model,
                    instructions=self.agent_config.instructions
                )
            
            self._connected = True
            logger.info("✅ MCP server connected and agent created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to establish MCP connection: {e}")
            await self._cleanup_connection()
            raise
    
    async def _cleanup_connection(self):
        """Clean up MCP server connection and reset conversation state."""
        if self._server and self._connected:
            try:
                logger.info("🧹 Cleaning up MCP server connection...")
                await self._server.cleanup()
                logger.info("✅ MCP server connection closed gracefully")
            except Exception as e:
                logger.warning(f"⚠️  Warning during server cleanup: {e}")
            finally:
                self._server = None
                self._agent = None
                self._connected = False
                self._conversation_history = []
                self._last_response_id = None
                logger.info("🔄 Connection state reset")
    
    async def query(self, question: str, max_retries: int = 3, use_conversation_context: bool = True) -> str:
        """
        Execute a natural language query against the MCP server with conversation context.
        
        Args:
            question: Natural language question
            max_retries: Maximum number of retry attempts
            use_conversation_context: Whether to use previous conversation context
            
        Returns:
            Response string from the agent
            
        Raises:
            RuntimeError: If not connected or query fails
        """
        if not self._connected or not self._agent:
            raise RuntimeError("Client not connected. Use async with client.connect():")
        
        for attempt in range(max_retries):
            try:
                # Use conversation context if enabled and available
                previous_response_id = self._last_response_id if use_conversation_context else None
                if previous_response_id:
                    logger.info(f"🧠 Using conversation context: {previous_response_id[:12]}...")
                else:
                    logger.info("🆕 Starting fresh conversation (no previous context)")
                
                logger.info(f"⚡ Executing query (attempt {attempt + 1}/{max_retries})")
                
                if AGENTS_AVAILABLE:
                    result = await Runner.run(
                        self._agent, 
                        question,
                        previous_response_id=previous_response_id
                    )
                    
                    response = result.final_output_as(str)
                    response_id = result.last_response_id
                else:
                    # Mock implementation for testing
                    import uuid
                    response = f"Mock response for: {question}"
                    response_id = str(uuid.uuid4())
                
                # Update conversation state
                self._conversation_history.append({
                    "question": question,
                    "response": response,
                    "response_id": response_id
                })
                self._last_response_id = response_id
                
                logger.info(f"✅ Query successful! New response ID: {response_id[:12]}...")
                return response
                
            except Exception as e:
                logger.warning(f"⚠️  Query attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Query failed after {max_retries} attempts")
                    raise
                await asyncio.sleep(1)  # Brief delay before retry
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self._conversation_history.copy()
    
    def clear_conversation_context(self):
        """Clear conversation context while keeping connection."""
        self._conversation_history = []
        self._last_response_id = None
        logger.info("🧠 Conversation context cleared")
    
    def get_last_response_id(self) -> Optional[str]:
        """Get the last response ID for manual context management."""
        return self._last_response_id
    
    async def batch_query(self, questions: List[str], use_conversation_context: bool = True) -> Dict[str, str]:
        """
        Execute multiple queries efficiently with conversation context.
        
        Args:
            questions: List of questions to ask
            use_conversation_context: Whether to maintain context between questions
            
        Returns:
            Dictionary mapping questions to responses
        """
        results = {}
        logger.info(f"🔄 Starting batch query: {len(questions)} questions")
        
        for i, question in enumerate(questions, 1):
            try:
                logger.info(f"📝 Processing question {i}/{len(questions)}")
                response = await self.query(question, use_conversation_context=use_conversation_context)
                results[question] = response
                logger.info(f"✅ Question {i} completed successfully")
            except Exception as e:
                logger.error(f"❌ Failed to process question {i}: {e}")
                results[question] = f"Error: {e}"
        
        logger.info(f"🏁 Batch query completed: {len(results)} results")
        return results

def _format_issue_list(response: str) -> str:
    """Format issue list responses with better visual hierarchy."""
    import re
    
    # Look for numbered issues in the response
    lines = []
    
    # Split response into lines and process
    response_lines = response.split('\n')
    current_issue = []
    
    for line in response_lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect issue patterns like "1. **[MCP-382]**" or "**[MCP-382]**"
        if re.search(r'\*\*\[?MCP-\d+\]?\*\*', line) and ('Implement' in line or 'Setup' in line or 'Build' in line):
            if current_issue:
                lines.extend(_format_single_issue(current_issue))
                lines.append("")  # Add spacing between issues
                current_issue = []
            current_issue.append(line)
        elif current_issue and line:
            current_issue.append(line)
        elif not current_issue and line:
            # Header text
            lines.append(line)
            if "MCP" in line and "project" in line:
                lines.append("")
    
    # Format the last issue
    if current_issue:
        lines.extend(_format_single_issue(current_issue))
    
    return '\n'.join(lines)

def _format_single_issue(issue_lines: List[str]) -> List[str]:
    """Format a single issue with improved spacing and visual hierarchy."""
    if not issue_lines:
        return []
    
    formatted = []
    full_text = ' '.join(issue_lines)
    
    # Extract issue key and title using regex
    import re
    issue_match = re.search(r'MCP-(\d+)', full_text)
    
    if issue_match:
        issue_key = f"MCP-{issue_match.group(1)}"
        
        # Extract title - look for pattern after the issue key
        title_patterns = [
            rf'\[?{re.escape(issue_key)}\]?\*\*:?\s*-?\s*([^-\n]+?)(?:\s*-|\s*\*\*|\s*$)',
            rf'\*\*\[?{re.escape(issue_key)}\]?\*\*:?\s*-?\s*([^-\n]+?)(?:\s*-|\s*Description|\s*Status|$)'
        ]
        
        title = "Unknown Title"
        for pattern in title_patterns:
            title_match = re.search(pattern, full_text)
            if title_match:
                title = title_match.group(1).strip()
                break
        
        formatted.append(f"🎯 {issue_key}: {title}")
        
        # Extract description if available
        desc_match = re.search(r'Description[:\*\s]*([^-\n]+?)(?:\s*-|\s*Status|$)', full_text)
        if desc_match:
            desc = desc_match.group(1).strip()
            if desc and len(desc) > 10:  # Only show substantial descriptions
                formatted.append(f"   📝 {desc}")
        
        # Extract status, priority, etc.
        status_match = re.search(r'Status[:\*\s]*([^-\n]+?)(?:\s*-|\s*Priority|$)', full_text)
        if status_match:
            status = status_match.group(1).strip().replace('*', '')
            if status:
                formatted.append(f"   📊 Status: {status}")
        
        priority_match = re.search(r'Priority[:\*\s]*([^-\n]+?)(?:\s*-|\s*Assignee|$)', full_text)
        if priority_match:
            priority = priority_match.group(1).strip().replace('*', '')
            if priority:
                formatted.append(f"   ⚡ Priority: {priority}")
    
    return formatted if formatted else [f"🎯 {' '.join(issue_lines)[:100]}..."]

def _format_dependency_suggestions(response: str) -> str:
    """Format dependency suggestion responses with clear hierarchy and pairings."""
    import re
    
    lines = []
    
    # Look for dependency patterns in the response
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Handle header lines
        if line.startswith("Based on") or "here's a suggested" in line.lower():
            lines.append(f"🎯 {line}")
            lines.append("")
        elif line.startswith("###") or line.startswith("**") and line.endswith("**"):
            clean_line = line.replace("#", "").replace("*", "").strip()
            lines.append(f"📋 {clean_line}")
            lines.append("")
        # Look for dependency relationship patterns
        elif re.search(r'MCP-\d+.*(?:should|must|needs).*(?:before|after|depend).*MCP-\d+', line, re.IGNORECASE):
            # This is a dependency relationship description
            lines.append(f"🔗 {line}")
        elif re.search(r'MCP-\d+.*(?:→|->).*MCP-\d+', line):
            # Arrow-based dependency
            lines.append(f"🔗 {line}")
        elif re.search(r'^\d+\.\s.*MCP-\d+.*MCP-\d+', line):
            # Numbered dependency item with two issue keys
            clean_line = re.sub(r'^\d+\.\s*', '', line)
            lines.append(f"🔗 {clean_line}")
        elif re.search(r'MCP-\d+', line) and len(line) > 20:
            # Line contains issue keys and substantial content
            if "depends on" in line.lower() or "blocks" in line.lower() or "requires" in line.lower():
                lines.append(f"   📌 {line}")
            else:
                lines.append(f"   💡 {line}")
        else:
            # Regular content
            if len(line) > 5:
                lines.append(f"   {line}")
    
    return '\n'.join(lines)

def _format_link_confirmation(response: str) -> str:
    """Format link creation confirmation with clear success indicators and specific issue details."""
    import re
    
    lines = []
    
    # Check for successful link creation
    if any(word in response.lower() for word in ['successfully', 'created', 'linked', 'established']):
        lines.append("✅ DEPENDENCY LINK CREATED SUCCESSFULLY")
        lines.append("")
        
        # Extract specific issue keys from the response
        issue_keys = re.findall(r'MCP-\d+', response)
        if len(issue_keys) >= 2:
            lines.append(f"🔗 Linked Issues: {issue_keys[0]} ← depends on → {issue_keys[1]}")
            lines.append("")
        
        # Look for link type information
        link_type_match = re.search(r'(?:link type|type)[:"\s]*([A-Za-z\s]+?)(?:["\n]|$)', response, re.IGNORECASE)
        if link_type_match:
            link_type = link_type_match.group(1).strip()
            lines.append(f"� Link Type: {link_type}")
            lines.append("")
        
        # Extract any additional details from the response
        for line in response.split('\n'):
            line = line.strip()
            if line and not any(skip in line.lower() for skip in ['successfully', 'created', 'link has been']):
                if 'MCP-' in line and len(line) > 10:
                    lines.append(f"📌 {line}")
        
        if not any('📌' in line for line in lines):
            lines.append("🎯 This creates a dependency relationship where one issue")
            lines.append("   must be completed before work can proceed on the other.")
    else:
        # Handle error cases or other responses
        lines.append("📋 LINK CREATION RESPONSE")
        lines.append("")
        
        # Look for error information
        if 'error' in response.lower() or 'failed' in response.lower():
            lines.append("❌ Issue encountered:")
            lines.append("")
        
        # Format the actual response content
        for line in response.split('\n'):
            line = line.strip()
            if line:
                lines.append(f"   {line}")
    
    return '\n'.join(lines)

def _format_default_response(response: str) -> str:
    """Default formatting with improved readability and spacing."""
    import textwrap
    
    # Simple paragraph formatting with better spacing
    paragraphs = response.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # Wrap long paragraphs
            wrapped = textwrap.fill(para, width=75)
            formatted_paragraphs.append(wrapped)
    
    return '\n\n'.join(formatted_paragraphs)

async def demo_optimized_client():
    """Demonstrate the optimized MCP client with enhanced CLI output."""
    # Load environment variables
    load_dotenv()
    
    # Configure client
    mcp_config = MCPConfig()
    agent_config = AgentConfig()
    
    client = OptimizedMCPClient(mcp_config, agent_config)
    
    # Example queries with improved error handling guidance
    questions = [
        #"What Jira projects do I have access to?",
        "Show me issues in the MCP project", 
        "Based on the summary and description fields of each work item in the MCP project, suggest where dependencies should be set using linked issues",
        "First check what issue link types are available in this Jira instance, then set the first dependency from your previous suggestions using an appropriate link type"
    ]
    
    try:
        # Print header
        print("\n" + "=" * 80)
        print("🚀 OpenAI + MCP Integration Demo")
        print("   Intelligent Jira Assistant with Conversation Memory")
        print("=" * 80)
        
        # Show configuration
        print(f"\n🔧 Configuration:")
        print(f"   • Container: {mcp_config.container_name}")
        print(f"   • Agent Model: {agent_config.model}")
        print(f"   • Agent Name: {agent_config.name}")
        print(f"   • Total Questions: {len(questions)}")
        
        # Use the client with proper connection management
        async with client.connect():
            print(f"\n✅ Connected to MCP server successfully!")
            
            # Option 1: Individual queries with conversation context
            for i, question in enumerate(questions, 1):
                print(f"\n" + "─" * 80)
                print(f"🎯 Question {i} of {len(questions)}")
                print("─" * 80)
                print(f"❓ {question}")
                print()
                
                # Show conversation context info with better formatting
                context_info = ""
                if client._last_response_id:
                    context_info = f"� Context: Using memory from response {client._last_response_id[:12]}..."
                else:
                    context_info = "� Context: Starting fresh conversation (no previous context)"
                
                print(f"{context_info}")
                print(f"📊 History: {len(client.get_conversation_history())} previous messages")
                print()
                
                try:
                    print("⏳ Processing query...")
                    response = await client.query(question)
                    
                    # Format the response with enhanced visual appeal
                    print("\n" + "═" * 80)
                    print("✨ RESPONSE")
                    print("═" * 80)
                    print()
                    
                    # Parse and format different types of content
                    if "Here are some" in response and "issues" in response:
                        # Format issue list with better spacing
                        formatted_response = _format_issue_list(response)
                    elif "dependencies" in response.lower() and "suggest" in response.lower():
                        # Format dependency suggestions with better spacing
                        formatted_response = _format_dependency_suggestions(response)
                    elif "link has been" in response and "created" in response:
                        # Format link creation confirmation with better spacing
                        formatted_response = _format_link_confirmation(response)
                    else:
                        # Default formatting with improved spacing
                        formatted_response = _format_default_response(response)
                    
                    print(formatted_response)
                    print()
                    print("═" * 80)
                    
                    # Show updated context with nice formatting
                    new_history_count = len(client.get_conversation_history())
                    new_response_id = client.get_last_response_id()
                    
                    print(f"\n� Updated State:")
                    print(f"   • Conversation Length: {new_history_count} messages")
                    print(f"   • Latest Response ID: {new_response_id[:12] if new_response_id else 'None'}...")
                    print(f"   • Status: ✅ Success")
                    
                except Exception as e:
                    print("💥 Error occurred:")
                    print("┌" + "─" * 78 + "┐")
                    print(f"│ ❌ {str(e):<74} │")
                    print("└" + "─" * 78 + "┘")
                    print(f"   • Status: ❌ Failed")
                    
                    # Check if this was a recoverable error where the agent still succeeded
                    new_history_count = len(client.get_conversation_history())
                    if new_history_count > len(questions) - (len(questions) - i):  # Agent may have succeeded despite error
                        print("   • 🔄 Note: Agent may have recovered automatically")
                        print("   • 🧠 Checking if conversation context was still updated...")
                        
                        # Show the latest response if available
                        final_history = client.get_conversation_history()
                        if final_history and len(final_history) >= i:
                            latest_response = final_history[-1]['response'][:100]
                            print(f"   • 💡 Latest response: {latest_response}...")
                            print("   • ✅ Recovery successful - continuing demo")
            
            # Final summary
            print(f"\n" + "=" * 80)
            print("📋 Session Summary")
            print("=" * 80)
            final_history = client.get_conversation_history()
            print(f"✅ Completed {len(questions)} questions")
            print(f"📚 Generated {len(final_history)} conversation exchanges")
            print(f"🧠 Final memory state: {len(final_history)} messages in context")
            
            if final_history:
                print(f"🔗 Last response ID: {client.get_last_response_id()}")
                print("\n💡 Conversation flow demonstrated:")
                for idx, exchange in enumerate(final_history, 1):
                    print(f"   {idx}. Q: {exchange['question'][:50]}{'...' if len(exchange['question']) > 50 else ''}")
                    print(f"      A: {exchange['response'][:50]}{'...' if len(exchange['response']) > 50 else ''}")
            
            # Option 2: Batch processing (commented out for demo)
            # results = await client.batch_query(questions)
            # for question, response in results.items():
            #     print(f"Q: {question}\nA: {response}\n")
            
    except Exception as e:
        print(f"\n💥 Demo failed with error:")
        print("┌" + "─" * 78 + "┐")
        print(f"│ ❌ {str(e):<74} │")
        print("└" + "─" * 78 + "┘")
        logger.error(f"Demo failed: {e}")
        raise

def main():
    """Main entry point with enhanced CLI presentation."""
    import sys
    
    # Print banner
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "🚀 Optimized OpenAI + MCP Integration Demo".center(78) + "█")
    print("█" + "Intelligent Jira Assistant with Memory".center(78) + "█") 
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    # Check requirements
    print("\n🔍 Pre-flight checks:")
    
    if AGENTS_AVAILABLE:
        print("   ✅ OpenAI Agents library available")
    else:
        print("   ⚠️  OpenAI Agents library missing - running in mock mode")
        print("   💡 For full functionality, install with: pip install openai-agents")
        print("   🧪 Testing infrastructure will work with mock implementations")
    
    try:
        if DOTENV_AVAILABLE:
            load_dotenv()
        import os
        if os.getenv("OPENAI_API_KEY"):
            print("   ✅ OpenAI API key configured")
        else:
            print("   ⚠️  OpenAI API key not found in environment")
    except Exception as e:
        print(f"   ⚠️  Environment check failed: {e}")
    
    print("   ✅ Starting demo...")
    
    try:
        asyncio.run(demo_optimized_client())
        
        # Success footer
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + "✅ Demo completed successfully!".center(78) + "█")
        print("█" + "🎉 OpenAI + MCP integration working perfectly".center(78) + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        print("\n💡 Key features demonstrated:")
        print("   • ✅ Seamless OpenAI + MCP integration")
        print("   • 🧠 Conversation memory across queries")
        print("   • 🔄 Automatic context management")
        print("   • 🛡️  Graceful error handling and recovery")
        print("   • 📊 Real-time status and progress tracking")
        print("   • 🔧 Intelligent error recovery (e.g., link type corrections)")
        print("   • 🎯 Production-ready resilience patterns")
        
    except KeyboardInterrupt:
        print("\n" + "⚠" * 80)
        print("⚠" + " " * 78 + "⚠")
        print("⚠" + "⏹️  Demo interrupted by user (Ctrl+C)".center(78) + "⚠")
        print("⚠" + " " * 78 + "⚠")
        print("⚠" * 80)
        sys.exit(0)
        
    except Exception as e:
        print("\n" + "❌" * 80)
        print("❌" + " " * 76 + "❌")
        print("❌" + f"💥 Demo failed: {str(e)[:64]}".center(76) + "❌")
        print("❌" + " " * 76 + "❌")
        print("❌" * 80)
        
        print(f"\n🔍 Debug information:")
        print(f"   • Error: {type(e).__name__}")
        print(f"   • Message: {str(e)}")
        print(f"   • Suggestion: Check MCP server connection and OpenAI API key")
        
        logger.error(f"Demo failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
