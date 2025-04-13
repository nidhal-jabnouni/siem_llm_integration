from typing import List, Any
import os
import chromadb
from langchain.document import Document
from langchain.embeddings import Embeddings
from application.tools.logger import logger

def store_to_chroma(docs: List[Document], embedding: Embeddings, persist_path: str = "chroma_logs_db") -> Any:
    """
    Store documents in Chroma vector database with direct embedding management.
    
    Args:
        docs: List of documents to store
        embedding: Embedding function to use
        persist_path: Directory to persist the database
        
    Returns:
        Chroma client and collection
    """
    try:
        logger.info(f"Storing {len(docs)} documents in Chroma at {persist_path}")
        
        # Ensure directory exists
        os.makedirs(persist_path, exist_ok=True)
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=persist_path)
        
        # Create or get collection
        collection = client.get_or_create_collection("log_embeddings")
        
        # Generate document IDs and prepare data
        documents = [doc.page_content for doc in docs]
        metadatas = [doc.metadata for doc in docs]
        ids = [f"doc_{i}" for i in range(len(docs))]
        
        # Generate embeddings directly using the provided embedding function
        embeddings = embedding.embed_documents(documents)
        
        # Add documents with embeddings to collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info("Successfully stored documents in Chroma")
        
        # Return both client and collection for future operations
        return {
            "client": client,
            "collection": collection,
            "embedding_function": embedding
        }
    except Exception as e:
        logger.error(f"Error storing documents in Chroma: {e}")
        raise