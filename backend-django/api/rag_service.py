"""
Improved RAG Service using LlamaIndex for better document retrieval
No API keys needed for LlamaIndex itself - it's just a framework!
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
    Document as LlamaDocument
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)


class ImprovedRAGService:
    """
    Improved RAG service using LlamaIndex
    
    Benefits:
    - Better chunking strategies
    - Automatic metadata extraction
    - Query transformations
    - Response synthesis
    - No API keys needed (uses local models by default)
    """
    
    def __init__(self):
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY', '')
        self.collection_name = os.getenv('COLLECTION_NAME', 'docs')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        
        # Initialize Qdrant client
        try:
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key if self.qdrant_api_key else None
            )
            logger.info(f"Connected to Qdrant at {self.qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.qdrant_client = None
        
        # Configure LlamaIndex settings
        self._configure_llama_index()
        
        # Initialize vector store
        self.vector_store = None
        self.index = None
        if self.qdrant_client:
            self._initialize_vector_store()
    
    def _configure_llama_index(self):
        """Configure LlamaIndex with appropriate models"""
        # Use local HuggingFace embeddings (no API key needed!)
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Configure LLM
        if self.openai_api_key:
            Settings.llm = LlamaOpenAI(
                api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0
            )
            logger.info("Using OpenAI LLM")
        else:
            # Use a simple stub LLM (no API key needed)
            from llama_index.core.llms import MockLLM
            Settings.llm = MockLLM(max_tokens=512)
            logger.info("Using Mock LLM (set OPENAI_API_KEY for real responses)")
        
        # Configure chunking
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        logger.info("LlamaIndex configured successfully")
    
    def _initialize_vector_store(self):
        """Initialize Qdrant vector store"""
        try:
            # Create vector store
            self.vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=self.collection_name
            )
            
            # Try to load existing index
            try:
                storage_context = StorageContext.from_defaults(
                    vector_store=self.vector_store
                )
                self.index = VectorStoreIndex.from_vector_store(
                    self.vector_store,
                    storage_context=storage_context
                )
                logger.info(f"Loaded existing index from collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist yet, will be created on first ingest
                logger.info("No existing index found, will create on first ingest")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
    
    def ingest_documents(self, file_paths: List[tuple]) -> Dict[str, Any]:
        """
        Ingest documents using LlamaIndex
        
        Args:
            file_paths: List of (file_path, filename) tuples
            
        Returns:
            Dict with ingestion results
        """
        if not self.qdrant_client:
            raise Exception("Qdrant client not available")
        
        try:
            documents = []
            doc_ids = []
            
            # Load documents
            for file_path, filename in file_paths:
                try:
                    # Use LlamaIndex's document loader
                    loader = SimpleDirectoryReader(
                        input_files=[file_path]
                    )
                    docs = loader.load_data()
                    
                    # Add metadata
                    for doc in docs:
                        doc.metadata['filename'] = filename
                        doc.metadata['source'] = file_path
                        documents.append(doc)
                        doc_ids.append(doc.doc_id)
                    
                    logger.info(f"Loaded {len(docs)} documents from {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")
                    continue
            
            if not documents:
                return {
                    'doc_ids': [],
                    'chunks_indexed': 0,
                    'files_processed': 0,
                    'error': 'No documents could be loaded'
                }
            
            # Create or update index
            if self.index is None:
                # Create new index
                storage_context = StorageContext.from_defaults(
                    vector_store=self.vector_store
                )
                self.index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    show_progress=True
                )
                logger.info("Created new vector index")
            else:
                # Add to existing index
                for doc in documents:
                    self.index.insert(doc)
                logger.info(f"Added {len(documents)} documents to existing index")
            
            # Count chunks (approximate)
            chunks_count = len(documents) * 2  # Rough estimate
            
            return {
                'doc_ids': [str(doc_id) for doc_id in doc_ids],
                'chunks_indexed': chunks_count,
                'files_processed': len(file_paths),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {
                'doc_ids': [],
                'chunks_indexed': 0,
                'files_processed': 0,
                'error': str(e)
            }
    
    def query(self, question: str, session_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: User's question
            session_context: Optional conversation context
            
        Returns:
            Dict with answer and citations
        """
        if not self.index:
            return {
                'answer': "No documents have been indexed yet. Please upload some documents first.",
                'citations': [],
                'sources': []
            }
        
        try:
            # Build query with context if provided
            full_query = question
            if session_context:
                full_query = f"Context: {session_context}\n\nQuestion: {question}"
            
            # Query the index
            query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="compact"
            )
            
            response = query_engine.query(full_query)
            
            # Extract citations
            citations = []
            sources = []
            
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    metadata = node.node.metadata
                    citation = {
                        'filename': metadata.get('filename', 'unknown'),
                        'page_start': metadata.get('page_label', 1),
                        'page_end': metadata.get('page_label', 1),
                        'chunk_id': node.node.node_id,
                        'score': node.score if hasattr(node, 'score') else 0.0
                    }
                    citations.append(citation)
                    
                    sources.append({
                        'text': node.node.get_content()[:200] + '...',
                        'metadata': metadata
                    })
            
            return {
                'answer': str(response),
                'citations': citations,
                'sources': sources,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                'answer': f"Sorry, I encountered an error: {str(e)}",
                'citations': [],
                'sources': [],
                'error': str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        try:
            if self.qdrant_client and self.index:
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                return {
                    'collection_name': self.collection_name,
                    'vectors_count': collection_info.vectors_count if hasattr(collection_info, 'vectors_count') else 0,
                    'status': 'ready'
                }
            else:
                return {
                    'collection_name': self.collection_name,
                    'vectors_count': 0,
                    'status': 'not_initialized'
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'collection_name': self.collection_name,
                'vectors_count': 0,
                'status': 'error',
                'error': str(e)
            }


# Global instance
_rag_service = None

def get_rag_service() -> ImprovedRAGService:
    """Get or create RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = ImprovedRAGService()
    return _rag_service

