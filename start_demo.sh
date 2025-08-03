#!/bin/bash

# FGA-Secured RAG Demo Startup Script
# This script automates the entire setup and launch process

set -e

echo "🚀 Starting FGA-Secured RAG Demo Setup..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cp env_example.txt .env
    print_warning "Please edit .env file with your actual configuration before continuing."
    print_warning "Press Enter when you're ready to continue..."
    read
fi


# Check if required tools are installed
print_status "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

print_success "Prerequisites check passed!"
print_status "Waiting for OpenFGA to be ready..."
sleep 10

# Step 2: Setup Couchbase Capella
print_status "Step 2: Setting up Couchbase Capella..."
python3 setup_couchbase_capella.py

# Step 3: Install dependencies
print_status "Step 3: Installing Python dependencies..."
pip install -r requirements.txt

print_status "Installing Node.js dependencies..."
npm install

# Step 4: Setup OpenFGA
print_status "Step 4: Setting up OpenFGA..."
npm run setup-openfga

# Step 5: Launch the application
print_status "Step 5: Launching Streamlit application..."
print_success "Demo setup completed! Opening Streamlit app..."
echo ""
echo "🎉 FGA-Secured RAG Demo is ready!"
echo "=================================="
echo ""
echo "📱 Streamlit app will open in your browser at: http://localhost:8501"
echo ""
echo "🎮 How to use the demo:"
echo "   1. Click '🔄 Initialize Demo Data' in the sidebar"
echo "   2. Switch between users: Ashish (Intern) vs Kate (Product Manager)"
echo "   3. Ask: 'What is the budget for Project Titan?'"
echo "   4. Observe different responses based on permissions!"
echo ""
echo "🔧 Services running:"
echo "   - OpenFGA: http://localhost:8080"
echo "   - Couchbase Capella: Your cloud cluster"
echo "   - Streamlit: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Launch Streamlit
streamlit run streamlit_app.py 