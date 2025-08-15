"""
MoodFlix Backend Configuration
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    TMDB_API_KEY = os.getenv('TMDB_API_KEY')
    
    # External API URLs
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    TMDB_BASE_URL = os.getenv('TMDB_BASE_URL', 'https://api.themoviedb.org/3')
    TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p'
    
    # Redis settings
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '3'))
    RATE_LIMIT_PER_DAY = int(os.getenv('RATE_LIMIT_PER_DAY', '100'))
    
    # OpenAI limits
    OPENAI_MONTHLY_LIMIT = float(os.getenv('OPENAI_MONTHLY_LIMIT', '7.0'))
    
    # Emergency controls
    EMERGENCY_STOP = os.getenv('EMERGENCY_STOP', 'false').lower() == 'true'
    
    # Cache settings
    CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '24'))
    CACHE_TTL_SECONDS = CACHE_TTL_HOURS * 3600
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
    
    # Analytics
    ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'false').lower() == 'true'
    
    # Sentry (optional)
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    
    @classmethod
    def validate_required_env_vars(cls) -> list[str]:
        """Validate that required environment variables are set"""
        missing_vars = []
        
        if not cls.OPENAI_API_KEY:
            missing_vars.append('OPENAI_API_KEY')
        
        if not cls.TMDB_API_KEY:
            missing_vars.append('TMDB_API_KEY')
        
        return missing_vars
    
    @classmethod
    def get_tmdb_image_url(cls, path: Optional[str], size: str = 'w500') -> Optional[str]:
        """Generate TMDb image URL"""
        if not path:
            return None
        return f"{cls.TMDB_IMAGE_BASE_URL}/{size}{path}"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    RATE_LIMIT_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    RATE_LIMIT_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    RATE_LIMIT_ENABLED = False
    REDIS_URL = 'redis://localhost:6379/1'  # Use different DB for tests

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, config_map['default'])

