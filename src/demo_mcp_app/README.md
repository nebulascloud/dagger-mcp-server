# OpenAI + MCP Integration Demo

**Simple, production-ready implementation of OpenAI Agents with Model Context Protocol (MCP) integration.**

## Overview

This demo application showcases seamless integration between OpenAI's native MCP support and Jira through the MCP Atlassian server. It demonstrates intelligent conversation capabilities with memory across multiple interactions.

## Features

✅ **Native OpenAI + MCP Integration** - Uses openai-agents library for direct MCP communication  
🧠 **Conversation Memory** - Maintains context across queries using OpenAI Responses API  
🔄 **Automatic Resource Management** - Proper async context managers and cleanup  
🛡️ **Production Error Handling** - Comprehensive error handling and recovery  
📊 **Beautiful CLI Output** - Enhanced user interface with progress tracking  
⚡ **High Performance** - Optimized connection pooling and reuse  

## Quick Start

### Prerequisites

1. **Running MCP Atlassian Server**
   ```bash
   # Ensure your MCP server is running in Docker
   docker ps | grep practical_mclean
   ```

2. **OpenAI API Key**
   ```bash
   # Copy and configure environment
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Dependencies**
   ```bash
   pip install openai-agents python-dotenv
   ```

### Run the Demo

```bash
python3 openai_mcp_demo.py
```

## What It Demonstrates

The demo runs three intelligent queries that showcase conversation memory:

1. **"Show me issues in the MCP project"** - Retrieves current Jira issues
2. **"Based on the summary and description fields of each work item in the MCP project, suggest where dependencies should be set using linked issues"** - AI analyzes the retrieved issues and suggests dependencies
3. **"Please set the first dependency listed in your suggestions"** - AI remembers the previous suggestions and creates the actual Jira link

### Key Innovation: Conversation Context

The magic happens through OpenAI's Responses API:
```python
# First query - no context
result = await Runner.run(agent, "Show me issues")

# Second query - uses context from first
result = await Runner.run(
    agent, 
    "Analyze these issues",
    previous_response_id=result.last_response_id  # 🧠 Memory!
)
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAI Agent  │◄──►│ Optimized Client │◄──►│  MCP Atlassian  │
│  (gpt-4o-mini)  │    │   (This Demo)    │    │     Server      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
    Conversation              Resource                 Docker
       Memory               Management               Container
    (Responses API)        (Async Context)        (practical_mclean)
```

## Code Structure

```
demo_mcp_app/
├── openai_mcp_demo.py        # 🎯 Main implementation  
├── .env.example              # Configuration template
└── README.md                 # This file
```

**Single file, maximum impact!** 🚀

## Configuration Classes

### MCPConfig
```python
@dataclass
class MCPConfig:
    command: str = "docker"
    container_name: str = "practical_mclean"  
    mcp_command: str = "mcp-atlassian"
```

### AgentConfig  
```python
@dataclass
class AgentConfig:
    name: str = "jira-assistant"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Jira assistant..."
```

## Usage Examples

### Basic Usage
```python
from openai_mcp_demo import OptimizedMCPClient

client = OptimizedMCPClient()

async with client.connect():
    response = await client.query("What Jira projects do I have?")
    print(response)
```

### Conversation Context
```python
async with client.connect():
    # Build conversation context
    await client.query("Show me issues in MCP project")
    await client.query("Analyze dependencies for these issues")  # Remembers context!
    await client.query("Create the first suggested link")        # Remembers suggestions!
```

### Batch Processing
```python
async with client.connect():
    questions = ["Question 1", "Question 2", "Question 3"]
    results = await client.batch_query(questions, use_conversation_context=True)
```

## Evolution Story

This simple implementation evolved from a complex 400+ line solution to a clean, focused approach:

1. **Started with**: Complex `__init__.py` with manual JSON-RPC and custom ChatGPT function calling
2. **Experimented with**: Multiple bridge approaches and intermediate solutions  
3. **Discovered**: OpenAI's native MCP support in the openai-agents library
4. **Achieved**: Simple, powerful integration with conversation memory

**Key insight**: Sometimes the best solution is the simplest one! 💡

## Cleanup Legacy Files

If upgrading from previous versions:
```bash
./cleanup.sh  # Removes old experimental files
```

## Technical Details

### Connection Management
- Automatic MCP server connection via Docker
- Graceful async context managers
- Resource cleanup and connection pooling

### Error Handling
- Retry logic with exponential backoff
- Comprehensive error reporting
- Graceful degradation

### Conversation Context
- Uses OpenAI Responses API for memory
- Maintains conversation history
- Context-aware query processing

## License

MIT License - Feel free to use and modify!
