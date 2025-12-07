# Local LLM Setup Guide

## Overview

Vecinita now supports a **local LLM fallback** using Ollama. This means:

1. **Primary**: Groq API (fast, free tier)
2. **Fallback**: OpenAI API (reliable, paid)
3. **Final Fallback**: Ollama (local, completely offline, free)

The system will automatically try each provider in order until one succeeds.

## Why Use Local LLM?

- ✅ **No API costs** - runs completely on your machine
- ✅ **No quota limits** - unlimited requests
- ✅ **Offline support** - works without internet
- ✅ **Privacy** - your data never leaves your machine
- ✅ **Automatic fallback** - kicks in when API services fail

## Installation Steps

### 0. Install Python Package

First, ensure the langchain-ollama package is installed:

```powershell
# With uv (recommended)
uv add langchain-ollama

# Or with pip
pip install langchain-ollama
```

### 1. Install Ollama

**Windows:**
```powershell
# Download and run the installer
# Visit: https://ollama.ai/download/windows
```

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Service

```powershell
# Ollama runs as a background service after installation
# It starts automatically on system boot
# Default URL: http://localhost:11434
```

### 3. Pull a Model

```powershell
# Download the recommended model (about 2GB)
ollama pull llama3.2

# Or try other models:
ollama pull llama3.1   # Larger, more capable
ollama pull mistral    # Alternative model
ollama pull phi        # Smaller, faster
```

### 4. Verify Installation

```powershell
# Test that Ollama is running
ollama list

# Test generation
ollama run llama3.2 "Hello, how are you?"
```

### 5. Configure Vecinita (Optional)

The default configuration works out of the box, but you can customize:

```env
# .env file
OLLAMA_BASE_URL=http://localhost:11434  # Default
OLLAMA_MODEL=llama3.2                    # Default

# To use a different model:
OLLAMA_MODEL=llama3.1
# or
OLLAMA_MODEL=mistral
```

## How It Works

When you run Vecinita:

1. **API Keys Present**: Uses Groq/OpenAI normally
   - Ollama is available as silent fallback
   
2. **API Keys Fail** (quota exceeded, invalid, rate limited):
   - Automatically switches to local Ollama
   - No configuration needed
   
3. **No API Keys**: Uses Ollama as primary
   - Works completely offline

## Testing the Fallback

### Test Automatic Fallback

```powershell
# Temporarily invalidate your API keys in .env
GROQ_API_KEY=invalid
OPEN_API_KEY=invalid

# Start the server
uvicorn src.main:app --reload

# Make a request - should use Ollama
curl "http://localhost:8000/ask?question=Hello"
```

### Test Ollama Directly

```powershell
# Run Ollama standalone
ollama run llama3.2

# Type your questions
>>> What is RAG?
>>> How do embeddings work?
```

## Performance Comparison

| Provider | Speed | Cost | Offline | Quality |
|----------|-------|------|---------|---------|
| **Groq** | ⚡⚡⚡ Fast | Free (limited) | ❌ | ⭐⭐⭐⭐ |
| **OpenAI** | ⚡⚡ Medium | $$ Paid | ❌ | ⭐⭐⭐⭐⭐ |
| **Ollama** | ⚡ Slow | Free | ✅ | ⭐⭐⭐ |

*Speed depends on your hardware. GPU recommended for better performance.*

## Troubleshooting

### "Ollama not available or not running"

```powershell
# Check if Ollama service is running
ollama list

# Restart Ollama
# Windows: Restart from system tray
# macOS/Linux: sudo systemctl restart ollama
```

### "Model not found"

```powershell
# Pull the model
ollama pull llama3.2

# Verify it's available
ollama list
```

### Slow Responses

Ollama performance depends on your hardware:
- **CPU only**: 30-60 seconds per response
- **With GPU**: 3-10 seconds per response

To improve performance:
1. Use a smaller model: `OLLAMA_MODEL=phi`
2. Close other applications
3. Upgrade to a machine with GPU

### Change Model

```powershell
# See available models
ollama list

# Pull a different model
ollama pull mistral

# Update .env
OLLAMA_MODEL=mistral

# Restart server
```

## Advanced Configuration

### Use Remote Ollama Server

```env
# .env file
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
```

### Disable Local Fallback

If you don't want to use Ollama even if installed:

```python
# In src/main.py, comment out:
# llm_local = Ollama(...)
```

## Model Recommendations

| Model | Size | Use Case |
|-------|------|----------|
| **llama3.2** | 2GB | Default, good balance |
| **llama3.1** | 4GB | Better quality, slower |
| **mistral** | 4GB | Alternative, creative |
| **phi** | 1.6GB | Fast, good for simple tasks |
| **llama2** | 4GB | Reliable, stable |

## System Requirements

**Minimum:**
- 8GB RAM
- 5GB disk space
- CPU: 4+ cores

**Recommended:**
- 16GB+ RAM
- 10GB disk space
- NVIDIA GPU with 6GB+ VRAM
- CPU: 8+ cores

## Next Steps

1. ✅ Install Ollama
2. ✅ Pull a model
3. ✅ Test the fallback
4. ✅ Configure your preferred model
5. ✅ Run Vecinita worry-free!

## Resources

- [Ollama Official Site](https://ollama.ai)
- [Ollama Models Library](https://ollama.ai/library)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [LangChain Ollama Integration](https://python.langchain.com/docs/integrations/llms/ollama)
