"""
LangSmith Agent Example

This example demonstrates how to use LangSmith for tracing and monitoring
agent runs with the Vecinita RAG system.

When you run this script with LANGSMITH_TRACING=true, all operations will
be automatically traced and visible in the LangSmith project dashboard.

Run with:
    python scripts/langsmith_agent_example.py

The traces will appear at:
    https://smith.langchain.com/projects/pr-trustworthy-sundial-70
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables
load_dotenv()

# Verify LangSmith configuration
print("=" * 60)
print("LangSmith Configuration Check")
print("=" * 60)
print(f"LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING', 'not set')}")
print(f"LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT', 'not set')}")
print(f"LANGSMITH_ENDPOINT: {os.getenv('LANGSMITH_ENDPOINT', 'not set')}")
print(f"LANGSMITH_API_KEY: {'set' if os.getenv('LANGSMITH_API_KEY') else 'not set'}")
print("=" * 60)
print()


# Define tools for the agent
@tool
def get_vecinita_services(category: str = "general") -> str:
    """
    Get information about Vecinita services.
    
    Args:
        category: Type of service (general, education, healthcare, social)
    
    Returns:
        Description of Vecinita services
    """
    services = {
        "general": "Vecinita provides community-based services for neighborhood residents.",
        "education": "Education programs include tutoring, workshops, and digital literacy training.",
        "healthcare": "Healthcare services include wellness checks, health education, and referrals.",
        "social": "Social programs include community events, support groups, and volunteer opportunities.",
    }
    return services.get(category, services["general"])


@tool
def search_vecinita_faq(question: str) -> str:
    """
    Search Vecinita's FAQ database.
    
    Args:
        question: User's question
    
    Returns:
        Relevant FAQ answer
    """
    # This would connect to your RAG system in production
    return f"FAQ result for: {question}"


def create_vecinita_agent():
    """Create a Vecinita Q&A agent with LangSmith tracing."""
    
    # Initialize the model
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
    )
    
    # Define tools
    tools = [get_vecinita_services, search_vecinita_faq]
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant for Vecinita, a community organization.
You help answer questions about Vecinita's services and programs.
Use the available tools to provide accurate, helpful information.
Be friendly and supportive in your responses."""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent
    agent = create_react_agent(model, tools, prompt)
    
    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        early_stopping_method="force",
    )
    
    return agent_executor


def main():
    """Run the example agent."""
    
    print("\n" + "=" * 60)
    print("Vecinita Agent with LangSmith Tracing")
    print("=" * 60)
    print()
    print("Creating agent...")
    
    # Create the agent
    agent = create_vecinita_agent()
    
    # Example queries
    questions = [
        "What services does Vecinita offer?",
        "Tell me about education programs",
        "How can I get healthcare services?",
    ]
    
    # Run queries
    for i, question in enumerate(questions, 1):
        print(f"\n{'─' * 60}")
        print(f"Query {i}: {question}")
        print(f"{'─' * 60}")
        
        try:
            result = agent.invoke({"input": question})
            print(f"\nResponse: {result['output']}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Agent run complete!")
    print("Check your LangSmith project for traces:")
    print(f"  Project: {os.getenv('LANGSMITH_PROJECT', 'pr-trustworthy-sundial-70')}")
    print(f"  URL: https://smith.langchain.com/projects/{os.getenv('LANGSMITH_PROJECT', 'pr-trustworthy-sundial-70')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
