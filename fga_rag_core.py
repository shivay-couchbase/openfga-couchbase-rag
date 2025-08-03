import asyncio
import requests
import json
import os
from dotenv import load_dotenv
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import CouchbaseException
from couchbase.vector_search import VectorQuery, VectorSearch
from couchbase.search import SearchRequest, MatchNoneQuery
from unstructured.partition.auto import partition
from openai import OpenAI
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

class FGA_Secured_RAG:
    def __init__(self):
        # Load configuration from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.couchbase_connection_string = os.getenv('CB_CONNECTION_STRING')
        self.couchbase_username = os.getenv('CB_USERNAME')
        self.couchbase_password = os.getenv('CB_PASSWORD')
        self.bucket_name = os.getenv('CB_BUCKET')
        self.scope_name = os.getenv('CB_SCOPE', '_default')
        self.collection_name = os.getenv('CB_COLLECTION')
        self.fga_api_url = os.getenv('FGA_API_URL')
        self.fga_store_id = os.getenv('FGA_STORE_ID')
        self.fga_api_token = os.getenv('FGA_API_TOKEN')
        self.authorization_model_id = os.getenv('FGA_AUTHORIZATION_MODEL_ID')
        self.search_index_name = os.getenv('CB_INDEX', 'vector_search_fga')
        
        # Validate required environment variables
        required_vars = [
            'OPENAI_API_KEY', 'CB_CONNECTION_STRING', 'CB_USERNAME', 
            'CB_PASSWORD', 'CB_BUCKET', 'CB_COLLECTION', 'FGA_API_URL',
            'FGA_STORE_ID', 'FGA_AUTHORIZATION_MODEL_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize clients and connections
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.cluster = None
        self.collection = None
        self.scope = None
        self._connect_to_couchbase()

    def _connect_to_couchbase(self):
        """Connect to Couchbase cluster and get collection reference"""
        try:
            # Create cluster connection
            auth = PasswordAuthenticator(self.couchbase_username, self.couchbase_password)
            cluster_options = ClusterOptions(auth)
            self.cluster = Cluster(self.couchbase_connection_string, cluster_options)
            
            # Get bucket, scope and collection
            bucket = self.cluster.bucket(self.bucket_name)
            self.scope = bucket.scope(self.scope_name)
            self.collection = self.scope.collection(self.collection_name)
            
            print(f"Connected to Couchbase cluster: {self.couchbase_connection_string}")
            print(f"Using bucket: {self.bucket_name}, scope: {self.scope_name}, collection: {self.collection_name}")
        except CouchbaseException as e:
            print(f"Failed to connect to Couchbase: {e}")
            raise

    def generate_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embeddings for text using OpenAI"""
        return self.openai_client.embeddings.create(input=[text], model=model).data[0].embedding

    def get_authorized_documents(self, user_id: str) -> List[str]:
        """Get list of document IDs that the user has permission to view using OpenFGA ListObjects"""
        url = f"{self.fga_api_url}/stores/{self.fga_store_id}/list-objects"
        headers = {
            "Authorization": f"Bearer {self.fga_api_token}",
            "content-type": "application/json",
        }
        data = {
            "authorization_model_id": self.authorization_model_id,
            "user": f"user:{user_id}",
            "relation": "viewer",
            "type": "doc"
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()
            
            # Extract document IDs from the response
            authorized_docs = []
            if 'objects' in result:
                for obj in result['objects']:
                    # Remove the "doc:" prefix to get the actual document ID
                    doc_id = obj.replace("doc:", "")
                    authorized_docs.append(doc_id)
            
            return authorized_docs
        except requests.exceptions.RequestException as e:
            print(f"Error getting authorized documents: {e}")
            return []

    def search_authorized_documents(self, query: str, user_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents using the pre-query filtering pattern"""
        try:
            # Step 1: Get authorized document IDs from OpenFGA
            authorized_docs = self.get_authorized_documents(user_id)
            
            if not authorized_docs:
                print(f"No authorized documents found for user: {user_id}")
                return []
            
            # Step 2: Generate embedding for search query
            query_embedding = self.generate_embeddings(query, "text-embedding-ada-002")
            
            # Step 3: Perform vector search with metadata filter for authorized documents
            search_req = SearchRequest.create(MatchNoneQuery()).with_vector_search(
                VectorSearch.from_vector_query(
                    VectorQuery("embedding", query_embedding, num_candidates=top_k * 2)
                )
            )
            
            # Execute search
            result = self.scope.search(self.search_index_name, search_req)
            rows = list(result.rows())
            
            # Step 4: Filter results to only include authorized documents
            authorized_results = []
            for row in rows:
                try:
                    # Get the full document
                    doc = self.collection.get(row.id)
                    if doc and doc.value:
                        doc_content = doc.value
                        doc_source = doc_content.get("source", "")
                        
                        # Check if this document is in the authorized list
                        if doc_source in authorized_docs:
                            authorized_results.append({
                                "id": row.id,
                                "text": doc_content.get("text", ""),
                                "source": doc_source,
                                "score": row.score,
                                "metadata": doc_content.get("metadata", {})
                            })
                            
                            # Stop if we have enough results
                            if len(authorized_results) >= top_k:
                                break
                                
                except Exception as doc_error:
                    print(f"Could not fetch document {row.id}: {doc_error}")
            
            return authorized_results
                    
        except CouchbaseException as e:
            print(f"Search failed: {e}")
            return []

    def generate_rag_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate RAG response using OpenAI with authorized context"""
        if not context_docs:
            return "I don't have access to any relevant information to answer your question."
        
        # Prepare context from authorized documents
        context_text = "\n\n".join([doc["text"] for doc in context_docs])
        
        # Create system prompt
        system_prompt = """You are a helpful assistant with access to authorized documents. 
        Only use the information provided in the context to answer questions. 
        If the context doesn't contain enough information to answer the question, 
        say so clearly. Do not make up information."""
        
        # Create user prompt
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Sorry, I encountered an error while generating the response."

    def process_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """Main method to process a query with FGA authorization"""
        # Step 1: Search for authorized documents
        authorized_docs = self.search_authorized_documents(query, user_id)
        
        # Step 2: Generate response using authorized context
        response = self.generate_rag_response(query, authorized_docs)
        
        return {
            "query": query,
            "user_id": user_id,
            "authorized_documents_count": len(authorized_docs),
            "authorized_documents": [{"source": doc["source"], "score": doc["score"]} for doc in authorized_docs],
            "response": response
        }

    def setup_demo_data(self):
        """Setup demo documents and permissions"""
        # Create demo documents
        demo_docs = {
            "titan_marketing": {
                "text": "Project Titan is an innovative initiative focused on developing cutting-edge technology solutions. The project aims to revolutionize how organizations handle data processing and analytics. Our marketing strategy emphasizes the user-friendly interface and powerful capabilities that make Project Titan stand out in the competitive landscape.",
                "source": "titan_marketing"
            },
            "titan_spec": {
                "text": "Project Titan Engineering Specifications: The project has been allocated a budget of $2.5 million for development and implementation. Key technical requirements include scalable architecture, real-time processing capabilities, and integration with existing enterprise systems. The development timeline is set for 18 months with quarterly milestones.",
                "source": "titan_spec"
            }
        }
        
        # Clear existing documents
        print("Clearing existing documents...")
        query = f"SELECT META().id FROM `{self.bucket_name}`.`{self.scope_name}`.`{self.collection_name}`"
        result = self.cluster.query(query)
        for row in result:
            self.collection.remove(row['id'])
        
        # Insert demo documents
        print("Inserting demo documents...")
        for doc_id, content in demo_docs.items():
            doc_content = {
                "text": content["text"],
                "embedding": self.generate_embeddings(content["text"], "text-embedding-ada-002"),
                "metadata": {
                    "type": "demo_document",
                    "created_by": "system"
                },
                "source": content["source"]
            }
            self.collection.insert(doc_id, doc_content)
        
        print("Demo data setup completed.")

    def setup_permissions(self):
        """Setup demo permissions in OpenFGA"""
        # Setup permissions for intern_ashish (only marketing)
        self.add_tuple("intern_ashish", "titan_marketing")
        
        # Setup permissions for pm_kate (both documents)
        self.add_tuple("pm_kate", "titan_marketing")
        self.add_tuple("pm_kate", "titan_spec")
        
        print("Demo permissions setup completed.")

    def add_tuple(self, user: str, resource: str):
        """Add permission tuple to OpenFGA"""
        url = f"{self.fga_api_url}/stores/{self.fga_store_id}/write"
        headers = {
            "Authorization": f"Bearer {self.fga_api_token}",
            "content-type": "application/json",
        }
        data = {
            "writes": {
                "tuple_keys": [
                    {
                        "user": f"user:{user}",
                        "relation": "viewer",
                        "object": f"doc:{resource}"
                    }
                ]
            },
            "authorization_model_id": self.authorization_model_id
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            print(f"Added permission: user:{user} -> viewer -> doc:{resource}")
        except requests.exceptions.RequestException as e:
            print(f"Error adding permission: {e}")

    def initialize_demo(self):
        """Initialize the demo with data and permissions"""
        print("Initializing demo...")
        self.setup_demo_data()
        self.setup_permissions()
        print("Demo initialization completed.") 