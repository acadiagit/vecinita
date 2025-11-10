"""
Vecinita LangGraph RAG Agent
A retrieval-augmented generation agent that can decide when to retrieve context
from the Supabase vectorstore or respond directly to the user.
"""

import os
from typing import Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.supabase_retriever import get_supabase_retriever
from src.agent_config import (
    CHAT_MODEL_NAME,
    TEMPERATURE,
    GRADE_PROMPT,
    REWRITE_PROMPT,
    GENERATE_PROMPT_EN,
    GENERATE_PROMPT_ES
)

# Load environment variables
load_dotenv()


# --- Pydantic Model for Document Grading ---
class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


class VecinitaRAGAgent:
    """
    LangGraph-based RAG agent for Vecinita project.

    The agent can:
    1. Decide whether to retrieve context from the vectorstore
    2. Grade retrieved documents for relevance
    3. Rewrite questions if documents are not relevant
    4. Generate answers based on retrieved context
    """

    def __init__(self, model_name: str = CHAT_MODEL_NAME, temperature: float = TEMPERATURE):
        """Initialize the RAG agent with model and retriever.

        Args:
            model_name: Name of the chat model to use
            temperature: Temperature for model responses
        """
        # Initialize the chat model
        # You can use "gpt-4o" with OpenAI or "llama-3.1-8b-instant" with Groq
        if "gpt" in model_name.lower():
            # Use OpenAI
            openai_key = os.environ.get("OPEN_API_KEY")
            if not openai_key:
                raise ValueError("OPEN_API_KEY must be set for OpenAI models")
            self.response_model = init_chat_model(
                model_name, temperature=temperature, api_key=openai_key)
        else:
            # Use Groq
            groq_key = os.environ.get("GROQ_API_KEY")
            if not groq_key:
                raise ValueError("GROQ_API_KEY must be set for Groq models")
            self.response_model = init_chat_model(
                model_name,
                temperature=temperature,
                model_provider="groq",
                api_key=groq_key
            )

        self.grader_model = self.response_model  # Use same model for grading

        # Initialize retriever and create tool
        retriever = get_supabase_retriever()
        self.retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_vecinita_docs",
            "Search and return information from Vecinita community documents."
        )

        # Build the graph
        self.graph = self._build_graph()

    def _generate_query_or_respond(self, state: MessagesState):
        """
        Call the model to generate a response based on the current state.
        Given the question, it will decide to retrieve using the retriever tool,
        or simply respond to the user.
        """
        response = (
            self.response_model
            .bind_tools([self.retriever_tool])
            .invoke(state["messages"])
        )
        return {"messages": [response]}

    def _grade_documents(
        self, state: MessagesState
    ) -> Literal["generate_answer", "rewrite_question"]:
        """
        Determine whether the retrieved documents are relevant to the question.

        Returns:
            "generate_answer" if relevant, "rewrite_question" if not relevant
        """
        question = state["messages"][0].content

        # Get the last message which should be a ToolMessage with retrieved docs
        last_message = state["messages"][-1]
        if isinstance(last_message, ToolMessage):
            context = last_message.content
        else:
            # Fallback if message type is unexpected
            context = str(last_message.content)

        prompt = GRADE_PROMPT.format(question=question, context=context)
        response = (
            self.grader_model
            .with_structured_output(GradeDocuments)
            .invoke([{"role": "user", "content": prompt}])
        )

        score = response.binary_score

        if score == "yes":
            print("--- DOCUMENTS ARE RELEVANT ---")
            return "generate_answer"
        else:
            print("--- DOCUMENTS NOT RELEVANT, REWRITING QUESTION ---")
            return "rewrite_question"

    def _rewrite_question(self, state: MessagesState):
        """Rewrite the original user question to improve retrieval."""
        messages = state["messages"]
        question = messages[0].content

        prompt = REWRITE_PROMPT.format(question=question)
        response = self.response_model.invoke(
            [{"role": "user", "content": prompt}])

        print(f"--- REWRITTEN QUESTION: {response.content} ---")

        # Return a new HumanMessage with the rewritten question
        return {"messages": [HumanMessage(content=response.content)]}

    def _generate_answer(self, state: MessagesState):
        """Generate an answer based on the retrieved context."""
        question = state["messages"][0].content

        # Get the last message which should be a ToolMessage with retrieved docs
        last_message = state["messages"][-1]
        if isinstance(last_message, ToolMessage):
            context = last_message.content
        else:
            context = str(last_message.content)

        # Detect language (simple heuristic, can be improved)
        # For simplicity, use English prompt by default
        # You can integrate langdetect here if needed
        prompt = GENERATE_PROMPT_EN.format(question=question, context=context)

        response = self.response_model.invoke(
            [{"role": "user", "content": prompt}])

        return {"messages": [response]}

    def _build_graph(self) -> StateGraph:
        """Build and compile the LangGraph workflow."""
        workflow = StateGraph(MessagesState)

        # Define nodes
        workflow.add_node("generate_query_or_respond",
                          self._generate_query_or_respond)
        workflow.add_node("retrieve", ToolNode([self.retriever_tool]))
        workflow.add_node("rewrite_question", self._rewrite_question)
        workflow.add_node("generate_answer", self._generate_answer)

        # Define edges
        workflow.add_edge(START, "generate_query_or_respond")

        # Decide whether to retrieve or respond directly
        workflow.add_conditional_edges(
            "generate_query_or_respond",
            tools_condition,
            {
                "tools": "retrieve",
                END: END,
            },
        )

        # Grade documents after retrieval
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_documents,
        )

        # After generating answer, we're done
        workflow.add_edge("generate_answer", END)

        # After rewriting, go back to generate_query_or_respond
        workflow.add_edge("rewrite_question", "generate_query_or_respond")

        # Compile the graph
        return workflow.compile()

    def query(self, question: str, verbose: bool = True) -> dict:
        """
        Run the RAG agent with a question.

        Args:
            question: User's question
            verbose: Whether to print intermediate steps

        Returns:
            Dictionary containing the final answer and conversation history
        """
        input_state = {"messages": [HumanMessage(content=question)]}

        final_answer = None
        conversation_history = []

        if verbose:
            print(f"\n{'='*70}")
            print(f"QUESTION: {question}")
            print(f"{'='*70}\n")

        for chunk in self.graph.stream(input_state):
            for node, update in chunk.items():
                if verbose:
                    print(f"--- Update from node: {node} ---")
                    if "messages" in update and update["messages"]:
                        last_msg = update["messages"][-1]
                        if hasattr(last_msg, 'pretty_print'):
                            last_msg.pretty_print()
                        else:
                            print(last_msg)
                    print()

                # Store the conversation
                if "messages" in update:
                    conversation_history.extend(update["messages"])

        # Extract final answer
        if conversation_history:
            for msg in reversed(conversation_history):
                if isinstance(msg, AIMessage) and not msg.tool_calls:
                    final_answer = msg.content
                    break

        return {
            "answer": final_answer,
            "conversation_history": conversation_history
        }

    def visualize(self):
        """Generate and display a visualization of the graph."""
        try:
            from IPython.display import Image, display
            display(Image(self.graph.get_graph().draw_mermaid_png()))
        except Exception as e:
            print(f"Could not visualize graph: {e}")
            print("To visualize, ensure you have IPython and graphviz installed.")


def create_rag_agent(model_name: str = CHAT_MODEL_NAME, temperature: float = TEMPERATURE) -> VecinitaRAGAgent:
    """
    Factory function to create a Vecinita RAG agent.

    Args:
        model_name: Name of the chat model to use
        temperature: Temperature for model responses

    Returns:
        Initialized VecinitaRAGAgent
    """
    return VecinitaRAGAgent(model_name=model_name, temperature=temperature)
