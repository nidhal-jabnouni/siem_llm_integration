from typing import List, Dict, Any
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from src.application.tools.logger import logger

def update_documents(db: Dict[str, Any], documents: List[Document]) -> bool:
    """
    Update documents in the Chroma database with direct embedding management.
    
    Args:
        db: Dictionary containing Chroma client, collection and embedding function
        documents: List of documents to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Updating {len(documents)} documents in Chroma")
        
        collection = db["collection"]
        embedding_function = db["embedding_function"]
        
        # Prepare the data
        docs_content = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate embeddings for all documents
        embeddings = embedding_function.embed_documents(docs_content)
        
        # Get existing IDs without using 'ids' in include parameter
        existing_data = collection.get(include=[])  # Empty list gets minimal data including IDs
        existing_ids = existing_data["ids"]
        
        if len(existing_ids) >= len(documents):
            # Use existing IDs for update
            ids = existing_ids[:len(documents)]
        else:
            # Generate new IDs for any additional documents
            existing_count = len(existing_ids)
            new_ids = [f"doc_{i+existing_count}" for i in range(len(documents) - existing_count)]
            ids = existing_ids + new_ids
        
        # Delete existing documents first
        if existing_ids:
            collection.delete(ids=existing_ids)
        
        # Add documents with new embeddings
        collection.add(
            documents=docs_content,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully updated {len(documents)} documents in Chroma")
        return True
    except Exception as e:
        logger.error(f"Error updating documents in Chroma: {e}", exc_info=True)
        return False