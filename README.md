#  FGA-Secured RAG Demo

A comprehensive demonstration of Fine-Grained Authorization (FGA) in RAG (Retrieval-Augmented Generation) pipelines using OpenFGA, Couchbase, and OpenAI.

## Demo Scenario

This application demonstrates how to secure a RAG pipeline at a granular level using **Project Titan** as a corporate use case:

- **Document: `titan_marketing`** - Public marketing brief
- **Document: `titan_spec`** - Confidential engineering specifications with budget details
- **User: `intern_ashish`** - New intern with access to public information only
- **User: `pm_kate`** - Product Manager with access to all project documents

## Architecture

This demo implements the **Pre-Query Filtering** pattern for maximum efficiency and security:

1. **OpenFGA** determines user permissions using ListObjects API
2. **Couchbase** performs vector search only on authorized documents
3. **OpenAI** generates responses from secure, pre-filtered context

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Couchbase Capella account
- OpenFGA Server
- OpenAI API key

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

### 2. Environment Configuration

Copy the environment example and configure your settings:

```bash
cp env_example.txt .env
```

Edit `.env` with your actual configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Couchbase Configuration
CB_CONNECTION_STRING=couchbase://localhost
CB_USERNAME=Administrator
CB_PASSWORD=password
CB_BUCKET=fga_demo
CB_SCOPE=_default
CB_COLLECTION=documents
CB_INDEX=vector_search_fga

# OpenFGA Configuration
FGA_API_URL=http://localhost:8080
FGA_STORE_ID=your_store_id_here
FGA_API_TOKEN=your_api_token_here
FGA_AUTHORIZATION_MODEL_ID=your_model_id_here
```

### 3. Setup OpenFGA

```bash
npm run setup-openfga
```

This will:
- Create the authorization model
- Set up demo permissions
- Display configuration information

### 4. Setup Couchbase Capella

1. Create a bucket named `fga_demo` in your Capella dashboard
2. Run the setup script to create collection and search index:
   ```bash
   python3 setup_couchbase_capella.py
   ```

### 5. Launch the Application

```bash
npm run start-streamlit
```

Or directly:

```bash
streamlit run streamlit_app.py
```

## Using the Demo

### 1. Initialize Demo Data

Click the "Initialize Demo Data" button in the sidebar to set up:
- Demo documents in Couchbase
- User permissions in OpenFGA
- Vector embeddings for search

### 2. Test Different Users

Switch between users in the sidebar:
- **Ashish (Intern)**: Can only access marketing document
- **Kate (Product Manager)**: Can access both documents

### 3. Ask Questions

Try asking: **"What is the budget for Project Titan?"**

Observe how different users get different responses based on their permissions!

## 📁 Project Structure

```
final-fga/
├── streamlit_app.py          # Main Streamlit frontend
├── fga_rag_core.py          # Core RAG engine with FGA integration
├── demo.py                  # Original demo script
├── setup_openfga.js         # OpenFGA setup script
├── requirements.txt         # Python dependencies
├── package.json            # Node.js dependencies
├── env_example.txt         # Environment variables template
├── README.md               # This file
├── design-spec.md          # Original design specification
└── architecture-pattern.md # Architecture documentation
```

## Technical Details

### Core Components

#### `FGA_Secured_RAG` Class
- **`get_authorized_documents()`**: Uses OpenFGA ListObjects API
- **`search_authorized_documents()`**: Pre-query filtering implementation
- **`generate_rag_response()`**: OpenAI integration with secure context
- **`process_query()`**: Main orchestration method

#### Streamlit Frontend
- **User selection**: Switch between demo personas
- **Query interface**: Natural language question input
- **Results display**: Shows response, metrics, and security info
- **Demo controls**: Initialize data and permissions

### Security Flow

1. **User submits query** → Streamlit frontend
2. **Get authorized documents** → OpenFGA ListObjects API
3. **Vector search** → Couchbase (filtered by authorized docs)
4. **Generate response** → OpenAI (with secure context)
5. **Display results** → Streamlit with security metrics

## Testing

Run the original demo script:

```bash
npm run demo
```

Or run tests (when implemented):

```bash
npm run test
```

##  Additional Resources

- [OpenFGA Documentation](https://openfga.dev/)
- [Couchbase Vector Search](https://docs.couchbase.com/server/current/vector-search/vector-search.html)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
