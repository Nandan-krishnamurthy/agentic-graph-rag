"""
Graph RAG Agent Module

Main orchestration module for the Agentic Graph RAG system.
Coordinates entity extraction, Cypher generation, Neo4j queries, and answer formatting.
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from neo4j import GraphDatabase

from agent.entity_extractor import EntityExtractor
from agent.cypher_generator import CypherGenerator
from agent.answer_formatter import AnswerFormatter


class GraphRAGAgent:
    """
    Agentic Graph RAG (Retrieval-Augmented Generation) System.
    
    This agent orchestrates the complete pipeline from natural language
    question to human-readable answer using a Neo4j graph database.
    
    Pipeline:
    1. Extract entities from user question
    2. Generate Cypher query based on entities and question
    3. Execute query against Neo4j database
    4. Format raw results into natural language answer
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
        Initialize the Graph RAG Agent.
        
        Args:
            neo4j_uri: Neo4j connection URI (defaults to NEO4J_URI env var)
            neo4j_user: Neo4j username (defaults to NEO4J_USER env var)
            neo4j_password: Neo4j password (defaults to NEO4J_PASSWORD env var)
            groq_api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: LLM model to use for entity extraction and answer generation
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
        
        # Initialize AI components
        self.entity_extractor = EntityExtractor(api_key=groq_api_key, model=model)
        self.cypher_generator = CypherGenerator(api_key=groq_api_key, model=model)
        self.answer_formatter = AnswerFormatter(api_key=groq_api_key, model=model)
        
        print("✓ Graph RAG Agent initialized successfully")
    
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
        print("✓ Graph RAG Agent closed")
    
    def ask(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Main method to ask a question and get an answer.
        
        This method orchestrates the entire RAG pipeline:
        1. Extract entities from the question
        2. Generate a Cypher query
        3. Execute the query on Neo4j
        4. Format the results into a natural language answer
        
        Args:
            question: User's natural language question
            verbose: If True, print intermediate steps
            
        Returns:
            Dictionary containing:
                - question: Original question
                - entities: Extracted entities
                - cypher_query: Generated Cypher query
                - raw_results: Raw Neo4j query results
                - answer: Formatted natural language answer
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
            # Step 1: Extract entities from the question
            if verbose:
                print("\n[Step 1] Extracting entities...")
            
            extraction_result = self.entity_extractor.extract(question)
            entities = extraction_result.get("entities", [])
            query_intent = extraction_result.get("query_intent", "")
            
            if verbose:
                print(f"  Intent: {query_intent}")
                print(f"  Entities: {entities}")
            
            # Step 2: Generate Cypher query
            if verbose:
                print("\n[Step 2] Generating Cypher query...")
            
            cypher_result = self.cypher_generator.generate_with_validation(
                question=question,
                entities=entities
            )
            
            cypher_query = cypher_result["query"]
            
            if not cypher_result["valid"]:
                error_msg = f"Invalid Cypher query: {cypher_result['error']}"
                if verbose:
                    print(f"  ERROR: {error_msg}")
                return {
                    "question": question,
                    "entities": entities,
                    "cypher_query": cypher_query,
                    "raw_results": [],
                    "answer": "I couldn't generate a valid query for your question.",
                    "success": False,
                    "error": error_msg
                }
            
            if verbose:
                print(f"  Query: {cypher_query}")
            
            # Step 3: Execute query on Neo4j
            if verbose:
                print("\n[Step 3] Executing query on Neo4j...")
            
            raw_results = self._execute_query(cypher_query)
            
            if verbose:
                print(f"  Retrieved {len(raw_results)} results")
                if raw_results and len(raw_results) <= 3:
                    print(f"  Sample: {raw_results[:3]}")
            
            # Step 4: Format answer
            if verbose:
                print("\n[Step 4] Formatting answer...")
            
            answer = self.answer_formatter.format_answer(
                question=question,
                cypher_query=cypher_query,
                results=raw_results
            )
            
            if verbose:
                print(f"\n{'='*80}")
                print(f"Answer: {answer}")
                print(f"{'='*80}\n")
            
            return {
                "question": question,
                "entities": entities,
                "query_intent": query_intent,
                "cypher_query": cypher_query,
                "raw_results": raw_results,
                "answer": answer,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            if verbose:
                print(f"\nERROR: {error_msg}")
            
            return {
                "question": question,
                "entities": [],
                "cypher_query": "",
                "raw_results": [],
                "answer": f"I encountered an error processing your question: {str(e)}",
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
    
    def _execute_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as a list of dictionaries.
        
        Args:
            cypher_query: The Cypher query to execute
            
        Returns:
            List of result dictionaries
        """
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [dict(record) for record in result]


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

