"""
Answer Formatter Module

Formats Neo4j query results into natural, human-readable answers using Groq LLM.
"""

import os
import json
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class AnswerFormatter:
    """
    Formats Neo4j query results into natural language answers.
    
    Uses Groq LLM to convert raw database results into friendly,
    conversational responses.
    """
    
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the answer formatter.
        
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
            temperature=0.3,  # Slightly creative but still consistent
            max_tokens=500
        )
        
        self.prompt = self._create_prompt()
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for answer formatting."""
        template = """You are a helpful assistant that converts database query results into natural, conversational answers.

Your task is to take raw database results and format them into a clear, friendly answer to the user's question.

Guidelines:
1. Be conversational and natural
2. If no results found, say so politely
3. For multiple results, organize them clearly (use bullet points or numbered lists)
4. Include all relevant information from the results
5. Keep it concise but complete
6. Don't make up information - only use what's in the results

Examples:

Question: "Who works at TechCorp?"
Results: [{{"p.name": "John Smith", "p.role": "Engineer"}}, {{"p.name": "Jane Doe", "p.role": "Manager"}}]
Answer: "At TechCorp, there are 2 employees: John Smith who works as an Engineer, and Jane Doe who works as a Manager."

Question: "What products does HealthFirst use?"
Results: []
Answer: "I couldn't find any products associated with HealthFirst in the database."

Question: "Who does Emma report to?"
Results: [{{"manager.name": "Sarah Johnson", "manager.role": "VP Engineering"}}]
Answer: "Emma reports to Sarah Johnson, who is the VP Engineering."

Now format this answer:

Question: {question}
Cypher Query: {cypher_query}
Results: {results}

Provide a natural language answer:"""

        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that formats database results into friendly answers."),
            ("human", template)
        ])
    
    def format_answer(
        self,
        question: str,
        cypher_query: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Format Neo4j query results into a natural language answer.
        
        Args:
            question: Original user question
            cypher_query: The Cypher query that was executed
            results: List of result dictionaries from Neo4j
            
        Returns:
            Natural language answer string
            
        Example:
            >>> formatter = AnswerFormatter()
            >>> results = [{"p.name": "John", "p.role": "Engineer"}]
            >>> answer = formatter.format_answer(
            ...     "Who works at TechCorp?",
            ...     "MATCH (p:Person)...",
            ...     results
            ... )
            >>> print(answer)
            "John works at TechCorp as an Engineer."
        """
        # Handle empty results with a simple fallback
        if not results or len(results) == 0:
            return self._format_empty_results(question)
        
        # Prepare results as JSON string
        results_str = json.dumps(results, indent=2, default=str)
        
        try:
            # Use LLM to format the answer
            answer = self.chain.invoke({
                "question": question,
                "cypher_query": cypher_query,
                "results": results_str
            })
            
            return answer.strip()
            
        except Exception as e:
            print(f"Error formatting answer with LLM: {e}")
            # Fallback to simple formatting
            return self._format_simple(question, results)
    
    def _format_empty_results(self, question: str) -> str:
        """
        Format a response when no results are found.
        
        Args:
            question: Original user question
            
        Returns:
            Friendly message indicating no results
        """
        return f"I couldn't find any information to answer '{question}'. The database might not contain data matching your query."
    
    def _format_simple(
        self,
        question: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Simple fallback formatting without LLM.
        
        Args:
            question: Original user question
            results: Query results
            
        Returns:
            Basic formatted answer
        """
        # Count results
        count = len(results)
        
        if count == 0:
            return self._format_empty_results(question)
        
        # Build simple answer
        answer_parts = [f"Found {count} result(s):\n"]
        
        for i, result in enumerate(results[:10], 1):  # Limit to 10 results
            # Format each result
            parts = []
            for key, value in result.items():
                if value is not None:
                    parts.append(f"{key}: {value}")
            
            answer_parts.append(f"{i}. {', '.join(parts)}")
        
        if count > 10:
            answer_parts.append(f"\n... and {count - 10} more results")
        
        return "\n".join(answer_parts)


def main():
    """Test the answer formatter with example results."""
    from dotenv import load_dotenv
    load_dotenv()
    
    formatter = AnswerFormatter()
    
    test_cases = [
        {
            "question": "Who works at TechCorp Solutions?",
            "cypher_query": "MATCH (p:Person)-[:WORKS_AT]->(c:Company) WHERE c.name = 'TechCorp Solutions' RETURN p.name, p.role",
            "results": [
                {"p.name": "John Smith", "p.role": "Software Engineer"},
                {"p.name": "Jane Doe", "p.role": "Engineering Manager"},
                {"p.name": "Bob Johnson", "p.role": "Senior Developer"}
            ]
        },
        {
            "question": "What products does HealthFirst Medical use?",
            "cypher_query": "MATCH (c:Company)-[:USES]->(p:Product) WHERE c.name = 'HealthFirst Medical' RETURN p.name, p.category",
            "results": [
                {"p.name": "SecureVault", "p.category": "Security"},
                {"p.name": "HRConnect", "p.category": "Human Resources"}
            ]
        },
        {
            "question": "Who does Emma Johnson report to?",
            "cypher_query": "MATCH (p:Person)-[:REPORTS_TO]->(m:Person) WHERE p.name = 'Emma Johnson' RETURN m.name, m.role",
            "results": [
                {"m.name": "Sarah Williams", "m.role": "VP Engineering"}
            ]
        },
        {
            "question": "Which companies use NonExistentProduct?",
            "cypher_query": "MATCH (c:Company)-[:USES]->(p:Product) WHERE p.name = 'NonExistentProduct' RETURN c.name",
            "results": []
        }
    ]
    
    print("Answer Formatting Examples")
    print("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Question: {case['question']}")
        print(f"   Results count: {len(case['results'])}")
        print(f"\n   Formatted Answer:")
        
        answer = formatter.format_answer(
            case['question'],
            case['cypher_query'],
            case['results']
        )
        
        print(f"   {answer}")
        print("-" * 80)


if __name__ == "__main__":
    main()
