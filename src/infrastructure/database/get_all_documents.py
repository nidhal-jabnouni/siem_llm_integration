from typing import Dict, Any, List
from langchain.schema import Document
from src.application.tools.logger import logger





def get_all_documents(db: Dict[str, Any]) -> List[Document]:
    """
    Retrieve all documents from the Chroma database.
    
    Args:
        db: Dictionary containing Chroma client and collection
        
    Returns:
        List of all documents in the database
    """
    try:
        logger.info("Retrieving all documents from Chroma")
        
        collection = db["collection"]
        
        # Get all items from the collection
        all_data = collection.get(include=["documents", "metadatas", "embeddings"])
        
        # Create Document objects
        documents = []
        for i in range(len(all_data["documents"])):
            doc_content = all_data["documents"][i]
            metadata = all_data["metadatas"][i]
            
            # Add ID to metadata if not present
            if "id" not in metadata:
                metadata["id"] = all_data["ids"][i]
                
            documents.append(Document(page_content=doc_content, metadata=metadata))
            
        logger.info(f"Retrieved {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Error retrieving all documents: {e}")
        raise