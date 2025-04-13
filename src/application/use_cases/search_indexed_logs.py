from typing import List, Dict, Any
from infrastructure.database.search_logs import search_logs
from infrastructure.database.load_chroma import load_chroma
from infrastructure.embeddings.embedder import get_azure_embedding
from infrastructure.data_processing.data_preprocessor import get_all_documents
from application.tools.logger import logger

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
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Score: {result['similarity_score']:.4f}):")
            print("-" * 40)
            print(result['content'])
            print("-" * 40)
        
        return True
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return False