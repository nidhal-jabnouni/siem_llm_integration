import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass
class Config:
    """Configuration for the log analysis system."""
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str
    azure_embedding_deployment_name: str
    azure_deployment_name: str
    batch_size: int = 5
    batch_delay: float = 1.0
    log_file_path: str = "logs/fox_alerts.txt"
    persist_directory: str = "chroma_logs_db"
    chunk_size: int = 1000
    chunk_overlap: int = 100

def load_config() -> Config:
    """Load configuration from environment variables."""
    load_dotenv()
    
    # Required environment variables
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_EMBEDDING_DEPLOYMENT_NAME",
        "AZURE_DEPLOYMENT_NAME"
    ]
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return Config(
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_embedding_deployment_name=os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME"),
        azure_deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
        log_file_path=os.getenv("LOG_FILE_PATH", "logs/fox_alerts.txt"),
        persist_directory=os.getenv("PERSIST_DIRECTORY", "chroma_logs_db"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
        batch_size=int(os.getenv("BATCH_SIZE", "5")),
        batch_delay=float(os.getenv("BATCH_DELAY", "1.0"))
    )