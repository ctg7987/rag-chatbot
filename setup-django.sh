#!/bin/bash

# Django Backend Setup Script for RAG Chatbot
# This script sets up the Django backend with LlamaIndex

set -e

echo "🚀 Django RAG Chatbot - Setup Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directoryyy
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ Error: Please run this script from the rag-chatbot root directory${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Django Backend Setup${NC}"
echo "-----------------------------"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"

# Setup Django backend
cd backend-django

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Django and dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

echo -e "${GREEN}✅ Django backend dependencies installed!${NC}"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Django
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
COLLECTION_NAME=docs

# OpenAI (optional)
OPENAI_API_KEY=

# Database
DATABASE_URL=sqlite:///db.sqlite3
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
fi

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo -e "${GREEN}✅ Database setup complete!${NC}"
echo ""

cd ..

echo -e "${BLUE}Step 2: Frontend Setup${NC}"
echo "----------------------"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Found Node.js $NODE_VERSION${NC}"

# Setup frontend (if not already done)
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install --silent
fi

echo -e "${GREEN}✅ Frontend setup complete!${NC}"
echo ""

cd ..

echo -e "${BLUE}Step 3: Optional - Start Qdrant${NC}"
echo "--------------------------------"

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is available. Would you like to start Qdrant? (y/n)${NC}"
    read -t 10 -n 1 -r START_QDRANT || START_QDRANT='n'
    echo ""
    
    if [[ $START_QDRANT =~ ^[Yy]$ ]]; then
        echo "Starting Qdrant..."
        docker run -d -p 6333:6333 -p 6334:6334 \
            --name qdrant-rag \
            qdrant/qdrant:latest 2>/dev/null || echo "Qdrant container already running"
        echo -e "${GREEN}✅ Qdrant started!${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping Qdrant. Document ingestion will be limited.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found. Skipping Qdrant setup.${NC}"
    echo "   Install Docker to use Qdrant: https://docs.docker.com/get-docker/"
fi

echo ""
echo "========================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "========================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Start the Django backend:"
echo -e "   ${YELLOW}cd backend-django${NC}"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo -e "   ${YELLOW}python manage.py runserver 0.0.0.0:8000${NC}"
echo ""
echo "2. In a new terminal, start the frontend:"
echo -e "   ${YELLOW}cd frontend${NC}"
echo -e "   ${YELLOW}npm run dev${NC}"
echo ""
echo "3. Open your browser:"
echo -e "   ${BLUE}http://localhost:3000${NC} - Frontend"
echo -e "   ${BLUE}http://localhost:8000/api/${NC} - API"
echo -e "   ${BLUE}http://localhost:8000/admin/${NC} - Django Admin"
echo ""
echo "📚 Documentation:"
echo "   - DJANGO_SETUP.md - Complete Django setup guide"
echo "   - IMPLEMENTATION_GUIDE.md - Original FastAPI guide"
echo "   - ENHANCEMENTS_SUMMARY.md - Feature list"
echo ""
echo "💡 Key Improvements:"
echo "   ✅ LlamaIndex for better document retrieval"
echo "   ✅ Django ORM with proper database models"
echo "   ✅ Built-in admin panel at /admin/"
echo "   ✅ No API keys needed for basic functionality"
echo "   ✅ Fixed document retrieval issues"
echo ""
echo "🔑 Optional - Add OpenAI API Key:"
echo "   Edit backend-django/.env and set OPENAI_API_KEY"
echo ""
echo "🎯 Create Admin User (Optional):"
echo -e "   ${YELLOW}cd backend-django && source venv/bin/activate${NC}"
echo -e "   ${YELLOW}python manage.py createsuperuser${NC}"
echo ""
echo -e "${GREEN}Happy chatting with Django! 🚀${NC}"

