"""
高级图片压缩引擎
使用 imagequant (libimagequant) 和 mozjpeg 实现高质量压缩
"""
import io
import os
from typing import Tuple, Optional
from PIL import Image, ImageFile
from pathlib import Path

# 可选依赖
try:
    import pillow_avif
except ImportError:
    pass  # AVIF 支持可选

try:
    import imagequant
    HAS_IMAGEQUANT = True
except ImportError:
    HAS_IMAGEQUANT = False
    print("[警告] imagequant 未安装，PNG 将使用 Pillow 默认压缩")

try:
    import mozjpeg_lossless_optimization
    HAS_MOZJPEG = True
except ImportError:
    HAS_MOZJPEG = False
    print("[警告] mozjpeg-lossless-optimization 未安装，JPEG 将使用 Pillow 默认压缩")

# oxipng 需要 Rust 编译环境，暂时禁用
HAS_OXIPNG = False

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
        """PNG 压缩 - imagequant 量化 + oxipng 无损优化"""

        if not use_pngquant:
            img.save(output_path, 'PNG', optimize=True, compress_level=9)
            self._oxipng_optimize_file(output_path)
            return

        max_colors = 256

        if HAS_IMAGEQUANT:
            try:
                if img.mode not in ('RGBA', 'RGB'):
                    img = img.convert('RGBA' if 'A' in img.mode or img.mode == 'P' else 'RGB')

                # 不设置 min_quality/max_quality，最大压缩
                result = imagequant.quantize_pil_image(
                    img,
                    dithering_level=1.0,
                    max_colors=max_colors
                )

                result.save(output_path, 'PNG', optimize=True, compress_level=9)
                self._oxipng_optimize_file(output_path)
                print(f"[PNG压缩] imagequant 压缩完成")
                return
            except Exception as e:
                print(f"[PNG压缩] imagequant 失败: {e}")

        # Pillow 备用
        self._compress_png_pillow(img, output_path, max_colors)

    def _oxipng_optimize_file(self, filepath: str):
        """使用 oxipng 无损优化 PNG 文件（快速）"""
        if not HAS_OXIPNG:
            return

        try:
            # level 2 是默认值，平衡速度和压缩率
            oxipng.optimize(filepath, level=2)
        except Exception as e:
            print(f"[oxipng] 优化失败: {e}")

    def _compress_png_pillow(self, img: Image.Image, output_path: str, max_colors: int):
        """Pillow PNG 压缩备用方案"""
        try:
            has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

            if has_alpha:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img_q = img.quantize(colors=max_colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
                img_q.convert('RGBA').save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_q = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=max_colors)
                img_q.save(output_path, 'PNG', optimize=True, compress_level=9)
        except Exception:
            img.save(output_path, 'PNG', optimize=True, compress_level=9)

    def _compress_jpeg(self, img: Image.Image, output_path: str, quality: int):
        """JPEG 压缩 - 使用 MozJPEG 优化"""
        # 先用 Pillow 保存
        buffer = io.BytesIO()
        img.save(
            buffer,
            'JPEG',
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling='4:2:0'
        )

        jpeg_bytes = buffer.getvalue()

        # 使用 MozJPEG 进一步优化
        if HAS_MOZJPEG:
            try:
                jpeg_bytes = mozjpeg_lossless_optimization.optimize(jpeg_bytes)
                print(f"[JPEG压缩] MozJPEG 优化完成")
            except Exception as e:
                print(f"[JPEG压缩] MozJPEG 优化失败: {e}")

        # 写入文件
        with open(output_path, 'wb') as f:
            f.write(jpeg_bytes)

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
                self._compress_jpeg_memory(img, output_buffer, quality)
            elif target_format == 'WEBP':
                img.save(output_buffer, 'WEBP', quality=quality, method=6)
            else:
                img.save(output_buffer, target_format, optimize=True)

        compressed_size = len(output_buffer.getvalue())
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

        return compressed_size, ratio

    def _compress_png_memory(self, img: Image.Image, output_buffer: io.BytesIO, quality: int):
        """PNG 内存压缩 - imagequant (无质量限制，最大压缩)"""
        max_colors = 256
        temp_buffer = io.BytesIO()

        if HAS_IMAGEQUANT:
            try:
                if img.mode not in ('RGBA', 'RGB'):
                    img = img.convert('RGBA' if 'A' in img.mode or img.mode == 'P' else 'RGB')

                # 不设置 min_quality/max_quality，让 imagequant 自由压缩
                # 这与 wasm-image-compressor 的行为一致
                result = imagequant.quantize_pil_image(
                    img,
                    dithering_level=1.0,
                    max_colors=max_colors
                )
                result.save(temp_buffer, 'PNG', optimize=True, compress_level=9)

                optimized = self._oxipng_optimize_bytes(temp_buffer.getvalue())
                output_buffer.write(optimized)
                return
            except Exception:
                pass

        # Pillow 备用
        self._compress_png_pillow_memory(img, output_buffer, max_colors)

    def _oxipng_optimize_bytes(self, data: bytes) -> bytes:
        """使用 oxipng 无损优化 PNG 字节数据（快速）"""
        if not HAS_OXIPNG:
            return data

        try:
            optimized = oxipng.optimize_from_memory(data, level=2)
            return optimized if len(optimized) < len(data) else data
        except Exception:
            return data

    def _compress_png_pillow_memory(self, img: Image.Image, output_buffer: io.BytesIO, max_colors: int):
        """Pillow PNG 内存压缩备用"""
        try:
            has_alpha = img.mode in ('RGBA', 'LA')
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

    def _compress_jpeg_memory(self, img: Image.Image, output_buffer: io.BytesIO, quality: int):
        """JPEG 内存压缩 - 使用 MozJPEG 优化"""
        temp_buffer = io.BytesIO()
        img.save(temp_buffer, 'JPEG', quality=quality, optimize=True, progressive=True, subsampling='4:2:0')

        jpeg_bytes = temp_buffer.getvalue()

        if HAS_MOZJPEG:
            try:
                jpeg_bytes = mozjpeg_lossless_optimization.optimize(jpeg_bytes)
            except Exception:
                pass

        output_buffer.write(jpeg_bytes)

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
