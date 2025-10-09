#!/bin/bash

# RAG Chatbot Enhanced - Quick Setup Script
# This script sets up the enhanced version of the RAG chatbot

set -e

echo "🚀 RAG Chatbot Enhanced - Setup Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the rag-chatbot root directory"
    exit 1
fi

echo -e "${BLUE}Step 1: Backend Setup${NC}"
echo "----------------------"

# Check Python versionnn
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Setup backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Backend setup complete!${NC}"
echo ""

cd ..

echo -e "${BLUE}Step 2: Frontend Setup${NC}"
echo "----------------------"

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Found Node.js $NODE_VERSION"

# Setup frontend
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install --silent

# Install additional packages for enhanced version
echo "Installing enhanced features packages..."
npm install --silent react-markdown react-syntax-highlighter
npm install --silent --save-dev @types/react-syntax-highlighter

# Backup original page and use enhanced version
if [ -f "app/page.tsx" ] && [ ! -f "app/page-original.tsx" ]; then
    echo "Backing up original page.tsx..."
    cp app/page.tsx app/page-original.tsx
fi

if [ -f "app/page-enhanced.tsx" ]; then
    echo "Switching to enhanced page..."
    cp app/page-enhanced.tsx app/page.tsx
fi

echo -e "${GREEN}✅ Frontend setup complete!${NC}"
echo ""

cd ..

echo -e "${BLUE}Step 3: Database Initialization${NC}"
echo "--------------------------------"

# The database will be created automatically on first run
echo "Database will be created automatically on first backend start"
echo -e "${GREEN}✅ Database setup ready!${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "========================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Start the backend:"
echo -e "   ${YELLOW}cd backend${NC}"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo -e "   ${YELLOW}python app_enhanced.py${NC}"
echo ""
echo "2. In a new terminal, start the frontend:"
echo -e "   ${YELLOW}cd frontend${NC}"
echo -e "   ${YELLOW}npm run dev${NC}"
echo ""
echo "3. Open your browser:"
echo -e "   ${BLUE}http://localhost:3000${NC} - Frontend"
echo -e "   ${BLUE}http://localhost:8000/docs${NC} - API Documentation"
echo ""
echo "📚 Documentation:"
echo "   - IMPLEMENTATION_GUIDE.md - Complete setup and API docs"
echo "   - ENHANCEMENTS_SUMMARY.md - Feature list and statistics"
echo ""
echo "💡 Tips:"
echo "   - Use 'python app_mock.py' for development without Qdrant"
echo "   - Set OPENAI_API_KEY environment variable for real LLM"
echo "   - Toggle dark mode with the moon/sun icon"
echo "   - Click 'Sessions' to view conversation history"
echo "   - Click 'Documents' to manage uploaded files"
echo ""
echo -e "${GREEN}Happy chatting! 🚀${NC}"

