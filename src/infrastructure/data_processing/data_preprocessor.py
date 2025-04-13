"""Module for processing log data into documents for vector embedding."""
import pandas as pd
from typing import List, Optional
import src.application.tools.logger as logger
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter



def load_and_process_logs(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    """
    Load log data from CSV and process into documents for embedding.
    
    Args:
        file_path: Path to the log file
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of Document objects ready for embedding
    """
    try:
        logger.info(f"Loading log data from {file_path}")
        df = pd.read_csv(file_path, header=0)
        logger.info(f"Loaded {len(df)} log entries")
        
        # Process each log entry into a document
        documents = []
        for index, row in df.iterrows():
            try:
                content = (
                    f"Time: {row['time']}\n"
                    f"Event: {row['name']}\n"
                    f"IP: {row['ip']}\n"
                    f"Host: {row['host']}\n"
                    f"Short Code: {row['short']}\n"
                    f"Time Label: {row['time_label']}\n"
                    f"Event Label: {row['event_label']}"
                )
                
                # Store original data in metadata for easy retrieval
                metadata = {
                    "source": file_path,
                    "index": index,
                    "time": row['time'],
                    "ip": row['ip'],
                    "host": row['host'],
                    "event_label": row['event_label']
                }
                
                documents.append(Document(page_content=content, metadata=metadata))
            except KeyError as e:
                logger.warning(f"Missing field in log entry {index}: {e}")
                continue
                
        logger.info(f"Created {len(documents)} documents from log entries")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        docs = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(docs)} chunks")
        
        return docs
    except Exception as e:
        logger.error(f"Error processing log file {file_path}: {e}")
        raise
