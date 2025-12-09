"""
高级图片压缩引擎
使用 imagequant + zlib 实现高质量 PNG 压缩 (与 wasm-image-compressor 相同算法)
"""
import io
import os
import subprocess
import tempfile
import zlib
import struct
from typing import Tuple, Optional
from PIL import Image, ImageFile
from pathlib import Path

# 可选依赖
try:
    import pillow_avif
except ImportError:
    pass  # AVIF 支持可选

try:
    import mozjpeg_lossless_optimization
    HAS_MOZJPEG = True
except ImportError:
    HAS_MOZJPEG = False
    print("[警告] mozjpeg-lossless-optimization 未安装，JPEG 将使用 Pillow 默认压缩")

# imagequant - 与 libimagequant/pngquant 相同的量化算法
try:
    import imagequant
    HAS_IMAGEQUANT = True
    print("[imagequant] 已启用")
except ImportError:
    HAS_IMAGEQUANT = False
    print("[警告] imagequant 未安装，将使用备用方案")

# zopfli - 更好的 deflate 压缩
try:
    from zopfli.zopfli import compress as zopfli_compress
    HAS_ZOPFLI = True
    print("[zopfli] 已启用")
except ImportError:
    HAS_ZOPFLI = False
    print("[警告] zopfli 未安装，将使用 zlib")

# pypng - 自定义 PNG 编码
try:
    import png
    HAS_PYPNG = True
    print("[pypng] 已启用")
except ImportError:
    HAS_PYPNG = False
    print("[警告] pypng 未安装，将使用 Pillow")

# pngquant CLI 检测
PNGQUANT_PATH = Path(__file__).parent.parent.parent / "bin" / "pngquant.exe"
HAS_PNGQUANT = False
if PNGQUANT_PATH.exists():
    try:
        result = subprocess.run([str(PNGQUANT_PATH), "--version"], capture_output=True, timeout=5)
        HAS_PNGQUANT = result.returncode == 0
        if HAS_PNGQUANT:
            print(f"[pngquant] 已启用: {PNGQUANT_PATH}")
    except Exception:
        pass

if not HAS_PNGQUANT:
    print("[警告] pngquant 未找到，PNG 将使用 Pillow 压缩")

# oxipng CLI 检测 (PNG 无损优化，重新压缩 zlib)
OXIPNG_PATH = Path(__file__).parent.parent.parent / "bin" / "oxipng.exe"
HAS_OXIPNG = False
if OXIPNG_PATH.exists():
    try:
        result = subprocess.run([str(OXIPNG_PATH), "--version"], capture_output=True, timeout=5)
        HAS_OXIPNG = result.returncode == 0
        if HAS_OXIPNG:
            print(f"[oxipng] 已启用: {OXIPNG_PATH}")
    except Exception:
        pass

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
        """PNG 压缩 - 使用 pngquant CLI (与 TinyPNG 相同效果)"""

        if not use_pngquant or not HAS_PNGQUANT:
            img.save(output_path, 'PNG', optimize=True, compress_level=9)
            return

        # 保存为临时 PNG
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            img.save(tmp_path, 'PNG')

        try:
            # 使用 pngquant 压缩 (与 wasm-image-compressor 相同设置)
            # 不设置 --quality: 无质量限制，最大压缩
            # --speed=1: 最慢但压缩效果最好
            # --strip: 移除元数据
            result = subprocess.run([
                str(PNGQUANT_PATH),
                '128',  # 128色 与 wasm-image-compressor 一致
                '--speed=1',  # 最佳压缩
                '--strip',
                '--force',
                '--output', output_path,
                tmp_path
            ], capture_output=True, timeout=60)

            if result.returncode == 0:
                print(f"[PNG压缩] pngquant 压缩完成")
            else:
                print(f"[PNG压缩] pngquant 失败 (code={result.returncode})，使用 Pillow")
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
        except Exception as e:
            print(f"[PNG压缩] pngquant 异常: {e}，使用 Pillow")
            img.save(output_path, 'PNG', optimize=True, compress_level=9)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _oxipng_optimize(self, filepath: str):
        """使用 oxipng 无损优化 PNG"""
        if not HAS_OXIPNG:
            return

        try:
            # -o 6: 最大压缩 (不用 zopfli)
            # --strip all: 移除所有元数据
            result = subprocess.run([
                str(OXIPNG_PATH),
                '-o', '6',
                '--strip', 'all',
                filepath
            ], capture_output=True, timeout=60)

            if result.returncode == 0:
                print(f"[PNG压缩] oxipng 优化完成")
        except Exception as e:
            print(f"[PNG压缩] oxipng 优化失败: {e}")

    def _compress_png_imagequant(self, img: Image.Image, output_buffer: io.BytesIO, max_colors: int = 256, fast_mode: bool = True):
        """
        使用 imagequant 实现高压缩率 PNG

        Args:
            img: PIL Image
            output_buffer: 输出缓冲区
            max_colors: 最大颜色数
            fast_mode: True=快速模式(zlib,~1秒), False=最佳压缩(zopfli,~5秒)
        """
        if not HAS_IMAGEQUANT:
            raise RuntimeError("imagequant not available")

        # 确保是 RGBA 模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        width, height = img.size
        rgba_data = img.tobytes()

        # 使用 imagequant 量化
        indexed_pixels, palette = imagequant.quantize_raw_rgba_bytes(
            rgba_data,
            width,
            height,
            dithering_level=0.3,  # 低抖动实现高压缩率
            max_colors=max_colors,
            min_quality=0,
            max_quality=100
        )

        # 快速模式跳过像素优化（影响很小）
        if not fast_mode:
            indexed_pixels = self._optimize_pixel_repetition(indexed_pixels, palette, width, height, threshold=5)

        # 构建 PNG 文件
        png_data = self._build_png(width, height, palette, indexed_pixels, fast_mode=fast_mode)
        output_buffer.write(png_data)

    def _optimize_pixel_repetition(self, indexed_pixels: bytes, palette: list, width: int, height: int, threshold: int = 5) -> bytes:
        """
        后处理优化：使用 NumPy 向量化加速
        如果当前像素与左边像素的颜色差异小于阈值，则改为左边像素的颜色
        """
        try:
            import numpy as np
            return self._optimize_pixel_repetition_numpy(indexed_pixels, palette, width, height, threshold)
        except ImportError:
            return self._optimize_pixel_repetition_pure(indexed_pixels, palette, width, height, threshold)

    def _optimize_pixel_repetition_numpy(self, indexed_pixels: bytes, palette: list, width: int, height: int, threshold: int) -> bytes:
        """NumPy 向量化版本 - 快速"""
        import numpy as np

        # 构建调色板 RGB 数组
        num_colors = len(palette) // 4
        pal_rgb = np.array(palette, dtype=np.int32).reshape(-1, 4)[:, :3]  # (num_colors, 3)

        # 像素数组
        pixels = np.frombuffer(indexed_pixels, dtype=np.uint8).copy()
        pixels_2d = pixels.reshape(height, width)

        # 逐行处理（向量化列方向）
        for y in range(height):
            row = pixels_2d[y]
            for x in range(1, width):
                if row[x] != row[x-1]:
                    # 计算颜色差异
                    c1 = pal_rgb[row[x]]
                    c2 = pal_rgb[row[x-1]]
                    diff = np.sum((c1 - c2) ** 2)
                    if diff < threshold:
                        row[x] = row[x-1]

        return pixels.tobytes()

    def _optimize_pixel_repetition_pure(self, indexed_pixels: bytes, palette: list, width: int, height: int, threshold: int) -> bytes:
        """纯 Python 版本 - 备用"""
        pixels = bytearray(indexed_pixels)
        num_colors = len(palette) // 4

        def color_diff(idx1, idx2):
            if idx1 >= num_colors or idx2 >= num_colors:
                return 999999
            r1, g1, b1 = palette[idx1*4], palette[idx1*4+1], palette[idx1*4+2]
            r2, g2, b2 = palette[idx2*4], palette[idx2*4+1], palette[idx2*4+2]
            return (r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2

        for y in range(height):
            for x in range(1, width):
                pos = y * width + x
                prev_pos = pos - 1
                if pixels[pos] != pixels[prev_pos]:
                    diff = color_diff(pixels[pos], pixels[prev_pos])
                    if diff < threshold:
                        pixels[pos] = pixels[prev_pos]

        return bytes(pixels)

    def _oxipng_optimize_bytes(self, png_data: bytes) -> bytes:
        """使用 oxipng 优化 PNG 字节"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(png_data)

        try:
            # -o 4: 平衡速度和压缩率
            result = subprocess.run([
                str(OXIPNG_PATH),
                '-o', '4',
                '--strip', 'all',
                tmp_path
            ], capture_output=True, timeout=30)

            if result.returncode == 0:
                with open(tmp_path, 'rb') as f:
                    return f.read()
        except Exception:
            pass
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return png_data

    def _build_png(self, width: int, height: int, palette: list, indexed_pixels: bytes, fast_mode: bool = False) -> bytes:
        """
        手动构建 PNG 文件

        Args:
            palette: 平铺的调色板 [r0, g0, b0, a0, r1, g1, b1, a1, ...]
            indexed_pixels: 索引像素数据
            fast_mode: True=使用zlib快速压缩, False=使用zopfli最佳压缩
        """
        output = io.BytesIO()

        # PNG 签名
        output.write(b'\x89PNG\r\n\x1a\n')

        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 3, 0, 0, 0)
        self._write_chunk(output, b'IHDR', ihdr_data)

        # PLTE chunk (调色板)
        num_colors = len(palette) // 4
        plte_data = bytes([palette[i * 4 + c] for i in range(num_colors) for c in range(3)])
        self._write_chunk(output, b'PLTE', plte_data)

        # tRNS chunk (透明度)
        trns_data = bytes([palette[i * 4 + 3] for i in range(num_colors)])
        while trns_data and trns_data[-1] == 255:
            trns_data = trns_data[:-1]
        if trns_data:
            self._write_chunk(output, b'tRNS', trns_data)

        # IDAT chunk (图像数据)
        raw_data = b''.join(
            b'\x00' + indexed_pixels[y * width:(y + 1) * width]
            for y in range(height)
        )

        # 压缩选择
        if fast_mode or not HAS_ZOPFLI:
            # 快速模式：使用 zlib (快 10x，压缩率低 ~10%)
            compressor = zlib.compressobj(9, zlib.DEFLATED, 15, 9)
            compressed = compressor.compress(raw_data) + compressor.flush()
        else:
            # 最佳模式：使用 zopfli (慢但压缩率最高)
            compressed = zopfli_compress(raw_data, numiterations=15, gzip_mode=0)

        self._write_chunk(output, b'IDAT', compressed)

        # IEND chunk
        self._write_chunk(output, b'IEND', b'')

        return output.getvalue()

    def _write_chunk(self, output: io.BytesIO, chunk_type: bytes, data: bytes):
        """写入 PNG chunk"""
        output.write(struct.pack('>I', len(data)))
        output.write(chunk_type)
        output.write(data)
        crc = zlib.crc32(chunk_type + data) & 0xffffffff
        output.write(struct.pack('>I', crc))

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
        original_bytes = input_buffer.getvalue()
        original_size = len(original_bytes)

        target_format = target_format.upper()
        if target_format == 'JPG':
            target_format = 'JPEG'

        # PNG 使用 imagequant 或 pngquant CLI
        if target_format == 'PNG' and (HAS_IMAGEQUANT or HAS_PNGQUANT):
            success = self._compress_png_raw(original_bytes, output_buffer)
            if success:
                compressed_size = len(output_buffer.getvalue())
                ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                return compressed_size, ratio

        # 其他格式或 PNG 失败时用 PIL
        input_buffer.seek(0)
        with Image.open(input_buffer) as img:
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

    def _compress_png_raw(self, png_bytes: bytes, output_buffer: io.BytesIO) -> bool:
        """
        PNG 压缩 - 优先使用 imagequant + zlib (与 wasm-image-compressor 相同算法)
        """
        # 优先使用 imagequant (与 wasm-image-compressor 相同算法)
        if HAS_IMAGEQUANT:
            try:
                with Image.open(io.BytesIO(png_bytes)) as img:
                    self._compress_png_imagequant(img, output_buffer, max_colors=256)
                    compressor_name = "zopfli" if HAS_ZOPFLI else "zlib"
                    print(f"[PNG压缩] imagequant + {compressor_name} 完成")
                    return True
            except Exception as e:
                print(f"[PNG压缩] imagequant 失败: {e}")

        # 回退到 pngquant CLI
        if HAS_PNGQUANT:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
                tmp_in_path = tmp_in.name
                tmp_in.write(png_bytes)

            tmp_out_path = tmp_in_path.replace('.png', '_out.png')

            try:
                result = subprocess.run([
                    str(PNGQUANT_PATH),
                    '128',
                    '--speed=1',
                    '--strip',
                    '--force',
                    '--output', tmp_out_path,
                    tmp_in_path
                ], capture_output=True, timeout=60)

                if result.returncode == 0 and os.path.exists(tmp_out_path):
                    with open(tmp_out_path, 'rb') as f:
                        output_buffer.write(f.read())
                    print(f"[PNG压缩] pngquant 完成")
                    return True
            except Exception as e:
                print(f"[PNG压缩] pngquant 失败: {e}")
            finally:
                for path in [tmp_in_path, tmp_out_path]:
                    try:
                        os.unlink(path)
                    except Exception:
                        pass

        return False

    def _compress_png_memory(self, img: Image.Image, output_buffer: io.BytesIO, quality: int):
        """PNG 内存压缩 - 优先使用 imagequant"""

        # 优先使用 imagequant (与 wasm-image-compressor 相同算法)
        if HAS_IMAGEQUANT:
            try:
                self._compress_png_imagequant(img, output_buffer, max_colors=256)
                print(f"[PNG压缩] imagequant 完成")
                return
            except Exception as e:
                print(f"[PNG压缩] imagequant 失败: {e}")

        # 回退到 pngquant CLI
        if HAS_PNGQUANT:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
                tmp_in_path = tmp_in.name
                img.save(tmp_in_path, 'PNG')

            tmp_out_path = tmp_in_path.replace('.png', '_out.png')

            try:
                result = subprocess.run([
                    str(PNGQUANT_PATH),
                    '128',
                    '--speed=1',
                    '--strip',
                    '--force',
                    '--output', tmp_out_path,
                    tmp_in_path
                ], capture_output=True, timeout=60)

                if result.returncode == 0 and os.path.exists(tmp_out_path):
                    with open(tmp_out_path, 'rb') as f:
                        output_buffer.write(f.read())
                    return
            except Exception:
                pass
            finally:
                for path in [tmp_in_path, tmp_out_path]:
                    try:
                        os.unlink(path)
                    except Exception:
                        pass

        # 最后回退到 Pillow
        self._compress_png_pillow_memory(img, output_buffer, 128)

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
