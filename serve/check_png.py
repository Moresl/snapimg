"""
PNG 颜色检测工具
用法: python check_png.py <图片路径>
"""
import sys
from PIL import Image

def check_png(path):
    try:
        with Image.open(path) as img:
            print(f"文件: {path}")
            print(f"尺寸: {img.size[0]} x {img.size[1]}")
            print(f"模式: {img.mode}")

            if img.mode == 'P':  # 调色板模式 (量化后的PNG)
                pixels = list(img.getdata())
                unique_colors = len(set(pixels))
                print(f"[OK] Palette PNG")
                print(f"[OK] Colors: {unique_colors}")

                if unique_colors <= 64:
                    print(f"-> 64 colors or less")
                elif unique_colors <= 128:
                    print(f"-> 128 colors or less")
                elif unique_colors <= 256:
                    print(f"-> 256 colors or less")
            else:
                # 真彩色PNG
                pixels = list(img.convert('RGB').getdata())
                unique_colors = len(set(pixels))
                print(f"[NO] True color PNG (not quantized)")
                print(f"[NO] Colors: {unique_colors}")

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_png.py <图片路径>")
        print("示例: python check_png.py C:/test.png")
    else:
        check_png(sys.argv[1])
