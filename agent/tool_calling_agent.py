"""
Tool-Calling Agent Module

AI agent that can decide when to call the Neo4j query tool to answer questions.
Uses Groq LLM with function calling capabilities.
"""

import os
import json
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


class ToolCallingAgent:
    """
    AI agent that uses function calling to decide when to query Neo4j.
    
    The agent:
    1. Receives a user question
    2. Decides if it needs to query the database
    3. Generates appropriate Cypher queries using function calling
    4. Processes the results and formulates an answer
    """
    
    def __init__(
        self,
        neo4j_tool,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Initialize the tool-calling agent.
        
        Args:
            neo4j_tool: Instance of Neo4jQueryTool
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model to use (must support function calling)
        """
        self.neo4j_tool = neo4j_tool
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Initialize LLM with function calling support
        self.llm = ChatGroq(
            api_key=self.api_key,
            model=model,
            temperature=0,  # Deterministic
            max_tokens=2000
        )
        
        # Bind the tool to the LLM
        self.tools = [neo4j_tool.get_tool_definition()]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        return f"""You are a helpful AI assistant that answers questions about a Neo4j graph database.

DATABASE SCHEMA:
{self.neo4j_tool.get_schema()}

YOUR CAPABILITIES:
- You have access to a Neo4j database through the execute_cypher_query tool
- You can generate Cypher queries to retrieve information
- You should use the tool whenever the user asks about people, companies, or products

GUIDELINES:
1. When a user asks a question, decide if you need to query the database
2. If yes, generate an appropriate Cypher query using the execute_cypher_query tool
3. Use case-insensitive matching with toLower() for text comparisons
4. After receiving results, formulate a natural, conversational answer
5. If no results are found, explain this clearly
6. Always use MATCH and RETURN - never use write operations
7. Keep queries simple and efficient

IMPORTANT CYPHER RULES:
- Use ONLY node labels: Person, Company, Product
- Use ONLY relationships: WORKS_AT, REPORTS_TO, USES
- Use toLower() for case-insensitive matching
- Include all relevant properties in RETURN clause
- Use LIMIT to prevent returning too many results

EXAMPLES OF GOOD CYPHER QUERIES:

1. Find employees at a company:
   MATCH (p:Person)-[:WORKS_AT]->(c:Company)
   WHERE toLower(c.name) = toLower('TechCorp')
   RETURN p.name, p.role

2. Find products used by a company:
   MATCH (c:Company)-[:USES]->(prod:Product)
   WHERE toLower(c.name) = toLower('HealthFirst Medical')
   RETURN prod.name, prod.category

3. Find reporting relationships:
   MATCH (p:Person)-[:REPORTS_TO]->(manager:Person)
   WHERE toLower(p.name) = toLower('Emma Johnson')
   RETURN manager.name, manager.role

4. Find companies using a product:
   MATCH (c:Company)-[:USES]->(prod:Product)
   WHERE toLower(prod.name) = toLower('CloudSync Pro')
   RETURN c.name, c.industry

Remember: Generate the query, call the tool, then format the results into a natural answer."""
    
    def ask(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Ask a question and get an answer using tool calling.
        
        Args:
            question: User's natural language question
            verbose: If True, print detailed information
            
        Returns:
            Dictionary containing:
                - question: Original question
                - answer: Natural language answer
                - tool_calls: List of tool calls made
                - results: Results from tool calls
                - success: Boolean indicating if query succeeded
                - error: Error message if failed
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"Question: {question}")
            print(f"{'='*80}")
        
        try:
            # Initialize conversation
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=question)
            ]
            
            tool_calls_made = []
            all_results = []
            
            # Agent loop - allow multiple tool calls if needed
            max_iterations = 3
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                if verbose:
                    print(f"\n[Iteration {iteration}] Invoking LLM...")
                
                # Get response from LLM
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)
                
                # Check if LLM wants to call a tool
                if not response.tool_calls:
                    # No tool calls - LLM has provided final answer
                    if verbose:
                        print(f"[Iteration {iteration}] No tool calls. Final answer provided.")
                    
                    final_answer = response.content
                    
                    return {
                        "question": question,
                        "answer": final_answer,
                        "tool_calls": tool_calls_made,
                        "results": all_results,
                        "success": True,
                        "error": None
                    }
                
                # Process tool calls
                for tool_call in response.tool_calls:
                    if verbose:
                        print(f"\n[Iteration {iteration}] Tool call detected:")
                        print(f"  Function: {tool_call['name']}")
                        print(f"  Arguments: {tool_call['args']}")
                    
                    # Execute the tool
                    if tool_call['name'] == 'execute_cypher_query':
                        cypher_query = tool_call['args'].get('cypher_query', '')
                        
                        if verbose:
                            print(f"  Cypher Query:\n    {cypher_query}")
                        
                        # Execute query using the tool
                        result = self.neo4j_tool.execute_cypher(cypher_query)
                        
                        if verbose:
                            print(f"  Success: {result['success']}")
                            print(f"  Results count: {result['count']}")
                            if result['count'] > 0 and result['count'] <= 3:
                                print(f"  Sample results: {result['results'][:3]}")
                        
                        # Store tool call info
                        tool_calls_made.append({
                            "function": tool_call['name'],
                            "query": cypher_query,
                            "success": result['success'],
                            "count": result['count']
                        })
                        
                        all_results.extend(result['results'])
                        
                        # Add tool result to messages
                        tool_message = ToolMessage(
                            content=json.dumps(result, default=str),
                            tool_call_id=tool_call['id']
                        )
                        messages.append(tool_message)
            
            # If we get here, we hit max iterations
            if verbose:
                print(f"\n[Warning] Max iterations ({max_iterations}) reached")
            
            return {
                "question": question,
                "answer": "I encountered an issue processing your question after multiple attempts.",
                "tool_calls": tool_calls_made,
                "results": all_results,
                "success": False,
                "error": "Max iterations reached"
            }
            
        except Exception as e:
            if verbose:
                print(f"\n[Error] {str(e)}")
            
            return {
                "question": question,
                "answer": f"I encountered an error: {str(e)}",
                "tool_calls": [],
                "results": [],
                "success": False,
                "error": str(e)
            }
    
    def ask_simple(self, question: str) -> str:
        """
        Simplified ask method that returns only the answer.
        
        Args:
            question: User's natural language question
            
        Returns:
            Natural language answer string
        """
        result = self.ask(question, verbose=False)
        return result["answer"]


def main():
    """Test the tool-calling agent."""
    from dotenv import load_dotenv
    from neo4j import GraphDatabase
    from agent.neo4j_tool import Neo4jQueryTool
    
    load_dotenv()
    
    # Initialize Neo4j driver
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Create tool and agent
    neo4j_tool = Neo4jQueryTool(driver)
    agent = ToolCallingAgent(neo4j_tool)
    
    print("Tool-Calling Agent - Test Cases")
    print("=" * 80)
    
    test_questions = [
        "Who works at TechCorp Solutions?",
        "What products does HealthFirst Medical use?",
        "Who does Emma Johnson report to?",
        "Show me all people in the Finance industry",
        "Which companies use CloudSync Pro?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i} ---")
        result = agent.ask(question, verbose=True)
        
        print(f"\n{'='*80}")
        print(f"FINAL ANSWER:")
        print(f"{'='*80}")
        print(result['answer'])
        print()
    
    driver.close()


if __name__ == "__main__":
    main()
