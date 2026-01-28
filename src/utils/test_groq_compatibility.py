"""
src/utils/test_groq_compatibility.py
Groq + LangChain Compatibility Tester for Vecinita
Tests if current environment can handle tool calling
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

# Load environment variables from .env
load_dotenv()

# 1. Define a simple test tool
@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

# 2. Check API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ GROQ_API_KEY not found in .env file")
    exit(1)
else:
    print(f"✅ API key loaded (starts with: {api_key[:8]}...)")

# 3. Initialize model
try:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=api_key
    )
    print("✅ Model initialized: llama-3.3-70b-versatile")
except Exception as e:
    print(f"❌ Model init failed: {e}")
    exit(1)

# 4. Bind tool to model
try:
    llm_with_tools = llm.bind_tools([get_word_length])
    print("✅ Tools bound successfully")
except Exception as e:
    print(f"❌ Tool binding failed: {e}")
    print(f"   Your langchain version doesn't support bind_tools()")
    exit(1)

# 5. Test tool invocation
try:
    messages = [HumanMessage(content="How many letters in the word 'Vecinita'?")]
    response = llm_with_tools.invoke(messages)
    print(f"✅ Model response received")
    
    # Check if tool was called
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"✅ Tool call detected: {response.tool_calls}")
        print(f"   Tool name: {response.tool_calls[0]['name']}")
        print(f"   Tool args: {response.tool_calls[0]['args']}")
    else:
        print(f"⚠️  No tool call in response. Raw content: {response.content}")
        
except Exception as e:
    print(f"❌ Invocation failed: {e}")
    print(f"   This is the error you're seeing in production")
    import traceback
    traceback.print_exc()

# 6. Version report
print(f"\n📦 Installed Versions:")
import langchain
import langchain_groq
print(f"   langchain: {langchain.__version__}")
print(f"   langchain-groq: {langchain_groq.__version__}")

try:
    import langgraph
    print(f"   langgraph: {langgraph.__version__}")
except:
    print(f"   langgraph: NOT INSTALLED")

try:
    import pydantic
    print(f"   pydantic: {pydantic.__version__}")
except:
    print(f"   pydantic: NOT INSTALLED")

try:
    import langchain_core
    print(f"   langchain-core: {langchain_core.__version__}")
except:
    print(f"   langchain-core: NOT INSTALLED")

print("\n🔍 Environment Check:")
print(f"   .env file exists: {os.path.exists('.env')}")
print(f"   GROQ_API_KEY is set: {'Yes' if api_key else 'No'}")
## END-OF-FILE
