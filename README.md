# 🔍 Agentic Graph RAG using Neo4j

An intelligent question-answering system that uses **tool-calling architecture** where an AI agent decides when to query a Neo4j knowledge graph to answer questions.

## 📋 Project Overview

This project implements an **Agentic Graph RAG (Retrieval-Augmented Generation)** system using a **tool-calling architecture**. Unlike traditional prompt-based approaches, this system gives the AI agent a callable tool for executing Cypher queries. The agent autonomously decides when to call the tool, generates queries, receives JSON results, and formulates natural language answers.

**Key Capabilities:**
- 🤖 AI agent with tool-calling capabilities
- 🛠️ Neo4j query wrapped as a callable tool
- 🔍 Agent decides when to query the database
- 📊 Returns structured JSON results
- 💬 Agent formulates conversational answers
- ⚡ No Cypher generation in prompts
- 🔄 Multi-query support for complex questions

## 🏗️ Architecture

### Tool-Calling Architecture (New)

```
User Question
     ↓
┌──────────────────────────┐
│   Tool-Calling Agent     │
│     (Groq LLM)           │
│   - Analyzes question    │
│   - Decides to call tool │
│   - Generates Cypher     │
│   - Formulates answer    │
└──────────────────────────┘
     ↓ (Function Call)
┌──────────────────────────┐
│   Neo4j Query Tool       │
│   - Validates query      │
│   - Executes on Neo4j    │
│   - Returns JSON         │
└──────────────────────────┘
     ↓ (Query)
┌──────────────────────────┐
│      Neo4j Aura          │
│   Graph Database         │
└──────────────────────────┘
     ↓ (JSON Results)
┌──────────────────────────┐
│   Tool-Calling Agent     │
│   - Receives results     │
│   - Formats answer       │
└──────────────────────────┘
     ↓
  Natural Language Answer
```

### Benefits Over Prompt-Based Approach
- ✅ More reliable query generation (function calling vs prompting)
- ✅ Agent autonomy (decides when to query)
- ✅ Multi-query support (agent can make multiple calls)
- ✅ Better error handling
- ✅ Easier to extend with additional tools
- ✅ Cleaner separation of concerns

## 📊 Graph Schema

### Node Types
- Person (name, role)
- Company (name, industry)
- Product (name, category)

### Relationship Types
- (Person)-[:WORKS_AT]->(Company)
- (Person)-[:REPORTS_TO]->(Person)
- (Company)-[:USES]->(Product)

**Example Graph Structure:**
```cypher
(Alice:Person {role: "Engineer"})
    -[:WORKS_AT]->
(TechCorp:Company {industry: "Technology"})
    -[:USES]->
(CloudSync:Product {category: "Software"})

(Alice)-[:REPORTS_TO]->(Bob:Person {role: "Manager"})
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Graph Database** | Neo4j Aura (Cloud) |
| **LLM Provider** | Groq API |
| **LLM Model** | LLaMA 3.3 70B |
| **Backend** | Python 3.11+ |
| **Web Framework** | Streamlit |
| **LLM Framework** | LangChain (langchain-groq) |
| **Neo4j Driver** | neo4j-python-driver |
| **Environment** | python-dotenv |

## ⚙️ How It Works

### Tool-Calling Pipeline

1. **User Asks Question**
   - User asks: *"Who works at TechCorp Solutions?"*

2. **Agent Analysis**
   - AI agent receives the question
   - Analyzes if database query is needed
   - Decides to call `execute_cypher_query` tool

3. **Tool Call (Function Calling)**
   - Agent generates Cypher query:
     ```cypher
     MATCH (p:Person)-[:WORKS_AT]->(c:Company)
     WHERE toLower(c.name) = toLower('TechCorp Solutions')
     RETURN p.name, p.role
     ```
   - Calls tool with the query as parameter

4. **Query Execution**
   - Tool validates the query (security checks)
   - Executes against Neo4j database
   - Returns JSON results:
     ```json
     {
       "success": true,
       "results": [
         {"p.name": "John Smith", "p.role": "Software Engineer"},
         {"p.name": "Sarah Johnson", "p.role": "Product Manager"}
       ],
       "count": 2
     }
     ```

5. **Answer Formulation**
   - Agent receives the JSON results
   - Formulates natural language answer:
     *"At TechCorp Solutions, there are 2 employees: John Smith who works as a Software Engineer, and Sarah Johnson who works as a Product Manager."*

### Multi-Query Example

For complex questions, the agent can make multiple tool calls:

**Question:** *"Show me all employees at TechCorp and what products they use"*

**Agent's Approach:**
1. First tool call: Get employees at TechCorp
2. Second tool call: Get products used by TechCorp
3. Combine results into comprehensive answer
     RETURN p.name, p.role
     ```

3. **Neo4j Execution**
   - Query executes on Neo4j Aura cloud database
   - Returns structured results:
     ```json
     [
       {"p.name": "John Smith", "p.role": "Software Engineer"},
       {"p.name": "Jane Doe", "p.role": "Engineering Manager"}
     ]
     ```

4. **Answer Formatting**
   - LLM converts raw results → natural language
   - Final answer: *"At TechCorp Solutions, there are 2 employees: John Smith who works as a Software Engineer, and Jane Doe who works as an Engineering Manager."*

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11 or higher
- Neo4j Aura account (free tier available)
- Groq API key (free tier available)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd agentic-graph-rag
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Neo4j Aura Configuration
NEO4J_URI=neo4j+ssc://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Groq API Configuration
GROQ_API_KEY=your-groq-api-key
```

**Where to get credentials:**
- **Neo4j Aura**: Sign up at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura) (free tier)
- **Groq API**: Get your key at [console.groq.com](https://console.groq.com) (free tier)

**Note:** Use `neo4j+ssc://` URI scheme for Windows to bypass SSL certificate issues.

### 5. Seed the Database
Populate Neo4j with synthetic data (companies, people, products):
```bash
python db/seed_graph.py
```

**Expected Output:**
```
✓ Database cleared
✓ Created 5 companies
✓ Created 10 products
✓ Created 50 people
✓ Created WORKS_AT relationships
✓ Created 23 USES relationships
✓ Created 17 REPORTS_TO relationships
✓ Database seeding completed successfully!
```

## 🎯 Running the App

### Launch Streamlit Web Interface
```bash
streamlit run app.py
```

The app will open in your browser at: `http://localhost:8501`

### Using the Interface
1. Enter your question in natural language
2. Click **"🔍 Ask Question"**
3. View the answer and expand sections to see:
   - Tool calls made by the agent
   - Generated Cypher queries
   - Raw Neo4j JSON results

### Testing Individual Components

**Test Neo4j Tool:**
```bash
python -m agent.neo4j_tool
```

**Test Tool-Calling Agent:**
```bash
python -m agent.tool_calling_agent
```

**Test Complete System:**
```bash
python test_refactoring.py
```

## 💡 Sample Queries

Try these questions with the seeded data:

### Employee Queries
- *"Who works at TechCorp Solutions?"*
- *"Show me all employees in the Finance industry"*
- *"List everyone at HealthFirst Medical"*

### Product Queries
- *"What products does GreenEnergy Systems use?"*
- *"Which companies use CloudSync Pro?"*
- *"Show me all Security category products"*

### Relationship Queries
- *"Who does Emma Johnson report to?"*
- *"Show reporting relationships at RetailGiant Co"*
- *"Find all managers in the Technology industry"*

### Complex Queries
- *"What products do people at HealthFirst Medical use?"*
- *"Show me all employees and their products"*

## 📁 Project Structure

```
agentic-graph-rag/
├── agent/
│   ├── neo4j_tool.py            # [NEW] Callable Neo4j query tool
│   ├── tool_calling_agent.py    # [NEW] AI agent with tool calling
│   ├── graph_agent.py           # [REFACTORED] Uses tool-calling architecture
│   ├── entity_extractor.py      # [LEGACY] For reference
│   ├── cypher_generator.py      # [LEGACY] For reference
│   └── answer_formatter.py      # [LEGACY] For reference
├── db/
│   └── seed_graph.py            # Database seeding script
├── app.py                        # [UPDATED] Streamlit UI for tool-calling
├── test_refactoring.py          # [NEW] Test script for new architecture
├── ARCHITECTURE.md              # [NEW] Detailed architecture documentation
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🔄 Architecture Refactoring

This project has been **refactored from a prompt-based approach to a tool-calling architecture**. See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

### Key Changes:
- **Before:** Cypher queries generated in LLM prompts
- **After:** Cypher queries generated via function calling
- **Benefit:** More reliable, flexible, and maintainable

### What Changed:
1. **New:** `agent/neo4j_tool.py` - Wraps Neo4j queries as a callable tool
2. **New:** `agent/tool_calling_agent.py` - AI agent with tool calling capabilities
3. **Updated:** `agent/graph_agent.py` - Now uses tool-calling architecture
4. **Updated:** `app.py` - UI shows tool calls made by agent

### Migration:
The new architecture is **backward compatible**. The main `GraphRAGAgent.ask()` interface remains the same, so existing code continues to work.

For detailed comparison and migration guide, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🔮 Future Improvements

- [x] Tool-calling architecture for more reliable queries
- [ ] Add vector similarity search for fuzzy entity matching
- [ ] Support for more complex graph patterns (multi-hop traversals)
- [ ] Add more tools (web search, calculator, etc.)
- [ ] Multi-database support (agent chooses data source)
- [ ] Query history and caching
- [ ] User authentication and personalized graphs
- [ ] Export results to CSV/JSON
- [ ] Graph visualization in the UI
- [ ] Support for multiple LLM providers (OpenAI, Claude, etc.)
- [ ] Add unit tests and integration tests
- [ ] Deploy to cloud (Streamlit Cloud, Heroku, AWS)
- [ ] Add more entity types (Location, Skill, Project, etc.)
- [ ] Real-time graph updates and synchronization
- [ ] Natural language query suggestions

## 📝 License

This project is open source and available under the MIT License.


