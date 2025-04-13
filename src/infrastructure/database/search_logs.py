from typing import Dict, Any, List
from langchain_core.documents import Document
from src.application.tools.logger import logger
from langchain_community.vectorstores import Chroma

from langchain_core.embeddings import Embeddings

def search_logs(db: Dict[str, Any], query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search the vector database for relevant log entries using direct embedding.
    
    Args:
        db: Dictionary containing Chroma client, collection and embedding function
        query: Search query
        k: Number of results to return
        
    Returns:
        List of search results with documents and metadata
    """
    try:
        logger.info(f"Searching logs with query: '{query}'")
        
        collection = db["collection"]
        embedding_function = db["embedding_function"]
        
        # Get the total count of documents
        collection_count = collection.count()
        if collection_count == 0:
            logger.warning("No documents found in the collection")
            return []
        
        # Adjust k if needed
        search_k = min(k, collection_count)
        
        # Generate embedding for the query
        query_embedding = embedding_function.embed_query(query)
        
        # Perform the search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=search_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format the results
        formatted_results = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                # Convert distance to similarity score (1.0 - distance)
                similarity = 1.0 - float(results["distances"][0][i])
                
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": similarity
                })
                
        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise
