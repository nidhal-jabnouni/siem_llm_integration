import tools.logger as logger
from typing import Optional
from infrastructure.data_processing.data_preprocessor import load_and_process_logs, get_all_documents
from infrastructure.database.load_chroma import load_chroma
from infrastructure.database.update_documents import update_documents
from infrastructure.embeddings.embedder import get_azure_embedding
from domain.services.llm_enricher import LogEnricher


def enrich_logs(config, batch_size: Optional[int] = None, batch_delay: Optional[float] = None):
    """Enrich documents in the database with LLM insights."""
    try:
        # Override with command line arguments if provided
        if batch_size:
            config.batch_size = batch_size
        if batch_delay:
            config.batch_delay = batch_delay
            
        logger.info(f"Enriching documents with batch size {config.batch_size} and delay {config.batch_delay}")
        
        # Get embeddings
        embedding = get_azure_embedding()
        
        # Load vector database
        db = load_chroma(embedding, config.persist_directory)
        
        # Get all documents
        documents = get_all_documents(db)
        
        if not documents:
            logger.warning("No documents found in the database")
            print("❌ No documents found to enrich")
            return False
            
        logger.info(f"Retrieved {len(documents)} documents")
        
        # Initialize the LLM enricher
        enricher = LogEnricher(config)
        
        # Enrich documents
        enriched_documents = enricher.batch_enrich_documents(
            documents, 
            batch_size=config.batch_size, 
            delay=config.batch_delay
        )
        
        # Update the vector database
        success = update_documents(db, enriched_documents)
        
        if success:
            logger.info("Successfully enriched and updated all documents")
            print("✅ All documents have been enriched with LLM insights and updated in the database")
        else:
            logger.error("Failed to update the vector database")
            print("❌ Failed to update the vector database")
            
        return success
    except Exception as e:
        logger.error(f"Error enriching documents: {e}")
        print(f"❌ Error: {e}")
        return False