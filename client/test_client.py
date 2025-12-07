import sys
import urllib.parse
import requests

API_BASE = "http://localhost:8000"


def ask(question: str):
    if not question:
        print("Please provide a question.")
        return 1
    try:
        params = {"question": question}
        url = f"{API_BASE}/ask?{urllib.parse.urlencode(params)}"
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        print("\n=== Answer ===\n")
        print(data.get("answer", ""))
        ctx = data.get("context", [])
        print("\n=== Context (top) ===\n")
        if not ctx:
            print("No context documents returned.")
        else:
            for i, doc in enumerate(ctx, 1):
                source = doc.get("source", "unknown source")
                content = (doc.get("content", "") or "")[:200]
                print(f"[{i}] Source: {source}\n{content}\n")
        return 0
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return 2


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip() if len(
        sys.argv) > 1 else "What is Vecinita?"
    sys.exit(ask(question))
