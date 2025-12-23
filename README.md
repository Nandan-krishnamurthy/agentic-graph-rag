# 🔍 Agentic Graph RAG using Neo4j

An intelligent question-answering system that converts natural language queries into Cypher queries using LLM-powered agents to retrieve information from a Neo4j knowledge graph.

## 📋 Project Overview

This project implements an **Agentic Graph RAG (Retrieval-Augmented Generation)** system that enables users to ask questions in plain English and receive accurate answers by querying a graph database. Unlike traditional keyword search or vector databases, this system understands relationships between entities and leverages graph traversal for contextual answers.

**Key Capabilities:**
- 🧠 Understands natural language questions
- 🔗 Extracts entities and their relationships
- 📊 Generates optimized Cypher queries automatically
- 💬 Returns human-readable, conversational answers
- ⚡ Real-time query execution on Neo4j Aura

## 🏗️ Architecture

```
User Question
     ↓
┌─────────────────────┐
│  Entity Extractor   │  ← Groq LLM
│  (LLaMA 3.3)        │
└─────────────────────┘
     ↓
  [Entities]
     ↓
┌─────────────────────┐
│ Cypher Generator    │  ← Groq LLM
│  (LLaMA 3.3)        │
└─────────────────────┘
     ↓
  [Cypher Query]
     ↓
┌─────────────────────┐
│   Neo4j Aura        │
│  Graph Database     │
└─────────────────────┘
     ↓
  [Raw Results]
     ↓
┌─────────────────────┐
│ Answer Formatter    │  ← Groq LLM
│  (LLaMA 3.3)        │
└─────────────────────┘
     ↓
  Human Answer
```

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

### Step-by-Step Pipeline

1. **Entity Extraction**
   - User asks: *"Who works at TechCorp Solutions?"*
   - LLM extracts entities: `[{"name": "TechCorp Solutions", "type": "Company"}]`
   - Identifies query intent: *"Find employees at TechCorp Solutions"*

2. **Cypher Query Generation**
   - LLM converts natural language + entities → Cypher query
   - Generated query:
     ```cypher
     MATCH (p:Person)-[:WORKS_AT]->(c:Company)
     WHERE toLower(c.name) = toLower('TechCorp Solutions')
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
   - Extracted entities
   - Generated Cypher query
   - Raw Neo4j results

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
│   ├── entity_extractor.py      # Extract entities from questions
│   ├── cypher_generator.py      # Generate Cypher queries
│   ├── graph_agent.py           # Main orchestration logic
│   └── answer_formatter.py      # Format results as answers
├── db/
│   └── seed_graph.py            # Database seeding script
├── app.py                        # Streamlit web interface
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🔮 Future Improvements

- [ ] Add vector similarity search for fuzzy entity matching
- [ ] Support for more complex graph patterns (multi-hop traversals)
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


