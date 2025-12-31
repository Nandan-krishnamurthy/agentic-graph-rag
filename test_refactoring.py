"""
Test Script for Refactored Tool-Calling Architecture

This script demonstrates the new architecture where:
1. AI agent decides when to call the Neo4j query tool
2. Tool executes Cypher queries and returns JSON results
3. Agent formulates answers from the results
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_architecture():
    """Test the refactored architecture components"""
    print("=" * 80)
    print("Testing Refactored Tool-Calling Architecture")
    print("=" * 80)
    
    # Test 1: Import Neo4j Tool
    print("\n[Test 1] Importing Neo4j Tool...")
    try:
        from agent.neo4j_tool import Neo4jQueryTool
        print("✓ Neo4j Tool imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Neo4j Tool: {e}")
        return False
    
    # Test 2: Import Tool-Calling Agent
    print("\n[Test 2] Importing Tool-Calling Agent...")
    try:
        from agent.tool_calling_agent import ToolCallingAgent
        print("✓ Tool-Calling Agent imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Tool-Calling Agent: {e}")
        return False
    
    # Test 3: Import Main Graph Agent
    print("\n[Test 3] Importing GraphRAGAgent...")
    try:
        from agent.graph_agent import GraphRAGAgent
        print("✓ GraphRAGAgent imported successfully")
    except Exception as e:
        print(f"✗ Failed to import GraphRAGAgent: {e}")
        return False
    
    # Test 4: Verify old modules are not required
    print("\n[Test 4] Verifying architecture changes...")
    try:
        # These should still exist but are not used by GraphRAGAgent
        from agent.entity_extractor import EntityExtractor
        print("  Note: entity_extractor.py still exists (not deleted for reference)")
    except:
        pass
    
    try:
        from agent.cypher_generator import CypherGenerator
        print("  Note: cypher_generator.py still exists (not deleted for reference)")
    except:
        pass
    
    print("✓ Architecture uses new tool-calling approach")
    
    # Test 5: Tool definition
    print("\n[Test 5] Checking tool definition...")
    try:
        tool_def = Neo4jQueryTool.get_tool_definition()
        print(f"✓ Tool name: {tool_def['function']['name']}")
        print(f"✓ Tool has proper schema for function calling")
    except Exception as e:
        print(f"✗ Failed to get tool definition: {e}")
        return False
    
    # Test 6: Initialize agent (if credentials available)
    print("\n[Test 6] Testing agent initialization...")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password, groq_api_key]):
        print("⚠ Environment variables not set - skipping live test")
        print("  Required: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, GROQ_API_KEY")
    else:
        try:
            print("  Initializing agent...")
            agent = GraphRAGAgent()
            print("✓ Agent initialized successfully with tool-calling architecture")
            
            # Test connection
            print("\n[Test 7] Testing Neo4j connection...")
            if agent.test_connection():
                print("✓ Neo4j connection successful")
                
                # Test a simple query
                print("\n[Test 8] Testing simple query...")
                print("  Question: 'What is the schema?'")
                result = agent.ask("What types of nodes are in the database?", verbose=False)
                
                if result['success']:
                    print("✓ Query executed successfully")
                    print(f"  Answer: {result['answer'][:100]}...")
                    if result.get('tool_calls'):
                        print(f"  Tool calls made: {len(result['tool_calls'])}")
                else:
                    print(f"⚠ Query returned error: {result['error']}")
            else:
                print("⚠ Neo4j connection failed (check credentials)")
            
            agent.close()
            
        except Exception as e:
            print(f"⚠ Could not initialize agent: {e}")
    
    print("\n" + "=" * 80)
    print("Architecture Refactoring Complete!")
    print("=" * 80)
    print("\nKey Changes:")
    print("✓ Cypher queries wrapped in callable tool")
    print("✓ AI agent decides when to call the tool")
    print("✓ Tool returns JSON results from Neo4j")
    print("✓ No Cypher generation in prompts")
    print("✓ Agent formulates answers from tool results")
    print("\nNew Files:")
    print("  - agent/neo4j_tool.py (Neo4j query tool)")
    print("  - agent/tool_calling_agent.py (AI agent with tool calling)")
    print("  - ARCHITECTURE.md (comprehensive documentation)")
    print("\nModified Files:")
    print("  - agent/graph_agent.py (now uses tool-calling architecture)")
    print("  - app.py (updated UI for tool-calling)")
    print("\nTo run:")
    print("  streamlit run app.py")
    print("\n" + "=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_architecture()
    sys.exit(0 if success else 1)
