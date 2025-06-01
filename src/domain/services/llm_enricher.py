from typing import Dict, List
from src.infrastructure.config.settings import Config
from src.application.tools.logger import logger
from langchain.vectorstores import Chroma
import time
from langchain.schema import Document
from openai import AzureOpenAI

class LogEnricher:
    """Class for enriching log data with LLM insights."""
    
    def __init__(self, config: Config):
        """
        Initialize the log enricher.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.client = AzureOpenAI(
            api_key=config.azure_openai_api_key,
            api_version=config.azure_openai_api_version,
            azure_endpoint=config.azure_openai_endpoint
        )
        logger.info("Initialized LogEnricher with Azure OpenAI")
        
    def enrich_log_entry(self, log_entry: str) -> Dict[str, str]:
        """
        Enrich a log entry with LLM insights.
        
        Args:
            log_entry: Log entry text
            
        Returns:
            Dictionary containing the enriched data
        """
        try:
            # Prepare the prompt for the LLM
            prompt = f"""
            Analyze the following security log entry and provide:
            1. A threat assessment (Low, Medium, High)
            2. Potential attack type or security issue
            3. possibility of intervention or mitigation
            
            
            Log entry:
            {log_entry}
            
            Format your response as JSON with the following fields:
            "threat_level", "attack_type", "recommendations", "context"
            """
            
            # Call the Azure OpenAI GPT-4o API
            response = self.client.chat.completions.create(
                model=self.config.azure_deployment_name,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing security logs."},
                    {"role": "user", "content": prompt}
                ],
               response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "security_analysis",
            "schema": {
                "type": "object",
                "properties": {
                    "attack_type": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "intervention_required": {"type": "boolean"}
                },
                "required": ["attack_type", "severity", "intervention_required"],
                "additionalProperties": False
            }
        }
    },
                temperature=0.3
            )
            
            # Extract and parse the content
            enriched_data = response.choices[0].message.content
            logger.info("Successfully enriched log entry with LLM")
            
            return {
                "llm_enrichment": enriched_data
            }
            
        except Exception as e:
            logger.error(f"Error enriching log entry with LLM: {e}")
            return {
                "llm_enrichment": f"Error enriching: {str(e)}"
            }
    
    def batch_enrich_documents(self, documents: List[Document], batch_size: int = 5, delay: float = 1.0) -> List[Document]:
        """
        Enrich a batch of documents with LLM insights.
        
        Args:
            documents: List of documents to enrich
            batch_size: Number of documents to process in each batch
            delay: Delay between batches to avoid rate limiting
            
        Returns:
            List of enriched documents
        """
        enriched_documents = []
        total_docs = len(documents)
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
            
            for doc in batch:
                try:
                    # Skip if already enriched
                    if "llm_enrichment" in doc.metadata and doc.metadata["llm_enrichment"]:
                        enriched_documents.append(doc)
                        continue
                        
                    # Enrich the document
                    enrichment = self.enrich_log_entry(doc.page_content)
                    
                    # Create a new document with updated metadata
                    new_metadata = {**doc.metadata, **enrichment}
                    enriched_doc = Document(page_content=doc.page_content, metadata=new_metadata)
                    enriched_documents.append(enriched_doc)
                    
                except Exception as e:
                    logger.error(f"Error enriching document: {e}")
                    enriched_documents.append(doc)  # Keep the original document
            
            # Sleep to avoid rate limiting
            if i + batch_size < total_docs:
                logger.info(f"Sleeping for {delay} seconds to avoid rate limiting")
                time.sleep(delay)
        
        return enriched_documents