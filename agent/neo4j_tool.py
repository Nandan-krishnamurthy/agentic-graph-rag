"""
Neo4j Query Tool Module

Provides a callable tool for executing Cypher queries against Neo4j database.
This tool is designed to be used by AI agents via function calling.
"""

import json
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase


class Neo4jQueryTool:
    """
    Tool for executing Cypher queries against a Neo4j database.
    
    This tool is designed to be called by AI agents through function calling.
    It executes valid Cypher queries and returns JSON-formatted results.
    """
    
    SCHEMA = """
Node Labels:
- Person (properties: name, role)
- Company (properties: name, industry)
- Product (properties: name, category)

Relationships:
- (Person)-[:WORKS_AT]->(Company)
- (Person)-[:REPORTS_TO]->(Person)
- (Company)-[:USES]->(Product)
"""
    
    def __init__(self, driver: GraphDatabase.driver):
        """
        Initialize the Neo4j query tool.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
    
    def execute_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """
        Execute a Cypher query against the Neo4j database.
        
        This is the main tool function that will be called by the AI agent.
        
        Args:
            cypher_query: A valid Neo4j Cypher query
            
        Returns:
            Dictionary containing:
                - success: Boolean indicating if query executed successfully
                - results: List of result dictionaries from Neo4j
                - count: Number of results returned
                - error: Error message if query failed
                
        Example:
            >>> tool = Neo4jQueryTool(driver)
            >>> result = tool.execute_cypher(
            ...     "MATCH (p:Person) RETURN p.name LIMIT 5"
            ... )
            >>> print(result['results'])
            [{'p.name': 'John Smith'}, {'p.name': 'Jane Doe'}, ...]
        """
        try:
            # Validate the query
            validation = self._validate_query(cypher_query)
            if not validation['valid']:
                return {
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": f"Invalid query: {validation['error']}"
                }
            
            # Execute the query
            with self.driver.session() as session:
                result = session.run(cypher_query)
                results_list = [dict(record) for record in result]
            
            return {
                "success": True,
                "results": results_list,
                "count": len(results_list),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": str(e)
            }
    
    def _validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate a Cypher query before execution.
        
        Args:
            query: Cypher query string
            
        Returns:
            Dictionary with 'valid' boolean and 'error' message
        """
        if not query or len(query.strip()) == 0:
            return {"valid": False, "error": "Empty query"}
        
        query_upper = query.upper()
        
        # Check for required keywords
        if not any(keyword in query_upper for keyword in ["MATCH", "RETURN"]):
            return {"valid": False, "error": "Query must contain MATCH and RETURN"}
        
        # Prevent write operations (security measure)
        write_operations = ["CREATE", "DELETE", "REMOVE", "SET", "MERGE", "DETACH"]
        if any(op in query_upper for op in write_operations):
            return {"valid": False, "error": "Write operations are not allowed"}
        
        # Check for invalid node labels (not in schema)
        invalid_labels = ["User", "Organization", "Item", "Service", "Customer", "Order"]
        for label in invalid_labels:
            if f":{label.upper()}" in query_upper or f":({label.upper()}" in query_upper:
                return {"valid": False, "error": f"Invalid node label: {label}"}
        
        return {"valid": True, "error": None}
    
    def get_schema(self) -> str:
        """
        Get the database schema description.
        
        Returns:
            String describing the graph schema
        """
        return self.SCHEMA
    
    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """
        Get the tool definition for function calling.
        
        This returns the JSON schema that describes the tool to the AI agent.
        
        Returns:
            Dictionary in OpenAI function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": "execute_cypher_query",
                "description": (
                    "Execute a Cypher query against the Neo4j graph database. "
                    "Use this tool to retrieve information about people, companies, and products. "
                    "The database schema includes: "
                    "- Person nodes (properties: name, role) "
                    "- Company nodes (properties: name, industry) "
                    "- Product nodes (properties: name, category) "
                    "- Relationships: (Person)-[:WORKS_AT]->(Company), "
                    "(Person)-[:REPORTS_TO]->(Person), (Company)-[:USES]->(Product). "
                    "Only read operations (MATCH, RETURN) are allowed."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cypher_query": {
                            "type": "string",
                            "description": (
                                "A valid Neo4j Cypher query. Must use MATCH and RETURN. "
                                "Use case-insensitive matching with toLower(). "
                                "Examples: "
                                "'MATCH (p:Person)-[:WORKS_AT]->(c:Company) "
                                "WHERE toLower(c.name) = toLower('TechCorp') "
                                "RETURN p.name, p.role' or "
                                "'MATCH (c:Company)-[:USES]->(prod:Product) "
                                "RETURN c.name, collect(prod.name) as products'"
                            )
                        }
                    },
                    "required": ["cypher_query"]
                }
            }
        }


def main():
    """Test the Neo4j query tool."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize driver
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Create tool
    tool = Neo4jQueryTool(driver)
    
    print("Neo4j Query Tool - Test Cases")
    print("=" * 80)
    
    # Test cases
    test_queries = [
        {
            "name": "Find all people",
            "query": "MATCH (p:Person) RETURN p.name, p.role LIMIT 5"
        },
        {
            "name": "Find people at TechCorp",
            "query": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) WHERE toLower(c.name) CONTAINS 'techcorp' RETURN p.name, p.role"
        },
        {
            "name": "Invalid query (CREATE)",
            "query": "CREATE (p:Person {name: 'Test'})"
        },
        {
            "name": "Invalid query (empty)",
            "query": ""
        }
    ]
    
    for test in test_queries:
        print(f"\nTest: {test['name']}")
        print(f"Query: {test['query']}")
        print("-" * 80)
        
        result = tool.execute_cypher(test['query'])
        
        print(f"Success: {result['success']}")
        print(f"Count: {result['count']}")
        
        if result['success']:
            print(f"Results (first 3):")
            for r in result['results'][:3]:
                print(f"  {r}")
        else:
            print(f"Error: {result['error']}")
        
        print()
    
    # Print tool definition
    print("\nTool Definition for AI Agent:")
    print("=" * 80)
    print(json.dumps(tool.get_tool_definition(), indent=2))
    
    driver.close()


if __name__ == "__main__":
    main()
