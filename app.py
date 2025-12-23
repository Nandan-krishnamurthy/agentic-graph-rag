"""
Streamlit Application for Agentic Graph RAG System

A web interface for querying a Neo4j knowledge graph using natural language.
"""

import streamlit as st
from dotenv import load_dotenv
from agent.graph_agent import GraphRAGAgent
import json

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Agentic Graph RAG",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state for the agent
# This ensures the agent persists across reruns and connections aren't recreated
if 'agent' not in st.session_state:
    try:
        st.session_state.agent = GraphRAGAgent()
        st.session_state.agent_initialized = True
    except Exception as e:
        st.session_state.agent = None
        st.session_state.agent_initialized = False
        st.session_state.init_error = str(e)

# Main UI
st.title("🔍 Agentic Graph RAG System")
st.markdown("Ask questions about companies, people, and products in natural language")

# Show initialization error if agent failed to initialize
if not st.session_state.agent_initialized:
    st.error(f"❌ Failed to initialize agent: {st.session_state.init_error}")
    st.info("Please check your .env file and ensure Neo4j credentials are correct.")
    st.stop()

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This is an **Agentic Graph RAG** system that:
    1. 🧠 Extracts entities from your question
    2. 🔄 Generates a Cypher query
    3. 📊 Queries the Neo4j graph database
    4. 💬 Formats a natural language answer
    """)
    
    st.header("📝 Example Questions")
    st.markdown("""
    - Who works at TechCorp Solutions?
    - What products does HealthFirst Medical use?
    - Who does Emma Johnson report to?
    - Show me all people in the Finance industry
    - Which companies use CloudSync Pro?
    """)
    
    st.header("🔧 System Status")
    
    # Test connection button
    if st.button("Test Neo4j Connection"):
        with st.spinner("Testing connection..."):
            if st.session_state.agent.test_connection():
                st.success("✅ Connected to Neo4j")
            else:
                st.error("❌ Connection failed")
    
    # Show database statistics
    if st.button("Show Database Stats"):
        with st.spinner("Fetching statistics..."):
            stats = st.session_state.agent.get_statistics()
            if stats["success"]:
                st.json(stats["statistics"])
            else:
                st.error(f"Error: {stats['error']}")

# Main content area
st.header("Ask a Question")

# Create a form for the question input
# Using a form prevents the app from rerunning on every keystroke
with st.form(key="question_form"):
    # Text input for the user's question
    user_question = st.text_input(
        "Enter your question:",
        placeholder="e.g., Who works at TechCorp Solutions?",
        help="Ask anything about people, companies, or products in the database"
    )
    
    # Submit button
    submit_button = st.form_submit_button("🔍 Ask Question")

# Process the question when submitted
if submit_button:
    # Validate that a question was entered
    if not user_question or not user_question.strip():
        st.warning("⚠️ Please enter a question")
    else:
        # Show a spinner while processing
        with st.spinner("🤔 Thinking..."):
            try:
                # Call the Graph RAG Agent with the question
                # verbose=False keeps the terminal clean
                result = st.session_state.agent.ask(user_question, verbose=False)
                
                # Check if the query was successful
                if result["success"]:
                    # Display the answer prominently
                    st.success("✅ Answer")
                    st.markdown(f"**{result['answer']}**")
                    
                    # Create two columns for additional details
                    col1, col2 = st.columns(2)
                    
                    # Left column: Show extracted entities
                    with col1:
                        with st.expander("🏷️ Extracted Entities", expanded=False):
                            if result.get("entities"):
                                # Display entities in a nice format
                                for entity in result["entities"]:
                                    st.markdown(f"- **{entity['name']}** ({entity['type']})")
                            else:
                                st.info("No specific entities extracted")
                            
                            # Show query intent if available
                            if result.get("query_intent"):
                                st.markdown(f"\n**Intent:** {result['query_intent']}")
                    
                    # Right column: Show Cypher query
                    with col2:
                        with st.expander("🔍 Generated Cypher Query", expanded=False):
                            # Display the Cypher query with syntax highlighting
                            st.code(result["cypher_query"], language="cypher")
                    
                    # Full-width section: Show raw results
                    with st.expander("📊 Raw Neo4j Results", expanded=False):
                        if result["raw_results"]:
                            # Show count
                            st.info(f"Retrieved {len(result['raw_results'])} result(s)")
                            
                            # Display as JSON for readability
                            st.json(result["raw_results"])
                        else:
                            st.warning("No results found in the database")
                
                else:
                    # Handle errors from the agent
                    st.error("❌ Error Processing Question")
                    st.markdown(result["answer"])
                    
                    # Show error details in an expander
                    if result.get("error"):
                        with st.expander("🔍 Error Details"):
                            st.code(result["error"])
            
            except Exception as e:
                # Catch any unexpected errors
                st.error(f"❌ Unexpected Error: {str(e)}")
                st.info("Please check your Neo4j connection and try again.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Built with Streamlit, Neo4j Aura, and Groq LLM
    </div>
    """,
    unsafe_allow_html=True
)
