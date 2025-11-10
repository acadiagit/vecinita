"""
Example script demonstrating the Vecinita LangGraph RAG Agent

This script shows how to:
1. Initialize the RAG agent
2. Ask questions that require retrieval
3. Ask questions that can be answered directly
4. View the agent's decision-making process
"""

from src.rag_agent import create_rag_agent


def main():
    print("=" * 70)
    print("Vecinita LangGraph RAG Agent - Example Usage")
    print("=" * 70)

    # Initialize the RAG agent
    # You can use "gpt-4o" (OpenAI) or "llama-3.1-8b-instant" (Groq)
    print("\nInitializing RAG agent...")
    agent = create_rag_agent(model_name="llama-3.1-8b-instant", temperature=0)
    print("✅ Agent initialized successfully!\n")

    # Example 1: Question that requires retrieval from vectorstore
    print("\n" + "=" * 70)
    print("Example 1: Question requiring document retrieval")
    print("=" * 70)

    question1 = "What information do you have about reward hacking?"
    result1 = agent.query(question1, verbose=True)

    print("\n--- FINAL ANSWER ---")
    print(result1["answer"])

    # Example 2: Simple greeting (should respond directly without retrieval)
    print("\n" + "=" * 70)
    print("Example 2: Simple greeting (no retrieval needed)")
    print("=" * 70)

    question2 = "Hello! How are you?"
    result2 = agent.query(question2, verbose=True)

    print("\n--- FINAL ANSWER ---")
    print(result2["answer"])

    # Example 3: Question about Vecinita community
    print("\n" + "=" * 70)
    print("Example 3: Community-specific question")
    print("=" * 70)

    question3 = "What services are available in the Vecinita community?"
    result3 = agent.query(question3, verbose=True)

    print("\n--- FINAL ANSWER ---")
    print(result3["answer"])

    # Example 4: Interactive mode
    print("\n" + "=" * 70)
    print("Interactive Mode - Ask your own questions!")
    print("=" * 70)
    print("Type 'quit' or 'exit' to stop\n")

    while True:
        try:
            user_question = input("\nYour question: ").strip()

            if user_question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if not user_question:
                print("Please enter a question.")
                continue

            result = agent.query(user_question, verbose=False)
            print(f"\n🤖 Answer: {result['answer']}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
