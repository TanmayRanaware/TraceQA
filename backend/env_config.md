# Environment Configuration

## Anthropic Claude API Key Setup

To use the Claude AI integration, you need to set your Anthropic API key as an environment variable.

### Option 1: Set Environment Variable (Recommended)

```bash
export ANTHROPIC_API_KEY="your_actual_api_key_here"
```

### Option 2: Create .env file

Create a `.env` file in the backend directory:

```bash
# backend/.env
ANTHROPIC_API_KEY=your_actual_api_key_here
LLM_PROVIDER=claude
BASE_DIR=object_store
REQ_VERSIONS_DIR=req_versions
MAX_FILE_SIZE=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=10
```

### Option 3: Set in your shell profile

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
echo 'export ANTHROPIC_API_KEY="your_actual_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

## Pinecone Vector Database Setup

The system now uses Pinecone for persistent vector storage. You need to set up Pinecone credentials:

### 1. Get Pinecone API Key

1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Create a new project or use existing one
3. Get your API key from the API Keys section

### 2. Set Pinecone Environment Variables

```bash
export PINECONE_API_KEY="your_pinecone_api_key_here"
export PINECONE_ENVIRONMENT="gcp-starter"  # or your preferred environment
export PINECONE_INDEX_NAME="enterprise-requirements"  # or your preferred index name
```

### 3. Add to .env file

```bash
# backend/.env
ANTHROPIC_API_KEY=your_actual_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=enterprise-requirements
LLM_PROVIDER=claude
BASE_DIR=object_store
REQ_VERSIONS_DIR=req_versions
MAX_FILE_SIZE=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=10
```

## Security Notes

- Never commit your API keys to version control
- The `.env` file is already in `.gitignore`
- Use environment variables for production deployments
- Rotate your API keys regularly

## Testing the Integration

After setting the API keys, restart your backend server and test:

```bash
# Test Claude integration
curl http://localhost:8000/api/requirements/provider-info

# Test Pinecone integration
curl http://localhost:8000/api/vector-db/health
curl http://localhost:8000/api/vector-db/stats
```

You should see:
```json
# Provider info
{
  "provider_type": "ClaudeProvider",
  "provider_class": "<class 'app.providers.claude_provider.ClaudeProvider'>",
  "is_claude": true,
  "is_gemini": false,
  "is_openai": false,
  "is_ollama": false
}

# Vector DB health
{
  "status": "healthy",
  "storage_type": "pinecone",
  "vector_count": 0
}
```

## Fallback Behavior

If Pinecone is not configured or unavailable, the system will automatically fall back to in-memory vector storage. This ensures the system continues to work even without external dependencies.
