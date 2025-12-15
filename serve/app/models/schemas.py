"""
数据模型
"""
from pydantic import BaseModel
from typing import Optional, List


class CompressResult(BaseModel):
    """压缩结果"""
    filename: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    data: str 
    success: bool
    error: Optional[str] = None
    format: str


class BatchCompressResult(BaseModel):
    """批量压缩结果"""
    total: int
    success: int
    failed: int
    results: List[CompressResult]
    total_original_size: int
    total_compressed_size: int
    total_compression_ratio: float
