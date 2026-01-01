"""Quick test script to verify sources are returned from the API."""
import requests
import json

# Test the /ask endpoint
url = "http://localhost:8000/ask"
params = {
    "query": "How can I find a doctor who speaks my language?",
    "provider": "llama",
    "thread_id": "test-123"
}

print("Testing /ask endpoint...")
print(f"Query: {params['query']}\n")

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print("✅ Response received successfully\n")
    print(f"Answer: {data.get('answer', '')[:200]}...\n")

    sources = data.get('sources', [])
    print(f"Sources count: {len(sources)}")

    if sources:
        print("\n📚 Sources returned:")
        for i, source in enumerate(sources, 1):
            print(f"\n{i}. {source.get('title', 'Untitled')}")
            print(f"   URL: {source.get('url', 'No URL')}")
            print(f"   Type: {source.get('type', 'unknown')}")
            if source.get('chunkIndex') is not None:
                print(f"   Chunk: {source.get('chunkIndex')}")
    else:
        print("\n⚠️  No sources returned - this is the issue!")
        print("The agent may not be calling tools, or source extraction failed.")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
