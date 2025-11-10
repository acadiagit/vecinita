"""
Visual diagram of the Vecinita LangGraph RAG Agent workflow
This can be used to understand how the agent processes questions
"""

WORKFLOW_DIAGRAM = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    VECINITA LANGGRAPH RAG AGENT WORKFLOW                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│                         1. USER ASKS QUESTION                           │
│                                                                         │
│  Example: "What services are available in Vecinita?"                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   2. GENERATE QUERY OR RESPOND NODE                     │
│                                                                         │
│  LLM (GPT-4o or Llama-3.1) analyzes the question:                      │
│  ├─ Is this a simple greeting? → Respond directly                      │
│  ├─ Does it need document context? → Use retriever tool                │
│  └─ Can I answer from general knowledge? → Respond directly            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌─────────────────────┐   ┌────────────────────┐
         │  3a. RETRIEVE TOOL  │   │ 3b. DIRECT ANSWER  │
         │                     │   │                    │
         │ • Generate query    │   │ • No retrieval     │
         │   embedding         │   │ • Immediate reply  │
         │ • Search Supabase   │   │                    │
         │ • Return top 5 docs │   └─────────┬──────────┘
         │ • Include metadata  │             │
         └──────────┬──────────┘             │
                    │                        │
                    ▼                        │
         ┌─────────────────────┐             │
         │ 4. GRADE DOCUMENTS  │             │
         │                     │             │
         │ For each document:  │             │
         │ • Is it relevant?   │             │
         │ • Contains keywords?│             │
         │ • Semantic match?   │             │
         │                     │             │
         │ Decision:           │             │
         │ ├─ YES → Relevant   │             │
         │ └─ NO → Not relevant│             │
         └──────────┬──────────┘             │
                    │                        │
         ┌──────────┴──────────┐             │
         │                     │             │
         ▼                     ▼             │
┌───────────────────┐  ┌──────────────────┐ │
│ 5a. GENERATE      │  │ 5b. REWRITE      │ │
│     ANSWER        │  │     QUESTION     │ │
│                   │  │                  │ │
│ • Format context  │  │ • Analyze intent │ │
│ • Generate reply  │  │ • Reformulate    │ │
│ • Add citations   │  │ • Try again      │ │
│ • Return to user  │  │   ────┐          │ │
└─────────┬─────────┘  └────────┼──────────┘ │
          │                     │            │
          │                     ▼            │
          │         ┌───────────────────┐    │
          │         │ Back to Step 2    │    │
          │         │ (with new query)  │    │
          │         └───────────────────┘    │
          │                                  │
          └──────────────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────┐
                  │  6. FINAL ANSWER │
                  │                  │
                  │  Delivered to    │
                  │  user with       │
                  │  source citations│
                  └──────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║                              KEY COMPONENTS                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────┐
│  GRAPH NODES        │
├─────────────────────┤
│ • generate_query_or_respond  → Decides whether to retrieve
│ • retrieve                   → Queries Supabase vectorstore
│ • grade_documents            → Validates relevance
│ • rewrite_question           → Improves query
│ • generate_answer            → Creates final response
└─────────────────────┘

┌─────────────────────┐
│  GRAPH EDGES        │
├─────────────────────┤
│ • Conditional edges  → Smart routing based on LLM decisions
│ • Fixed edges        → Direct connections between nodes
│ • tools_condition    → Routes to retrieve or end based on tool calls
└─────────────────────┘

┌─────────────────────┐
│  EXTERNAL SERVICES  │
├─────────────────────┤
│ • Supabase           → Vectorstore with document chunks
│ • OpenAI/Groq        → LLM for generation and grading
│ • HuggingFace        → Embeddings model
└─────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║                           EXAMPLE SCENARIOS                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

SCENARIO 1: Simple Greeting
────────────────────────────
User: "Hello!"
  → generate_query_or_respond: No retrieval needed
  → Direct answer: "Hello! How can I help you today?"
  
SCENARIO 2: Document Query (Relevant)
──────────────────────────────────────
User: "What services does Vecinita offer?"
  → generate_query_or_respond: Need to retrieve
  → retrieve: Find 5 docs about Vecinita services
  → grade_documents: Documents are relevant ✓
  → generate_answer: "Vecinita offers..." (with citations)

SCENARIO 3: Document Query (Not Relevant)
──────────────────────────────────────────
User: "What is the population of Mars?"
  → generate_query_or_respond: Need to retrieve
  → retrieve: No relevant docs found
  → grade_documents: Documents not relevant ✗
  → rewrite_question: "population statistics Mars"
  → generate_query_or_respond: Retrieve again
  → (loop until relevant or respond with "no answer")

╔═══════════════════════════════════════════════════════════════════════════╗
║                          PERFORMANCE METRICS                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

Typical Response Times:
  • Simple question (no retrieval): ~1s
  • With retrieval (relevant docs): ~2s
  • With rewrite (1 iteration): ~3s
  • With rewrite (2 iterations): ~4s

Database Queries:
  • No retrieval path: 0 queries
  • Successful retrieval: 1 query
  • With 1 rewrite: 2 queries
  • With 2 rewrites: 3 queries

LLM API Calls:
  • No retrieval path: 1 call
  • Successful retrieval: 3 calls (decide, grade, answer)
  • With 1 rewrite: 5 calls (decide, grade, rewrite, decide, answer)
"""


def print_diagram():
    """Print the workflow diagram."""
    print(WORKFLOW_DIAGRAM)


if __name__ == "__main__":
    print_diagram()
