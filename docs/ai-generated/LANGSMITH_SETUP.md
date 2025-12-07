---
title: LangSmith Integration Guide
description: Setting up LangSmith for Evaluations, Tracing, and Monitoring
---

# LangSmith Integration Guide

This guide explains how to use LangSmith with the Vecinita RAG agent for comprehensive tracing, monitoring, and evaluation of your AI application.

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Configuration](#configuration)
4. [Running with Tracing](#running-with-tracing)
5. [Using the LangSmith Dashboard](#using-the-langsmith-dashboard)
6. [Evaluation](#evaluation)
7. [Troubleshooting](#troubleshooting)

## Overview

LangSmith is a comprehensive platform for observability, debugging, and evaluation of LLM applications. With Vecinita integrated with LangSmith, you can:

- **Trace**: Capture detailed execution traces of all agent runs
- **Monitor**: Track performance metrics and identify issues
- **Evaluate**: Systematically evaluate agent responses
- **Debug**: Inspect inputs, outputs, and intermediate steps
- **Compare**: A/B test different configurations

### Current Project Configuration

- **Project Name**: `pr-trustworthy-sundial-70`
- **Endpoint**: `https://api.smith.langchain.com`
- **Dashboard**: https://smith.langchain.com/projects/pr-trustworthy-sundial-70

## Setup

### Step 1: Install Dependencies

The required packages are already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install the core LangSmith packages directly:

```bash
pip install --pre -U langchain langchain-openai langsmith
```

### Step 2: Configure Environment Variables

All LangSmith configuration is in your `.env` file:

```env
# LangSmith Configuration
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=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
LANGSMITH_PROJECT=pr-trustworthy-sundial-70

# OpenAI API for LLM access
OPENAI_API_KEY=sk-proj-...your-key...
```

**Important**: Keep your API keys secure and never commit them to version control.

## Configuration

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `LANGSMITH_TRACING` | `true` | Enable/disable tracing |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | LangSmith API endpoint |
| `LANGSMITH_API_KEY` | `lsv2_pt_...` | Authentication key for LangSmith |
| `LANGSMITH_PROJECT` | `pr-trustworthy-sundial-70` | Project for organizing traces |

### Module: `src/langsmith_config.py`

This module handles LangSmith initialization:

```python
from langsmith_config import initialize_langsmith

# Initialize LangSmith
config = initialize_langsmith()
print(config['status'])  # "configured" or error message
```

### Integration in `src/main.py`

LangSmith is automatically initialized when the FastAPI app starts:

```python
from langsmith_config import initialize_langsmith

# This runs on startup
langsmith_config = initialize_langsmith()
print(f"[INFO] LangSmith Status: {langsmith_config['status']}")
```

## Running with Tracing

### Option 1: FastAPI Server (Automatic Tracing)

When you start the FastAPI server, all agent runs are automatically traced:

```bash
python -m src.main
# or
python scripts/run_fastapi.py
```

Check the console output:
```
[INFO] LangSmith Status: configured
[INFO] Traces will be sent to project: pr-trustworthy-sundial-70
```

### Option 2: Example Agent Script

Run the example agent to see tracing in action:

```bash
python scripts/langsmith_agent_example.py
```

This script demonstrates:
- Creating a tool-using agent
- Handling multiple queries
- Automatic trace capture
- Linking to dashboard

### Option 3: Custom Script

For custom scripts, ensure `LANGSMITH_TRACING=true`:

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Verify tracing is enabled
print(f"Tracing enabled: {os.getenv('LANGSMITH_TRACING')}")

# LangChain automatically uses LangSmith when:
# 1. LANGSMITH_TRACING=true
# 2. LANGSMITH_API_KEY is set
# 3. LANGSMITH_ENDPOINT is configured

model = ChatOpenAI(model="gpt-4o-mini")
response = model.invoke("Hello!")

# This will be automatically traced to LangSmith!
```

## Using the LangSmith Dashboard

### Accessing Your Project

Visit: https://smith.langchain.com/projects/pr-trustworthy-sundial-70

### What You'll See

1. **Runs**: All traces of agent execution
   - Input/output
   - Token usage
   - Execution time
   - Tool calls

2. **Datasets**: Test data for evaluation
   - Import your test cases
   - Create custom datasets

3. **Evaluators**: Custom evaluation functions
   - Define success criteria
   - Automated evaluation

4. **Feedback**: Manual feedback loops
   - Thumbs up/down
   - Custom scores
   - Comments

### Interpreting Traces

Each trace shows:

```
├── Input
│   └── {question: "What services does Vecinita offer?"}
├── LLM Call
│   ├── Model: gpt-4o-mini
│   ├── Tokens: 450/50
│   └── Time: 1.2s
├── Tool Calls
│   ├── Tool: search_vecinita_faq
│   ├── Input: {question: "..."}
│   └── Output: [document snippets]
└── Output
    └── {answer: "..."}
```

## Evaluation

### Creating Datasets

1. Go to the **Datasets** tab
2. Click **Create Dataset**
3. Import your test cases (JSON format)

Example format:
```json
{
  "name": "vecinita_qa_tests",
  "examples": [
    {
      "input": {"question": "What is Vecinita?"},
      "expected_output": {"answer": "...community organization..."}
    },
    {
      "input": {"question": "What services are offered?"},
      "expected_output": {"answer": "...education, healthcare..."}
    }
  ]
}
```

### Running Evaluations

```python
from langsmith import evaluate
from src.rag_agent import RAGAgent

# Define evaluation criteria
def evaluate_answer_quality(output):
    # Custom evaluation logic
    return {
        "score": 0.8,
        "reasoning": "Answer is accurate and relevant"
    }

# Run evaluation on dataset
results = evaluate(
    lambda q: RAGAgent().ask(q["question"]),
    data="vecinita_qa_tests",
    evaluators=[evaluate_answer_quality]
)
```

## Troubleshooting

### Traces Not Appearing

**Problem**: Traces don't show up in the dashboard

**Solutions**:

1. Verify environment variables:
```bash
echo $LANGSMITH_TRACING
echo $LANGSMITH_API_KEY
echo $LANGSMITH_PROJECT
```

2. Check that tracing is enabled:
```python
import os
print(os.getenv("LANGSMITH_TRACING"))  # Should be "true"
```

3. Verify API key is correct:
```bash
curl -H "x-api-key: $LANGSMITH_API_KEY" \
  https://api.smith.langchain.com/info
```

4. Check console logs when starting the app:
```
[INFO] LangSmith Status: configured
[INFO] Traces will be sent to project: pr-trustworthy-sundial-70
```

### Authentication Error

**Problem**: `401 Unauthorized` error

**Solution**: Verify API key:
```bash
export LANGSMITH_API_KEY=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
```

### No Tool Calls Captured

**Problem**: Tool executions don't appear in traces

**Solution**: Ensure tools are properly defined with `@tool` decorator:

```python
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """Tool description for LLM"""
    return "output"
```

### Performance Issues

**Problem**: Slow responses

**Solution**: Disable detailed tracing for high-throughput scenarios:

```bash
export LANGSMITH_TRACING=false
# Or in Python:
os.environ["LANGSMITH_TRACING"] = "false"
```

## Advanced Features

### Custom Metadata

Add metadata to traces:

```python
from langsmith import trace

@trace(metadata={"version": "1.0", "model": "gpt-4o-mini"})
def my_agent_run(question: str):
    # Your code here
    pass
```

### Feedback Collection

```python
from langsmith import client

# Add feedback to a run
client.create_feedback(
    run_id="your-run-id",
    key="manual_review",
    score=0.95,
    comment="Good response"
)
```

### Comparing Versions

1. Create two versions of your agent
2. Run both on the same dataset
3. Use LangSmith dashboard to compare results
4. Choose the better-performing version

## Resources

- **LangSmith Documentation**: https://docs.smith.langchain.com/
- **LangChain Documentation**: https://python.langchain.com/
- **Your Project Dashboard**: https://smith.langchain.com/projects/pr-trustworthy-sundial-70
- **LangSmith API Reference**: https://api.smith.langchain.com/redoc

## Next Steps

1. ✅ Configure environment variables (done)
2. ✅ Install dependencies (done)
3. ✅ Run the FastAPI server
4. Check the LangSmith dashboard
5. Create test datasets
6. Set up evaluators
7. Run comparative evaluations
8. Iterate and improve

---

**Last Updated**: December 6, 2025
**Project**: Vecinita RAG Q&A System
**Contact**: Development Team
