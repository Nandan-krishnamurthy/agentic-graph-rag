"""
Graph RAG Agent Module

Main orchestration module for the Agentic Graph RAG system.
Uses tool-calling approach where AI agent decides when to query Neo4j.
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from neo4j import GraphDatabase

from agent.neo4j_tool import Neo4jQueryTool
from agent.tool_calling_agent import ToolCallingAgent


class GraphRAGAgent:
    """
    Agentic Graph RAG (Retrieval-Augmented Generation) System.
    
    Uses a tool-calling approach where the AI agent decides when to query
    the Neo4j database using a callable tool.
    
    Architecture:
    1. User asks a question
    2. AI agent decides if it needs to query the database
    3. Agent generates Cypher query through tool calling
    4. Tool executes query and returns JSON results
    5. Agent formulates natural language answer from results
    
    This approach eliminates Cypher generation in prompts and gives the
    agent more control over the query process.
    """
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Initialize the Graph RAG Agent with tool-calling architecture.
        
        Args:
            neo4j_uri: Neo4j connection URI (defaults to NEO4J_URI env var)
            neo4j_user: Neo4j username (defaults to NEO4J_USER env var)
            neo4j_password: Neo4j password (defaults to NEO4J_PASSWORD env var)
            groq_api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: LLM model to use for the agent
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize Neo4j connection
        uri = neo4j_uri or os.getenv("NEO4J_URI")
        username = neo4j_user or os.getenv("NEO4J_USER")
        password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            raise ValueError("Neo4j credentials not provided. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        
        # Initialize Neo4j driver - SSL is auto-configured with neo4j+s:// URI
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Initialize the Neo4j query tool
        self.neo4j_tool = Neo4jQueryTool(self.driver)
        
        # Initialize the tool-calling agent
        self.agent = ToolCallingAgent(
            neo4j_tool=self.neo4j_tool,
            api_key=groq_api_key,
            model=model
        )
        
        print("✓ Graph RAG Agent initialized successfully with tool-calling architecture")
    
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
        print("✓ Graph RAG Agent closed")
    
    def ask(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Main method to ask a question and get an answer using tool-calling.
        
        The agent will:
        1. Analyze the question
        2. Decide if it needs to query the database
        3. Generate and execute Cypher queries via tool calling
        4. Formulate a natural language answer
        
        Args:
            question: User's natural language question
            verbose: If True, print intermediate steps
            
        Returns:
            Dictionary containing:
                - question: Original question
                - answer: Natural language answer
                - tool_calls: List of tool calls made (with queries and results)
                - raw_results: Combined results from all tool calls
                - success: Boolean indicating if the pipeline succeeded
                - error: Error message if pipeline failed
                
        Example:
            >>> agent = GraphRAGAgent()
            >>> result = agent.ask("Who works at TechCorp?")
            >>> print(result['answer'])
            "The following people work at TechCorp: John Smith (Software Engineer), ..."
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"Question: {question}")
            print(f"{'='*80}")
        
        try:
            # Use the tool-calling agent to process the question
            result = self.agent.ask(question, verbose=verbose)
            
            # Extract relevant information for backward compatibility
            return {
                "question": question,
                "answer": result["answer"],
                "tool_calls": result.get("tool_calls", []),
                "raw_results": result.get("results", []),
                "cypher_query": result["tool_calls"][0]["query"] if result.get("tool_calls") else "",
                "entities": [],  # Not extracted separately in tool-calling approach
                "query_intent": "",  # Not extracted separately in tool-calling approach
                "success": result["success"],
                "error": result.get("error")
            }
            
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            if verbose:
                print(f"\nERROR: {error_msg}")
            
            return {
                "question": question,
                "answer": f"I encountered an error processing your question: {str(e)}",
                "tool_calls": [],
                "raw_results": [],
                "cypher_query": "",
                "entities": [],
                "query_intent": "",
                "success": False,
                "error": error_msg
            }
    
    def ask_simple(self, question: str) -> str:
        """
        Simplified ask method that returns only the answer string.
        
        Args:
            question: User's natural language question
            
        Returns:
            Natural language answer string
            
        Example:
            >>> agent = GraphRAGAgent()
            >>> answer = agent.ask_simple("Who works at TechCorp?")
            >>> print(answer)
        """
        result = self.ask(question, verbose=False)
        return result["answer"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with node counts and relationship counts
        """
        try:
            with self.driver.session() as session:
                # Count nodes by label
                node_result = session.run(
                    "MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY label"
                )
                nodes = {record["label"]: record["count"] for record in node_result}
                
                # Count relationships by type
                rel_result = session.run(
                    "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY type"
                )
                relationships = {record["type"]: record["count"] for record in rel_result}
                
                # Total counts
                total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                
                stats = {
                    "total_nodes": total_nodes,
                    "total_relationships": total_rels,
                    "nodes_by_label": nodes,
                    "relationships_by_type": relationships
                }
                
            return {
                "success": True,
                "statistics": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_connection(self) -> bool:
        """
        Test if the Neo4j connection is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


def main():
    """Test the Graph RAG Agent with example questions."""
    print("Initializing Graph RAG Agent...")
    print("-" * 80)
    
    agent = GraphRAGAgent()
    
    # Test connection
    print("\nTesting Neo4j connection...")
    if agent.test_connection():
        print("✓ Connection successful")
    else:
        print("✗ Connection failed")
        return
    
    # Get database statistics
    print("\nDatabase Statistics:")
    stats_result = agent.get_statistics()
    if stats_result["success"]:
        stats = stats_result["statistics"]
        print(f"  Nodes: {stats.get('total_nodes', 0)}")
        print(f"  Relationships: {stats.get('total_relationships', 0)}")
    
    # Test questions
    test_questions = [
        "Who works at TechCorp Solutions?",
        "What products does HealthFirst Medical use?",
        "Show me all people in the Finance industry",
    ]
    
    print("\n" + "=" * 80)
    print("Testing Graph RAG Agent")
    print("=" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i} ---")
        result = agent.ask(question, verbose=True)
        
        if not result["success"]:
            print(f"ERROR: {result['error']}")
    
    # Close connection
    agent.close()


if __name__ == "__main__":
    main()

