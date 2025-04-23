from src.application.tools.logger import logger

from typing import Optional
from src.infrastructure.data_processing.data_preprocessor import load_and_process_logs
from src.infrastructure.database.store_to_chroma import store_to_chroma
from src.infrastructure.embeddings.embedder import get_azure_embedding

def index_logs(config, log_file: Optional[str] = None, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
    """Index log files."""
    try:
        log_file_path = log_file or config.log_file_path
        c_size = chunk_size or config.chunk_size
        c_overlap = chunk_overlap or config.chunk_overlap
        
        logger.info(f"Indexing log file: {log_file_path}")
        
        # Process logs into documents
        docs = load_and_process_logs(log_file_path, c_size, c_overlap)
        logger.info(f"Processed {len(docs)} chunks")
        
        # Get embeddings
        embedding = get_azure_embedding()
        
        # Store in vector database
        db = store_to_chroma(docs, embedding, config.persist_directory)
        logger.info(f"Successfully indexed logs to {config.persist_directory}")
        
        return True
    except Exception as e:
        logger.error(f"Error indexing logs: {e}")
        return False