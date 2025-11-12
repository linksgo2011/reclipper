import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    # 兼容旧版本pydantic
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用程序配置"""
    
    # OpenAI API配置
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_base_url: str = Field("https://api.openai.com/v1", env="OPENAI_BASE_URL")
    translation_model: str = Field("gpt-3.5-turbo", env="TRANSLATION_MODEL")
    
    # 下载配置
    download_dir: str = Field("./downloads", env="DOWNLOAD_DIR")
    max_video_size: str = Field("500MB", env="MAX_VIDEO_SIZE")
    
    # 翻译配置
    target_language: str = Field("zh-CN", env="TARGET_LANGUAGE")
    
    # 其他配置
    ffmpeg_path: Optional[str] = Field(None, env="FFMPEG_PATH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()