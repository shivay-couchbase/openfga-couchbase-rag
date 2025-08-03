import streamlit as st
import asyncio
import time
from fga_rag_core import FGA_Secured_RAG
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="FGA-Secured RAG Demo",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .user-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .response-card {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_rag_system():
    """Initialize the RAG system with caching"""
    try:
        rag_system = FGA_Secured_RAG()
        return rag_system
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🔒 FGA-Secured RAG Demo</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Demonstrating Fine-Grained Authorization in RAG Pipelines</p>', unsafe_allow_html=True)
    
    # Sidebar for user selection and controls
    with st.sidebar:
        st.header("👤 User Selection")
        
        # User selection
        selected_user = st.selectbox(
            "Choose your role:",
            ["intern_ashish", "pm_kate"],
            format_func=lambda x: "Ashish (Intern)" if x == "intern_ashish" else "Kate (Product Manager)"
        )
        
        # Display user permissions
        st.subheader("🔑 Your Permissions")
        if selected_user == "intern_ashish":
            st.markdown("""
            - ✅ **titan_marketing** (Public marketing brief)
            - ❌ **titan_spec** (Confidential engineering specs)
            """)
        else:
            st.markdown("""
            - ✅ **titan_marketing** (Public marketing brief)
            - ✅ **titan_spec** (Confidential engineering specs)
            """)
        
        st.divider()
        
        # Demo controls
        st.header("⚙️ Demo Controls")
        
        if st.button("🔄 Initialize Demo Data", type="primary"):
            with st.spinner("Setting up demo data and permissions..."):
                try:
                    rag_system = initialize_rag_system()
                    if rag_system:
                        rag_system.initialize_demo()
                        st.success("Demo data initialized successfully!")
                except Exception as e:
                    st.error(f"Failed to initialize demo: {e}")
        
        st.divider()
        
        # Architecture info
        st.header("🏗️ Architecture")
        st.markdown("""
        This demo implements **Pre-Query Filtering**:
        1. **OpenFGA** determines user permissions
        2. **Couchbase** searches only authorized documents
        3. **OpenAI** generates responses from secure context
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask About Project Titan")
        
        # Query input
        query = st.text_area(
            "Enter your question:",
            placeholder="e.g., What is the budget for Project Titan?",
            height=100
        )
        
        # Submit button
        if st.button("🚀 Submit Query", type="primary", disabled=not query.strip()):
            if query.strip():
                with st.spinner("Processing your query with FGA authorization..."):
                    try:
                        rag_system = initialize_rag_system()
                        if rag_system:
                            # Process the query
                            result = rag_system.process_query(query, selected_user)
                            
                            # Display results
                            st.markdown('<div class="response-card">', unsafe_allow_html=True)
                            st.subheader("🤖 AI Response")
                            st.write(result["response"])
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Display metrics
                            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                            
                            with col_metrics1:
                                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                st.metric("User", selected_user.replace("_", " ").title())
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            with col_metrics2:
                                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                st.metric("Documents Retrieved", result["authorized_documents_count"])
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            with col_metrics3:
                                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                st.metric("Authorization", "✅ Secure")
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Display authorized documents
                            if result["authorized_documents"]:
                                st.subheader("📄 Authorized Documents Used")
                                for doc in result["authorized_documents"]:
                                    st.markdown(f"- **{doc['source']}** (Score: {doc['score']:.3f})")
                            else:
                                st.warning("No authorized documents found for this query.")
                            
                            # Show the difference between users
                            st.subheader("🔍 Security Demonstration")
                            if selected_user == "intern_ashish":
                                st.markdown("""
                                **Ashish (Intern)** can only access the marketing document, 
                                so budget information is not available in the response.
                                """)
                            else:
                                st.markdown("""
                                **Kate (Product Manager)** has access to both documents, 
                                including the confidential engineering specifications with budget details.
                                """)
                                
                    except Exception as e:
                        st.error(f"Error processing query: {e}")
    
    with col2:
        st.header("📊 Demo Scenario")
        
        st.markdown("""
        ### Project Titan Documents:
        
        **📋 titan_marketing**
        - Public marketing brief
        - General project overview
        - No sensitive information
        
        **🔒 titan_spec** 
        - Confidential engineering specs
        - Budget details ($2.5M)
        - Technical requirements
        """)
        
        st.divider()
        
        st.header("🎯 Try This Query")
        st.markdown("""
        Ask: **"What is the budget for Project Titan?"**
        
        Then switch between users to see the difference in responses!
        """)
        
        st.divider()
        
        st.header("🔐 Security Features")
        st.markdown("""
        - ✅ **Pre-query filtering**
        - ✅ **Fine-grained permissions**
        - ✅ **Zero unauthorized data exposure**
        - ✅ **Audit trail ready**
        """)

if __name__ == "__main__":
    main() 