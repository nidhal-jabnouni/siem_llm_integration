from typing import List, Dict, Any
from src.infrastructure.database.search_logs import search_logs
from src.infrastructure.database.load_chroma import load_chroma
from src.infrastructure.embeddings.embedder import get_azure_embedding
from src.infrastructure.database.get_all_documents import get_all_documents
from src.application.tools.logger import logger


def search_indexed_logs(config, query: str, k: int = 5):
    """Search indexed logs."""
    try:
        logger.info(f"Searching logs with query: '{query}'")
        
        # Get embeddings
        embedding = get_azure_embedding()
        
        # Load vector database
        db = load_chroma(embedding, config.persist_directory)
        
        # Search
        results = search_logs(db, query, k)
        
        # Display results
        print(f"\nSearch results for: '{query}'")
        print("=" * 50)
        docs = get_all_documents(db)
    
        
        f
        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Score: {result['similarity_score']:.4f}):")
            print("-" * 40)
            print(result['content'])
            print("-" * 40)
        
        return True
        
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return False