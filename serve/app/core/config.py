"""
应用配置
"""
from typing import List


class Settings:
    MAX_FILE_SIZE: int = 10 * 1024 * 1024 
    MAX_FILES_PER_BATCH: int = 20
    ALLOWED_EXTENSIONS: List[str] = ['.jpg', '.jpeg', '.png', '.webp']


settings = Settings()
