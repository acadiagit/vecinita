"""
Integration example: Adding LangGraph RAG Agent to your existing FastAPI app

This shows how to integrate the RAG agent into main.py while keeping
your existing /ask endpoint for comparison.
"""

# Add this to the top of main.py, after other imports:
# from rag_agent import create_rag_agent

# Add this after initializing other clients (around line 40):
# Initialize RAG agent
# try:
#     print("Initializing LangGraph RAG agent...")
#     rag_agent = create_rag_agent(
#         model_name="llama-3.1-8b-instant",  # or "gpt-4o"
#         temperature=0
#     )
#     print("✅ RAG agent initialized successfully!")
# except Exception as e:
#     print(f"⚠️  Could not initialize RAG agent: {e}")
#     rag_agent = None

# Add this new endpoint (after the existing /ask endpoint):
# @app.get("/ask_agent")
# async def ask_with_agent(question: str, verbose: bool = False):
#     """
#     Ask a question using the LangGraph RAG agent.
#
#     The agent will decide whether to retrieve documents or respond directly.
#
#     Args:
#         question: User's question
#         verbose: Whether to include conversation history in response
#
#     Returns:
#         JSON with answer and optional conversation history
#     """
#     if not question:
#         raise HTTPException(status_code=400, detail="Question parameter cannot be empty.")
#
#     if not rag_agent:
#         raise HTTPException(
#             status_code=503,
#             detail="RAG agent is not available. Please check server logs."
#         )
#
#     print(f"\n--- RAG Agent Request: '{question}' ---")
#
#     try:
#         result = rag_agent.query(question, verbose=False)
#
#         response_data = {
#             "answer": result["answer"],
#             "agent_used": True
#         }
#
#         if verbose:
#             # Include conversation history if requested
#             response_data["conversation_history"] = [
#                 {
#                     "type": type(msg).__name__,
#                     "content": str(msg.content) if hasattr(msg, 'content') else str(msg)
#                 }
#                 for msg in result["conversation_history"]
#             ]
#
#         return response_data
#
#     except Exception as e:
#         print(f"❌ RAG agent error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# Optional: Add a comparison endpoint that uses both methods
# @app.get("/ask_compare")
# async def ask_compare(question: str):
#     """
#     Compare responses from the original method and the RAG agent.
#     """
#     if not question:
#         raise HTTPException(status_code=400, detail="Question parameter cannot be empty.")
#
#     # Get response from original method
#     original_response = await ask_question(question)
#
#     # Get response from RAG agent
#     agent_response = None
#     if rag_agent:
#         try:
#             result = rag_agent.query(question, verbose=False)
#             agent_response = result["answer"]
#         except Exception as e:
#             agent_response = f"Error: {e}"
#
#     return {
#         "question": question,
#         "original_method": original_response,
#         "agent_method": agent_response or "Agent not available"
#     }


# Example usage:
# 1. Start your server: uvicorn main:app --reload
# 2. Test the original endpoint: http://localhost:8000/ask?question=Hello
# 3. Test the agent endpoint: http://localhost:8000/ask_agent?question=Hello
# 4. Test with verbose: http://localhost:8000/ask_agent?question=Hello&verbose=true
# 5. Compare both: http://localhost:8000/ask_compare?question=What is Vecinita?
