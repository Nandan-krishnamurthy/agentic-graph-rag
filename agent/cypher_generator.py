"""
Cypher Query Generator Module

Generates Neo4j Cypher queries from natural language questions
using Groq LLM with strict schema adherence.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class CypherGenerator:
    """
    Generates Cypher queries for Neo4j based on natural language questions
    and extracted entities.
    
    Strictly adheres to the defined graph schema:
    - (Person)-[:WORKS_AT]->(Company)
    - (Person)-[:REPORTS_TO]->(Person)
    - (Company)-[:USES]->(Product)
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
    
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Cypher generator.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model to use
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.llm = ChatGroq(
            api_key=self.api_key,
            model=model,
            temperature=0,  # Deterministic output
            max_tokens=500
        )
        
        self.prompt = self._create_prompt()
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """
        Create the prompt template for Cypher generation.
        
        Includes schema definition and query examples.
        """
        template = """You are an expert Neo4j Cypher query generator. Your task is to convert natural language questions into valid Cypher queries.

GRAPH SCHEMA (MUST FOLLOW EXACTLY):
{schema}

CRITICAL RULES:
1. Use ONLY the node labels and relationships defined above
2. Do NOT create relationships that don't exist in the schema
3. Do NOT hallucinate properties or labels
4. Return ONLY the Cypher query - no explanations, no markdown, no code blocks
5. Use case-insensitive matching with toLower() for text comparisons
6. Use MATCH to find existing nodes, never CREATE
7. Keep queries simple and efficient

EXAMPLES:

Question: "Who works at TechCorp Solutions?"
Entities: [{{"name": "TechCorp Solutions", "type": "Company"}}]
Cypher:
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE toLower(c.name) = toLower('TechCorp Solutions')
RETURN p.name, p.role

Question: "What products does HealthFirst Medical use?"
Entities: [{{"name": "HealthFirst Medical", "type": "Company"}}]
Cypher:
MATCH (c:Company)-[:USES]->(p:Product)
WHERE toLower(c.name) = toLower('HealthFirst Medical')
RETURN p.name, p.category

Question: "Who does Emma Johnson report to?"
Entities: [{{"name": "Emma Johnson", "type": "Person"}}]
Cypher:
MATCH (p:Person)-[:REPORTS_TO]->(manager:Person)
WHERE toLower(p.name) = toLower('Emma Johnson')
RETURN manager.name, manager.role

Question: "Which companies use CloudSync Pro?"
Entities: [{{"name": "CloudSync Pro", "type": "Product"}}]
Cypher:
MATCH (c:Company)-[:USES]->(p:Product)
WHERE toLower(p.name) = toLower('CloudSync Pro')
RETURN c.name, c.industry

Question: "Show all employees at TechCorp and what products they use"
Entities: [{{"name": "TechCorp", "type": "Company"}}]
Cypher:
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE toLower(c.name) CONTAINS toLower('TechCorp')
OPTIONAL MATCH (c)-[:USES]->(prod:Product)
RETURN p.name, p.role, collect(prod.name) as products

Question: "List all people in the Finance industry"
Entities: []
Cypher:
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE toLower(c.industry) = toLower('Finance')
RETURN p.name, p.role, c.name

Now generate a Cypher query for this question:

Question: {question}
Entities: {entities}

Return ONLY the Cypher query, nothing else:"""

        return ChatPromptTemplate.from_messages([
            ("system", "You are a Cypher query generator. Return only valid Cypher queries with no additional text."),
            ("human", template)
        ]).partial(schema=self.SCHEMA)
    
    def generate(
        self, 
        question: str, 
        entities: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a Cypher query from a natural language question.
        
        Args:
            question: User's natural language question
            entities: List of extracted entities with 'name' and 'type' keys
            
        Returns:
            Valid Cypher query string
            
        Example:
            >>> generator = CypherGenerator()
            >>> query = generator.generate(
            ...     "Who works at TechCorp?",
            ...     [{"name": "TechCorp", "type": "Company"}]
            ... )
            >>> print(query)
            MATCH (p:Person)-[:WORKS_AT]->(c:Company)
            WHERE toLower(c.name) = toLower('TechCorp')
            RETURN p.name, p.role
        """
        if not question or not question.strip():
            return "MATCH (n) RETURN n LIMIT 10"
        
        entities = entities or []
        entities_str = json.dumps(entities, indent=2)
        
        try:
            cypher_query = self.chain.invoke({
                "question": question,
                "entities": entities_str
            })
            
            # Clean up the output
            cypher_query = cypher_query.strip()
            
            # Remove markdown code blocks if present
            if cypher_query.startswith("```"):
                lines = cypher_query.split("\n")
                cypher_query = "\n".join(lines[1:-1]) if len(lines) > 2 else cypher_query
            
            cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            
            return cypher_query
            
        except Exception as e:
            print(f"Error generating Cypher query: {e}")
            return "MATCH (n) RETURN n LIMIT 10"
    
    def generate_with_validation(
        self,
        question: str,
        entities: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate Cypher query with basic validation.
        
        Args:
            question: User's natural language question
            entities: List of extracted entities
            
        Returns:
            Dictionary with 'query', 'valid', and 'error' keys
        """
        query = self.generate(question, entities)
        
        # Basic validation
        valid = True
        error = None
        
        if not query or len(query.strip()) == 0:
            valid = False
            error = "Empty query generated"
        elif not any(keyword in query.upper() for keyword in ["MATCH", "RETURN", "CREATE", "MERGE"]):
            valid = False
            error = "Query missing required Cypher keywords"
        
        # Check for invalid labels/relationships
        invalid_labels = []
        for label in ["User", "Organization", "Item", "Service"]:
            if f":{label}" in query:
                invalid_labels.append(label)
        
        if invalid_labels:
            valid = False
            error = f"Query contains invalid labels: {', '.join(invalid_labels)}"
        
        return {
            "query": query,
            "valid": valid,
            "error": error
        }


def main():
    """Test the Cypher generator with example questions."""
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = CypherGenerator()
    
    test_cases = [
        {
            "question": "Who works at TechCorp Solutions?",
            "entities": [{"name": "TechCorp Solutions", "type": "Company"}]
        },
        {
            "question": "What products does HealthFirst Medical use?",
            "entities": [{"name": "HealthFirst Medical", "type": "Company"}]
        },
        {
            "question": "Who does Emma Johnson report to?",
            "entities": [{"name": "Emma Johnson", "type": "Person"}]
        },
        {
            "question": "Which companies use CloudSync Pro?",
            "entities": [{"name": "CloudSync Pro", "type": "Product"}]
        },
        {
            "question": "Show me all people in the Technology industry",
            "entities": []
        },
    ]
    
    print("Cypher Query Generation Examples")
    print("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Question: {case['question']}")
        print(f"   Entities: {case['entities']}")
        print(f"\n   Generated Cypher:")
        
        result = generator.generate_with_validation(
            case['question'],
            case['entities']
        )
        
        print(f"   {result['query']}")
        print(f"\n   Valid: {result['valid']}")
        if result['error']:
            print(f"   Error: {result['error']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
