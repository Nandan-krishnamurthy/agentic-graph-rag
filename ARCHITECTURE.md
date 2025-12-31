# Agentic Graph RAG - Tool-Calling Architecture

## Overview

This project has been refactored from a prompt-based Cypher generation approach to a **tool-calling architecture**. This represents a significant architectural improvement that gives the AI agent more autonomy and reliability.

## Architecture Changes

### Before (Prompt-Based)
```
User Question → Entity Extraction → Cypher Generation (in prompt) → Execute Query → Format Answer
```

The old approach:
1. Extracted entities from the question
2. Generated Cypher queries using LLM with examples in prompts
3. Validated and executed the query
4. Formatted results into an answer

**Problems:**
- Cypher generation was unreliable (depended on prompt examples)
- No ability for the agent to refine queries
- Hard-coded pipeline with fixed steps
- Agent couldn't decide whether to query or not

### After (Tool-Calling)
```
User Question → AI Agent (with tool access) → Tool Calls (when needed) → JSON Results → Natural Answer
```

The new approach:
1. AI agent analyzes the question
2. Agent decides if it needs to query the database
3. Agent generates Cypher via function calling
4. Tool executes query and returns JSON results
5. Agent can make multiple queries if needed
6. Agent formulates final answer from all results

**Benefits:**
- Agent has full control over when and how to query
- Can make multiple queries to gather information
- More reliable query generation through structured function calling
- Tool returns structured JSON for easy processing
- Separation of concerns: agent logic vs. database operations
- Easier to extend with additional tools

## New Architecture Components

### 1. Neo4j Query Tool (`agent/neo4j_tool.py`)

A callable tool that wraps Neo4j database operations:

```python
class Neo4jQueryTool:
    def execute_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """Execute a Cypher query and return JSON results"""
        # Validates query
        # Executes against Neo4j
        # Returns structured results
```

**Features:**
- Query validation (prevents write operations)
- Schema enforcement (only valid labels/relationships)
- Returns JSON with success status, results, and count
- Provides tool definition for AI agent

**Tool Definition:**
```json
{
  "type": "function",
  "function": {
    "name": "execute_cypher_query",
    "description": "Execute a Cypher query against Neo4j...",
    "parameters": {
      "type": "object",
      "properties": {
        "cypher_query": {
          "type": "string",
          "description": "A valid Neo4j Cypher query..."
        }
      }
    }
  }
}
```

### 2. Tool-Calling Agent (`agent/tool_calling_agent.py`)

An AI agent that can call tools to answer questions:

```python
class ToolCallingAgent:
    def ask(self, question: str) -> Dict[str, Any]:
        """Process question using tool calling"""
        # Agent analyzes question
        # Decides if tool call is needed
        # Generates and executes queries
        # Formulates answer from results
```

**Features:**
- Uses Groq LLM with function calling
- Can make multiple tool calls per question
- Intelligent decision-making about when to query
- Natural language answer generation

**Agent Loop:**
1. Receive user question
2. LLM analyzes and decides action
3. If tool call needed → execute tool → add results to context
4. Continue until LLM provides final answer
5. Return answer with full trace of tool calls

### 3. Updated Graph Agent (`agent/graph_agent.py`)

The main interface now uses the tool-calling architecture:

```python
class GraphRAGAgent:
    def __init__(self, ...):
        self.neo4j_tool = Neo4jQueryTool(self.driver)
        self.agent = ToolCallingAgent(self.neo4j_tool)
    
    def ask(self, question: str) -> Dict[str, Any]:
        """Ask question using tool-calling agent"""
        return self.agent.ask(question)
```

**Changes:**
- Removed: EntityExtractor, CypherGenerator, AnswerFormatter
- Added: Neo4jQueryTool, ToolCallingAgent
- Simpler initialization
- Backward compatible return format

## Comparison: Old vs New

### Old Approach (Prompt-Based Cypher Generation)

**Code Flow:**
```python
# Step 1: Extract entities
entities = entity_extractor.extract(question)

# Step 2: Generate Cypher from entities and prompt examples
cypher = cypher_generator.generate(question, entities)

# Step 3: Execute query
results = execute_query(cypher)

# Step 4: Format answer
answer = answer_formatter.format(question, results)
```

**Limitations:**
- Fixed pipeline (can't adapt)
- Cypher generation depends on prompt examples
- No multi-query capability
- Hard to debug failures

### New Approach (Tool-Calling)

**Code Flow:**
```python
# Agent decides everything
result = agent.ask(question)

# Internally:
# - Agent analyzes question
# - Decides if database query needed
# - Generates Cypher via function calling
# - Executes through tool
# - Can make multiple queries
# - Formulates final answer
```

**Advantages:**
- Flexible, adaptive pipeline
- Agent decides when to query
- Structured function calling (more reliable)
- Multi-query support
- Easy to add new tools
- Better error handling

## Usage Examples

### Basic Usage

```python
from agent.graph_agent import GraphRAGAgent

# Initialize agent (same as before)
agent = GraphRAGAgent()

# Ask a question (same interface)
result = agent.ask("Who works at TechCorp Solutions?")

# Access results
print(result['answer'])  # Natural language answer
print(result['tool_calls'])  # List of tool calls made
print(result['raw_results'])  # Combined JSON results
```

### Detailed Usage

```python
# Ask with verbose output
result = agent.ask("Who works at TechCorp?", verbose=True)

# Result structure
{
    'question': 'Who works at TechCorp?',
    'answer': 'John Smith works at TechCorp as an Engineer...',
    'tool_calls': [
        {
            'function': 'execute_cypher_query',
            'query': 'MATCH (p:Person)-[:WORKS_AT]->(c:Company)...',
            'success': True,
            'count': 5
        }
    ],
    'raw_results': [
        {'p.name': 'John Smith', 'p.role': 'Engineer'},
        {'p.name': 'Jane Doe', 'p.role': 'Manager'}
    ],
    'success': True,
    'error': None
}
```

### Testing Individual Components

**Test the Neo4j Tool:**
```bash
cd c:\agentic-graph-rag
python -m agent.neo4j_tool
```

**Test the Tool-Calling Agent:**
```bash
python -m agent.tool_calling_agent
```

**Test the Full System:**
```bash
python -m agent.graph_agent
```

## Migration Guide

### For Developers

If you were using the old components:

**Before:**
```python
from agent.entity_extractor import EntityExtractor
from agent.cypher_generator import CypherGenerator
from agent.answer_formatter import AnswerFormatter

# These are now deprecated
```

**After:**
```python
from agent.neo4j_tool import Neo4jQueryTool
from agent.tool_calling_agent import ToolCallingAgent

# Use GraphRAGAgent for the complete system
from agent.graph_agent import GraphRAGAgent
```

### API Compatibility

The main `GraphRAGAgent.ask()` method maintains backward compatibility:

```python
# Old code still works
result = agent.ask("Who works at TechCorp?")
print(result['answer'])  # ✓ Still works
print(result['cypher_query'])  # ✓ Still works (first query)
print(result['raw_results'])  # ✓ Still works

# New fields available
print(result['tool_calls'])  # ✓ New: List of all tool calls
```

## Configuration

### Environment Variables

No changes to environment variables needed:

```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
GROQ_API_KEY=your-groq-api-key
```

### Model Selection

The tool-calling agent uses Groq's function-calling capable models:

```python
# Default model (recommended)
agent = GraphRAGAgent(model="llama-3.3-70b-versatile")

# The model must support function calling
```

## Advanced Features

### Multi-Query Support

The agent can now make multiple queries to gather information:

```python
# Question requiring multiple queries
result = agent.ask("Show me all employees at TechCorp and what products they use")

# The agent might:
# 1. First query: Get all employees at TechCorp
# 2. Second query: Get products used by the company
# 3. Combine results into final answer
```

### Error Handling

Better error handling with detailed feedback:

```python
result = agent.ask("Invalid question")

if not result['success']:
    print(f"Error: {result['error']}")
    print(f"Tool calls attempted: {result['tool_calls']}")
```

### Adding New Tools

Easy to extend with additional tools:

```python
# Define a new tool
class MyCustomTool:
    def execute(self, param: str) -> Dict:
        # Tool logic here
        pass
    
    @staticmethod
    def get_tool_definition() -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "my_custom_tool",
                "description": "What this tool does",
                "parameters": {...}
            }
        }

# Add to agent
tools = [
    neo4j_tool.get_tool_definition(),
    MyCustomTool.get_tool_definition()
]
```

## Benefits of Refactoring

### 1. **Reliability**
- Structured function calling vs. prompt engineering
- Better query generation success rate
- Clear error messages

### 2. **Flexibility**
- Agent can decide when to query
- Multi-query support
- Adaptive to different question types

### 3. **Maintainability**
- Separation of concerns (agent vs. tool)
- Easy to add new tools
- Clear data flow

### 4. **Debuggability**
- Full trace of tool calls
- Structured result format
- Better error information

### 5. **Extensibility**
- Simple to add new tools (web search, calculator, etc.)
- Can combine multiple data sources
- Agent-based architecture scales well

## Testing

### Run All Tests

```bash
# Test Neo4j tool
python agent\neo4j_tool.py

# Test tool-calling agent
python agent\tool_calling_agent.py

# Test full system
python agent\graph_agent.py

# Run Streamlit app
streamlit run app.py
```

### Expected Output

When testing, you should see:
1. Tool definitions printed
2. Example queries executed
3. JSON results returned
4. Natural language answers generated

## Troubleshooting

### Issue: "Tool calls not working"
**Solution:** Ensure you're using a function-calling capable model:
```python
model="llama-3.3-70b-versatile"  # ✓ Supports function calling
```

### Issue: "No results returned"
**Check:**
1. Neo4j connection is working
2. Database has data (`agent.get_statistics()`)
3. Query syntax is correct (check tool_calls in result)

### Issue: "Invalid Cypher query"
**The tool validates queries automatically:**
- Only MATCH and RETURN allowed
- Only valid labels (Person, Company, Product)
- Only valid relationships (WORKS_AT, REPORTS_TO, USES)

## Future Enhancements

Possible extensions with this architecture:

1. **Additional Tools:**
   - Web search tool for external data
   - Calculator tool for computations
   - Document retrieval tool for context

2. **Multi-Database:**
   - Add tools for multiple databases
   - Agent chooses appropriate data source

3. **Tool Chaining:**
   - Agent can chain tool calls
   - Complex multi-step operations

4. **Caching:**
   - Cache frequent queries
   - Improve response time

5. **Analytics:**
   - Track which queries are most common
   - Optimize based on usage patterns

## Conclusion

The tool-calling architecture represents a significant improvement over prompt-based Cypher generation:

- ✅ More reliable query generation
- ✅ Agent autonomy and flexibility
- ✅ Better error handling
- ✅ Easier to extend
- ✅ Cleaner code architecture

The refactoring maintains backward compatibility while opening up new possibilities for future enhancements.

---

**Questions or Issues?**
Check the individual module documentation in:
- `agent/neo4j_tool.py`
- `agent/tool_calling_agent.py`
- `agent/graph_agent.py`
