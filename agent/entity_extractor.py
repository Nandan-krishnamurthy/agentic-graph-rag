"""
Entity Extraction Module

Extracts structured entities from natural language questions using Groq LLM.
Supports: Person, Company, Product entity types.
"""

import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


class Entity(BaseModel):
    """Single entity model."""
    name: str = Field(description="The name of the entity")
    type: str = Field(description="The type of entity: Person, Company, or Product")


class ExtractedEntities(BaseModel):
    """Collection of extracted entities."""
    entities: List[Entity] = Field(description="List of entities found in the question")
    query_intent: str = Field(description="Brief description of what the user is asking about")


class EntityExtractor:
    """
    Extracts entities from natural language questions using Groq LLM.
    
    Identifies Person, Company, and Product entities that can be used
    for graph database queries.
    """
    
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the entity extractor.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model to use (e.g., llama-3.3-70b-versatile, mixtral-8x7b-32768)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.llm = ChatGroq(
            api_key=self.api_key,
            model=model,
            temperature=0,  # Deterministic output
            max_tokens=1000
        )
        
        self.parser = JsonOutputParser(pydantic_object=ExtractedEntities)
        self.prompt = self._create_prompt()
        self.chain = self.prompt | self.llm | self.parser
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """
        Create the prompt template for entity extraction.
        
        Uses clear instructions and examples for consistent extraction.
        """
        template = """You are an expert at extracting entities from natural language questions for graph database queries.

Your task is to identify all entities mentioned in the user's question and classify them into these types:
- Person: Individual people (e.g., "John Smith", "Sarah", "the CEO")
- Company: Organizations, businesses, or corporations (e.g., "TechCorp", "Google", "the startup")
- Product: Products, services, or tools (e.g., "CloudSync Pro", "iPhone", "the analytics platform")

Important rules:
1. Extract ALL entities that are explicitly mentioned or clearly implied
2. Preserve the exact names as mentioned in the question
3. If a generic reference is made (e.g., "the manager", "our company"), extract it as-is
4. Include job titles/roles as Person entities when referring to specific individuals
5. Return an empty list if no entities are found
6. Also provide a brief query_intent describing what the user wants to know

Examples:

Question: "Who does John Smith report to at TechCorp?"
{{
  "entities": [
    {{"name": "John Smith", "type": "Person"}},
    {{"name": "TechCorp", "type": "Company"}}
  ],
  "query_intent": "Find reporting relationship for John Smith at TechCorp"
}}

Question: "Which companies use CloudSync Pro?"
{{
  "entities": [
    {{"name": "CloudSync Pro", "type": "Product"}}
  ],
  "query_intent": "Find companies that use CloudSync Pro product"
}}

Question: "Show me all employees at HealthFirst Medical"
{{
  "entities": [
    {{"name": "HealthFirst Medical", "type": "Company"}}
  ],
  "query_intent": "List all employees at HealthFirst Medical"
}}

Question: "What products does Emma Johnson's company use?"
{{
  "entities": [
    {{"name": "Emma Johnson", "type": "Person"}}
  ],
  "query_intent": "Find products used by Emma Johnson's company"
}}

Now extract entities from this question:
Question: {question}

{format_instructions}

Return valid JSON only, no additional text."""

        return ChatPromptTemplate.from_messages([
            ("system", "You are a precise entity extraction system. Always return valid JSON."),
            ("human", template)
        ]).partial(format_instructions=self.parser.get_format_instructions())
    
    def extract(self, question: str) -> Dict[str, Any]:
        """
        Extract entities from a natural language question.
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary with 'entities' list and 'query_intent' string
            
        Example:
            >>> extractor = EntityExtractor()
            >>> result = extractor.extract("Who works at TechCorp?")
            >>> print(result)
            {
                'entities': [{'name': 'TechCorp', 'type': 'Company'}],
                'query_intent': 'Find employees at TechCorp'
            }
        """
        if not question or not question.strip():
            return {
                "entities": [],
                "query_intent": "Empty question"
            }
        
        try:
            result = self.chain.invoke({"question": question})
            return result
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {
                "entities": [],
                "query_intent": "Error processing question"
            }
    
    def extract_entities_only(self, question: str) -> List[Dict[str, str]]:
        """
        Extract only the entities list (convenience method).
        
        Args:
            question: User's natural language question
            
        Returns:
            List of entity dictionaries with 'name' and 'type'
        """
        result = self.extract(question)
        return result.get("entities", [])


def main():
    """Test the entity extractor with example questions."""
    from dotenv import load_dotenv
    load_dotenv()
    
    extractor = EntityExtractor()
    
    test_questions = [
        "Who does John Smith report to at TechCorp?",
        "Which companies use CloudSync Pro?",
        "What products does Emma Johnson's company use?",
        "Show me all employees in the Finance industry",
        "Does HealthFirst Medical use SecureVault?",
    ]
    
    print("Entity Extraction Examples")
    print("=" * 70)
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        result = extractor.extract(question)
        print(f"Intent: {result['query_intent']}")
        print(f"Entities: {json.dumps(result['entities'], indent=2)}")
        print("-" * 70)


if __name__ == "__main__":
    main()
