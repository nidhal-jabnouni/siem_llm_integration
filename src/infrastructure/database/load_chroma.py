from typing import Any
import os
import chromadb
from langchain.embeddings import Embeddings
from langchain.vectorstores import Chroma
from application.tools.logger import logger

def load_chroma(embedding: Embeddings, persist_path: str = "chroma_logs_db") -> Any:
    """
    Load an existing Chroma database with direct access.
    
    Args:
        embedding: Embedding function to use
        persist_path: Directory where the database is persisted
        
    Returns:
        Chroma client and collection
    """
    try:
        if not os.path.exists(persist_path):
            logger.warning(f"Chroma database directory {persist_path} does not exist")
            raise FileNotFoundError(f"No Chroma database found at {persist_path}")
            
        logger.info(f"Loading Chroma database from {persist_path}")
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=persist_path)
        
        # Get the collection
        collection = client.get_collection("log_embeddings")
        
        return {
            "client": client,
            "collection": collection,
            "embedding_function": embedding
        }
    except Exception as e:
        logger.error(f"Error loading Chroma database: {e}")
        raise
