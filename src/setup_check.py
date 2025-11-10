#!/usr/bin/env python3
"""
Quick Setup Script for Vecinita LangGraph RAG Agent
This script helps verify your environment and setup
"""

import os
import sys


def check_env_vars():
    """Check if required environment variables are set."""
    print("Checking environment variables...")

    required_vars = {
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_KEY": "Supabase service role key",
    }

    optional_vars = {
        "OPEN_API_KEY": "OpenAI API key (for GPT-4o)",
        "GROQ_API_KEY": "Groq API key (for Llama-3.1)",
    }

    missing = []

    # Check required vars
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  ❌ {var} - {desc}")
        else:
            print(f"  ✅ {var} is set")

    # Check optional vars (need at least one)
    has_model_key = False
    for var, desc in optional_vars.items():
        if os.getenv(var):
            print(f"  ✅ {var} is set")
            has_model_key = True
        else:
            print(f"  ℹ️  {var} - {desc} (optional)")

    if not has_model_key:
        missing.append("  ❌ Need either OPEN_API_KEY or GROQ_API_KEY")

    if missing:
        print("\n⚠️  Missing required environment variables:")
        for m in missing:
            print(m)
        print("\nPlease add these to your .env file")
        return False

    print("\n✅ All required environment variables are set!")
    return True


def check_packages():
    """Check if required packages are installed."""
    print("\nChecking installed packages...")

    packages = [
        "langgraph",
        "langchain",
        "langchain_core",
        "langchain_community",
        "langchain_huggingface",
        "supabase",
        "sentence_transformers",
        "pydantic",
        "dotenv",
    ]

    missing = []

    for package in packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package} - NOT INSTALLED")

    if missing:
        print("\n⚠️  Missing packages. Install with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    print("\n✅ All required packages are installed!")
    return True


def test_supabase_connection():
    """Test connection to Supabase."""
    print("\nTesting Supabase connection...")

    try:
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            print("  ⚠️  Skipping (credentials not set)")
            return False

        client = create_client(url, key)

        # Try a simple query
        response = client.table("document_chunks").select(
            "*").limit(1).execute()

        print(f"  ✅ Connected to Supabase successfully!")
        print(f"  ℹ️  Found {len(response.data)} document(s) in sample query")
        return True

    except Exception as e:
        print(f"  ❌ Failed to connect to Supabase: {e}")
        return False


def test_embeddings():
    """Test embedding model."""
    print("\nTesting embedding model...")

    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedding = model.embed_query("test")

        print(f"  ✅ Embedding model loaded successfully!")
        print(f"  ℹ️  Embedding dimension: {len(embedding)}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to load embedding model: {e}")
        return False


def main():
    """Run all setup checks."""
    print("=" * 70)
    print("Vecinita LangGraph RAG Agent - Setup Verification")
    print("=" * 70)
    print()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file\n")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}\n")

    # Run checks
    checks = [
        ("Environment Variables", check_env_vars),
        ("Python Packages", check_packages),
        ("Supabase Connection", test_supabase_connection),
        ("Embedding Model", test_embeddings),
    ]

    results = {}

    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"  ❌ Error during {name} check: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    print("SETUP SUMMARY")
    print("=" * 70)

    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")

    if all(results.values()):
        print("\n🎉 Your environment is ready to use the RAG agent!")
        print("\nNext steps:")
        print("  1. Run: python example_rag_usage.py")
        print("  2. Read: RAG_AGENT_README.md for more information")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        print("\nQuick fixes:")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - Missing env vars: Add them to your .env file")
        print("  - Supabase issues: Check your credentials and network connection")

    print()


if __name__ == "__main__":
    main()
