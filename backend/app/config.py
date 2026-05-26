from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # LLM
    openai_api_key: str = Field(default='', alias='OPENAI_API_KEY')
    llm_provider: str = Field(default='openai', alias='LLM_PROVIDER')
    llm_model: str = Field(default='gpt-3.5-turbo', alias='LLM_MODEL')
    llm_temperature: float = Field(default=0.0, alias='LLM_TEMPERATURE')
    llm_max_tokens: int = Field(default=1024, alias='LLM_MAX_TOKENS')

    # Embeddings
    embedding_model: str = Field(
        default='text-embedding-3-small', alias='EMBEDDING_MODEL'
    )
    embedding_dimension: int = Field(default=1536, alias='EMBEDDING_DIMENSION')

    # Qdrant
    qdrant_host: str = Field(default='localhost', alias='QDRANT_HOST')
    qdrant_port: int = Field(default=6333, alias='QDRANT_PORT')
    qdrant_collection: str = Field(
        default='rag_documents', alias='QDRANT_COLLECTION'
    )

    # Chunking
    chunk_size: int = Field(default=512, alias='CHUNK_SIZE')
    chunk_overlap: int = Field(default=64, alias='CHUNK_OVERLAP')
    chunking_strategy: str = Field(
        default='sliding_window', alias='CHUNKING_STRATEGY'
    )

    # Retrieval
    retrieval_top_k: int = Field(default=10, alias='RETRIEVAL_TOP_K')
    reranker_top_k: int = Field(default=3, alias='RERANKER_TOP_K')
    use_reranker: bool = Field(default=True, alias='USE_RERANKER')

    # API
    api_host: str = Field(default='0.0.0.0', alias='API_HOST')
    api_port: int = Field(default=8000, alias='API_PORT')
    debug: bool = Field(default=True, alias='DEBUG')

    # Paths
    @property
    def uploads_dir(self) -> Path:
        path = BASE_DIR / 'data' / 'uploads'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def processed_dir(self) -> Path:
        path = BASE_DIR / 'data' / 'processed'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def qdrant_url(self) -> str:
        return f'http://{self.qdrant_host}:{self.qdrant_port}'


@lru_cache
def get_settings() -> Settings:
    return Settings()
