"""
图片压缩 API - 内存处理，不保存文件
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from typing import List
from pathlib import Path
import io
import base64

from app.core.compressor import AdvancedCompressor
from app.core.config import settings
from app.models.schemas import CompressResult, BatchCompressResult

router = APIRouter()
compressor = AdvancedCompressor()


@router.post("/compress", response_model=CompressResult)
async def compress_single_image(file: UploadFile = File(...)):
    """压缩单个图片"""
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            return CompressResult(
                filename=file.filename,
                original_size=0,
                compressed_size=0,
                compression_ratio=0,
                data="",
                success=False,
                error=f"不支持的格式: {file_ext}",
                format=""
            )

        content = await file.read()
        original_size = len(content)

        if original_size > settings.MAX_FILE_SIZE:
            return CompressResult(
                filename=file.filename,
                original_size=original_size,
                compressed_size=0,
                compression_ratio=0,
                data="",
                success=False,
                error="文件过大",
                format=""
            )

        input_buffer = io.BytesIO(content)
        output_buffer = io.BytesIO()

        target_format = file_ext[1:]
        compressed_size, ratio = compressor.compress_in_memory(
            input_buffer,
            output_buffer,
            target_format
        )

        output_buffer.seek(0)
        base64_data = base64.b64encode(output_buffer.read()).decode('utf-8')

        mime_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp'
        }
        mime_type = mime_map.get(target_format, 'image/png')
        data_url = f"data:{mime_type};base64,{base64_data}"

        return CompressResult(
            filename=file.filename,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=ratio,
            data=data_url,
            success=True,
            format=target_format
        )

    except Exception as e:
        return CompressResult(
            filename=file.filename,
            original_size=0,
            compressed_size=0,
            compression_ratio=0,
            data="",
            success=False,
            error=str(e),
            format=""
        )


@router.post("/compress/batch", response_model=BatchCompressResult)
async def compress_batch_images(files: List[UploadFile] = File(...)):
    """批量压缩图片，返回 base64 数据"""
    if len(files) > settings.MAX_FILES_PER_BATCH:
        raise HTTPException(400, f"最多支持 {settings.MAX_FILES_PER_BATCH} 个文件")

    results = []
    total_original_size = 0
    total_compressed_size = 0
    success_count = 0
    failed_count = 0

    for file in files:
        try:
            # 验证文件类型
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                results.append(CompressResult(
                    filename=file.filename,
                    original_size=0,
                    compressed_size=0,
                    compression_ratio=0,
                    data="",
                    success=False,
                    error=f"不支持的格式: {file_ext}",
                    format=""
                ))
                failed_count += 1
                continue

            # 读取文件到内存
            content = await file.read()
            original_size = len(content)

            # 检查文件大小
            if original_size > settings.MAX_FILE_SIZE:
                results.append(CompressResult(
                    filename=file.filename,
                    original_size=original_size,
                    compressed_size=0,
                    compression_ratio=0,
                    data="",
                    success=False,
                    error="文件过大",
                    format=""
                ))
                failed_count += 1
                continue

            # 内存中压缩
            input_buffer = io.BytesIO(content)
            output_buffer = io.BytesIO()

            target_format = file_ext[1:]  # 去掉点号
            compressed_size, ratio = compressor.compress_in_memory(
                input_buffer,
                output_buffer,
                target_format
            )

            # 转为 base64
            output_buffer.seek(0)
            base64_data = base64.b64encode(output_buffer.read()).decode('utf-8')

            # 确定 MIME 类型
            mime_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'webp': 'image/webp'
            }
            mime_type = mime_map.get(target_format, 'image/png')
            data_url = f"data:{mime_type};base64,{base64_data}"

            results.append(CompressResult(
                filename=file.filename,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=ratio,
                data=data_url,
                success=True,
                format=target_format
            ))

            total_original_size += original_size
            total_compressed_size += compressed_size
            success_count += 1

        except Exception as e:
            results.append(CompressResult(
                filename=file.filename,
                original_size=0,
                compressed_size=0,
                compression_ratio=0,
                data="",
                success=False,
                error=str(e),
                format=""
            ))
            failed_count += 1

    # 计算总压缩率
    total_ratio = 0
    if total_original_size > 0:
        total_ratio = (1 - total_compressed_size / total_original_size) * 100

    return BatchCompressResult(
        total=len(files),
        success=success_count,
        failed=failed_count,
        results=results,
        total_original_size=total_original_size,
        total_compressed_size=total_compressed_size,
        total_compression_ratio=total_ratio
    )
