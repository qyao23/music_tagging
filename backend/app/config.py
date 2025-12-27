from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./music_tagging.db"
    
    # JWT 配置（简化版，使用固定密钥）
    SECRET_KEY: str = "music-tagging-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"

settings = Settings()
