"""
高级图片压缩引擎
使用纯 Python 实现，无需外部程序，方便打包
"""
import io
import os
from typing import Tuple, Optional
from PIL import Image, ImageFile, ImageOps
from pathlib import Path

try:
    import pillow_avif
except ImportError:
    pass  # AVIF 支持可选

# 允许加载截断的图片
ImageFile.LOAD_TRUNCATED_IMAGES = True


class AdvancedCompressor:
    """
    高级图片压缩器
    支持 PNG、JPEG、WebP、AVIF 等格式
    使用多种算法组合以达到最佳压缩效果
    """

    def __init__(self):
        self.supported_formats = {'PNG', 'JPEG', 'JPG', 'WEBP', 'AVIF'}

    def compress_image(
        self,
        input_path: str,
        output_path: str,
        quality: int = 85,
        output_format: Optional[str] = None,
        use_pngquant: bool = True
    ) -> Tuple[int, int, float]:
        """
        压缩图片

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            quality: 压缩质量 (1-100)
            output_format: 输出格式 (None=保持原格式)
            use_pngquant: PNG 是否使用 pngquant 有损压缩

        Returns:
            (原始大小, 压缩后大小, 压缩率)
        """
        original_size = os.path.getsize(input_path)

        with Image.open(input_path) as img:
            # 获取原始格式
            original_format = img.format
            target_format = output_format or original_format

            # 转换 RGBA 到 RGB（如果目标格式不支持透明度）
            if target_format in ['JPEG', 'JPG'] and img.mode in ['RGBA', 'LA', 'P']:
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ['RGBA', 'LA'] else None)
                img = background
            elif img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGBA' if target_format in ['PNG', 'WEBP', 'AVIF'] else 'RGB')

            # 根据格式选择压缩策略
            if target_format == 'PNG':
                self._compress_png(img, output_path, quality, use_pngquant)
            elif target_format in ['JPEG', 'JPG']:
                self._compress_jpeg(img, output_path, quality)
            elif target_format == 'WEBP':
                self._compress_webp(img, output_path, quality)
            elif target_format == 'AVIF':
                self._compress_avif(img, output_path, quality)
            else:
                raise ValueError(f"Unsupported format: {target_format}")

        compressed_size = os.path.getsize(output_path)
        compression_ratio = (1 - compressed_size / original_size) * 100

        return original_size, compressed_size, compression_ratio

    def _compress_png(self, img: Image.Image, output_path: str, quality: int, use_pngquant: bool):
        """PNG 压缩 - 纯 Python 实现，平衡质量和压缩率"""

        if use_pngquant:
            try:
                # 根据质量参数决定颜色数量（平衡质量和大小）
                # TinyPNG 使用约 256 色
                if quality >= 90:
                    max_colors = 256
                elif quality >= 85:
                    max_colors = 256  # 默认 85 质量也用 256 色，保证质量
                elif quality >= 75:
                    max_colors = 200
                else:
                    max_colors = 128

                print(f"[PNG压缩] 原始模式: {img.mode}, 大小: {img.size}")

                # 检查透明通道
                has_alpha = img.mode in ('RGBA', 'LA') or (
                    img.mode == 'P' and 'transparency' in img.info
                )

                if has_alpha:
                    # 有透明通道：使用 FASTOCTREE 方法量化
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                    # RGBA 必须使用 FASTOCTREE 或 MAXCOVERAGE 方法
                    img_quantized = img.quantize(
                        colors=max_colors,
                        method=Image.Quantize.FASTOCTREE,  # RGBA 必须用这个方法
                        dither=Image.Dither.FLOYDSTEINBERG
                    )

                    # 转回 RGBA 保持质量
                    img_rgba = img_quantized.convert('RGBA')

                    # 保存为优化的 PNG
                    img_rgba.save(
                        output_path,
                        'PNG',
                        optimize=True,
                        compress_level=9
                    )
                    print(f"[PNG压缩] 有透明通道，FASTOCTREE 量化为 {max_colors} 色，RGBA 模式")

                else:
                    # 无透明通道：使用调色板压缩
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 使用自适应调色板（质量更好）
                    img_quantized = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=max_colors)

                    # 保存为 PNG8
                    img_quantized.save(
                        output_path,
                        'PNG',
                        optimize=True,
                        compress_level=9
                    )
                    print(f"[PNG压缩] 无透明通道，自适应调色板 {max_colors} 色，P 模式")

            except Exception as e:
                print(f"[PNG压缩] 量化失败: {e}，使用备用方案")
                # 备用方案：尝试调色板转换
                try:
                    if img.mode == 'RGB':
                        img_p = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
                        img_p.save(output_path, 'PNG', optimize=True, compress_level=9)
                    elif img.mode == 'RGBA':
                        # RGBA 先量化再保存
                        img_p = img.quantize(colors=256)
                        img_p.save(output_path, 'PNG', optimize=True, compress_level=9)
                    else:
                        img.save(output_path, 'PNG', optimize=True, compress_level=9)
                except Exception as e2:
                    print(f"[PNG压缩] 备用方案也失败: {e2}，使用基础保存")
                    img.save(output_path, 'PNG', optimize=True, compress_level=9)
        else:
            # 无损压缩
            img.save(
                output_path,
                'PNG',
                optimize=True,
                compress_level=9
            )

    def _compress_jpeg(self, img: Image.Image, output_path: str, quality: int):
        """JPEG 压缩 - 使用优化的渐进式 JPEG"""
        img.save(
            output_path,
            'JPEG',
            quality=quality,
            optimize=True,
            progressive=True,  # 渐进式 JPEG
            subsampling='4:2:0'  # 色度子采样
        )

    def _compress_webp(self, img: Image.Image, output_path: str, quality: int):
        """WebP 压缩 - 使用 Google WebP 编码器"""
        img.save(
            output_path,
            'WEBP',
            quality=quality,
            method=6,  # 最慢但压缩最好
            lossless=False
        )

    def _compress_avif(self, img: Image.Image, output_path: str, quality: int):
        """AVIF 压缩 - 下一代图片格式，压缩率最高"""
        img.save(
            output_path,
            'AVIF',
            quality=quality,
            speed=0  # 最慢但压缩最好
        )


    def get_optimal_format(self, input_path: str) -> str:
        """
        分析图片并返回最佳输出格式

        Args:
            input_path: 输入文件路径

        Returns:
            最佳格式 (AVIF/WebP/JPEG/PNG)
        """
        with Image.open(input_path) as img:
            # 检查是否有透明通道
            has_alpha = img.mode in ['RGBA', 'LA', 'P'] and (
                img.mode != 'P' or 'transparency' in img.info
            )

            # 如果有透明通道，优先使用支持透明的格式
            if has_alpha:
                return 'AVIF'  # AVIF 支持透明且压缩率最高

            # 分析图片复杂度
            # 简单图片（如图标、logo）用 PNG
            # 复杂图片（如照片）用 AVIF/JPEG
            if self._is_simple_image(img):
                return 'PNG'
            else:
                return 'AVIF'  # AVIF 对照片压缩效果最好

    def _is_simple_image(self, img: Image.Image) -> bool:
        """判断是否为简单图片（图标、logo等）"""
        # 简单启发式：如果颜色数量少，认为是简单图片
        if img.mode == 'P':
            return True

        # 采样部分像素来估计颜色数量
        width, height = img.size
        if width * height < 100000:  # 小图片直接分析
            colors = len(set(list(img.getdata())))
            return colors < 256
        else:
            # 大图片采样
            img_small = img.resize((100, 100), Image.Resampling.LANCZOS)
            colors = len(set(list(img_small.getdata())))
            return colors < 100

    def compress_in_memory(
        self,
        input_buffer: io.BytesIO,
        output_buffer: io.BytesIO,
        target_format: str,
        quality: int = 85
    ) -> Tuple[int, float]:
        """
        内存中压缩图片

        Returns:
            (压缩后大小, 压缩率)
        """
        input_buffer.seek(0)
        original_size = len(input_buffer.getvalue())

        with Image.open(input_buffer) as img:
            target_format = target_format.upper()
            if target_format == 'JPG':
                target_format = 'JPEG'

            # 转换模式
            if target_format == 'JPEG' and img.mode in ['RGBA', 'LA', 'P']:
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ['RGBA', 'LA']:
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGBA' if target_format in ['PNG', 'WEBP'] else 'RGB')

            # 压缩
            if target_format == 'PNG':
                self._compress_png_memory(img, output_buffer, quality)
            elif target_format == 'JPEG':
                img.save(output_buffer, 'JPEG', quality=quality, optimize=True, progressive=True)
            elif target_format == 'WEBP':
                img.save(output_buffer, 'WEBP', quality=quality, method=6)
            else:
                img.save(output_buffer, target_format, optimize=True)

        compressed_size = len(output_buffer.getvalue())
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

        return compressed_size, ratio

    def _compress_png_memory(self, img: Image.Image, output_buffer: io.BytesIO, quality: int):
        """PNG 内存压缩"""
        max_colors = 256
        has_alpha = img.mode in ('RGBA', 'LA')

        try:
            if has_alpha:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img_q = img.quantize(colors=max_colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
                img_q.convert('RGBA').save(output_buffer, 'PNG', optimize=True, compress_level=9)
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_q = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=max_colors)
                img_q.save(output_buffer, 'PNG', optimize=True, compress_level=9)
        except:
            img.save(output_buffer, 'PNG', optimize=True, compress_level=9)

    def batch_compress(
        self,
        input_files: list,
        output_dir: str,
        quality: int = 85,
        output_format: Optional[str] = None
    ) -> list:
        """
        批量压缩图片

        Args:
            input_files: 输入文件列表
            output_dir: 输出目录
            quality: 压缩质量
            output_format: 输出格式

        Returns:
            压缩结果列表
        """
        results = []
        os.makedirs(output_dir, exist_ok=True)

        for input_file in input_files:
            try:
                filename = Path(input_file).stem
                ext = output_format.lower() if output_format else Path(input_file).suffix[1:]
                output_file = os.path.join(output_dir, f"{filename}.{ext}")

                original_size, compressed_size, ratio = self.compress_image(
                    input_file,
                    output_file,
                    quality,
                    output_format
                )

                results.append({
                    'filename': Path(input_file).name,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': ratio,
                    'output_path': output_file,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'filename': Path(input_file).name,
                    'error': str(e),
                    'success': False
                })

        return results
