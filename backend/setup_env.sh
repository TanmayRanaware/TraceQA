#!/bin/bash

# Setup script for Enterprise Requirements AI
echo "🚀 Setting up Enterprise Requirements AI Environment"

# Check if API keys are provided as arguments
if [ $# -lt 2 ]; then
    echo "❌ Please provide both API keys as arguments"
    echo "Usage: ./setup_env.sh GEMINI_API_KEY PINECONE_API_KEY"
    echo ""
    echo "You can get your API keys from:"
    echo "- Gemini: https://makersuite.google.com/app/apikey"
    echo "- Pinecone: https://app.pinecone.io/"
    exit 1
fi

GEMINI_API_KEY=$1
PINECONE_API_KEY=$2

# Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
# Google AI Studio API Configuration
GEMINI_API_KEY=${GEMINI_API_KEY}

# Pinecone Vector Database Configuration
PINECONE_API_KEY=${PINECONE_API_KEY}
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=enterprise-requirements

# LLM Provider Configuration
LLM_PROVIDER=gemini

# File Storage Configuration
BASE_DIR=object_store
REQ_VERSIONS_DIR=req_versions
MAX_FILE_SIZE=50

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=10
EOF

echo "✅ .env file created successfully"

# Set environment variables for current session
export GEMINI_API_KEY=${GEMINI_API_KEY}
export PINECONE_API_KEY=${PINECONE_API_KEY}
export PINECONE_ENVIRONMENT="gcp-starter"
export PINECONE_INDEX_NAME="enterprise-requirements"

echo "✅ Environment variables set for current session"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p object_store
mkdir -p req_versions
mkdir -p rag_index

echo "✅ Directories created"

# Test the configuration
echo "🧪 Testing configuration..."
python3 -c "
import os
gemini_key = os.environ.get('GEMINI_API_KEY')
pinecone_key = os.environ.get('PINECONE_API_KEY')

if gemini_key:
    print('✅ GEMINI_API_KEY is set')
else:
    print('❌ GEMINI_API_KEY is not set')

if pinecone_key:
    print('✅ PINECONE_API_KEY is set')
else:
    print('❌ PINECONE_API_KEY is not set')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate your virtual environment: source venv/bin/activate"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Start the backend: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo "4. Test the APIs:"
echo "   - Health: curl http://localhost:8000/api/health"
echo "   - Gemini: curl http://localhost:8000/api/requirements/provider-info"
echo "   - Pinecone: curl http://localhost:8000/api/vector-db/health"
echo ""
echo "Note: The .env file is already added to .gitignore for security"
echo ""
echo "🌲 Pinecone will automatically create an index named 'enterprise-requirements'"
echo "   with 768-dimensional vectors optimized for Gemini embeddings"
