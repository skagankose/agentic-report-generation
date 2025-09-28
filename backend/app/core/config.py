"""
Application configuration settings
"""
import os
from typing import Optional


class Settings:
    """Application settings and configuration"""
    
    # Flask settings
    SECRET_KEY: str = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
    DEBUG: bool = os.environ.get('FLASK_ENV') == 'development'
    HOST: str = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT: int = int(os.environ.get('FLASK_PORT', 5000))
    
    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = os.environ.get('ANTHROPIC_API_KEY')
    OPENAI_API_KEY: Optional[str] = os.environ.get('OPENAI_API_KEY')
    TAVILY_API_KEY: Optional[str] = os.environ.get('TAVILY_API_KEY')
    
    # Application settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER: str = 'tmp'
    
    @property
    def has_llm_key(self) -> bool:
        """Check if at least one LLM API key is configured"""
        return bool(self.ANTHROPIC_API_KEY or self.OPENAI_API_KEY)
    
    @property
    def has_search_key(self) -> bool:
        """Check if search API key is configured"""
        return bool(self.TAVILY_API_KEY)


settings = Settings()
