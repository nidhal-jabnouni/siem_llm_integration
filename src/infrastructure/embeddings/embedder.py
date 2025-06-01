from langchain_openai import AzureOpenAIEmbeddings
from src.application.tools.logger import logger
from chromadb.api.types import EmbeddingFunction
import os

def get_azure_embedding() -> AzureOpenAIEmbeddings:
    """
    Initializes Azure OpenAI embeddings with environment variable configs.
    """
    try:
        logger.info("Initializing Azure OpenAI embeddings...")

        # Optional safety: remove conflicting var if exists
        if "OPENAI_API_BASE" in os.environ:
            del os.environ["OPENAI_API_BASE"]

        return AzureOpenAIEmbeddings(
            deployment=os.environ["AZURE_EMBEDDING_DEPLOYMENT_NAME"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
             # You can tune this value if needed
        )
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI embeddings: {e}")
        raise


class AzureEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.embedder = get_azure_embedding()

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(input)