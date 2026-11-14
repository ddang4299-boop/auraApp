"""Làm nhẹ ảnh và font cho bản web (chạy lại mỗi khi thay ảnh trong assets/images/ hoặc font trong assets/fonts/).

    python tools/optimize_assets.py        (cần Pillow và fonttools: pip install pillow fonttools)

Mọi file gốc giữ nguyên, bản nhẹ được ghi ra chỗ riêng:
- assets/images/home/*.jpg -> assets/images/home/thumb/*.jpg (cạnh dài 640px).
  Thẻ ở trang chủ và trang Khái niệm chỉ rộng 58-171px; tải ảnh gốc 1000px (100-300 KB mỗi ảnh)
  làm trang chủ mở chậm trên mạng điện thoại. Trang chi tiết vẫn dùng ảnh gốc để phóng to.
- assets/images/logo.png -> assets/images/logo_splash.png (rộng 600px) cho màn chờ trong index.html:
  logo chỉ hiện rộng 250px nhưng là thứ tải đầu tiên lúc máy chủ đang khởi động.
- assets/fonts/*.ttf -> assets/fonts/web/*.ttf: chỉ giữ chữ Latin + tiếng Việt và các dấu câu, ký hiệu
  thường gặp (bỏ chữ Hy Lạp, Kirin...). Font gốc có ~2.900 glyph, nặng ~340 KB mỗi kiểu chữ.
  Ký tự không có trong bản rút gọn (hiếm) vẫn hiện được nhờ font dự phòng của trình duyệt.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"
FONTS = ROOT / "assets" / "fonts"
THUMB_LONG = 640        # thẻ khái niệm ~171px, vùng cắt ~60% ảnh: 640px vẫn nét trên màn hình mật độ 2x
SPLASH_W = 600          # logo màn chờ hiện 250px: đủ nét đến mật độ 2,4x
# Latin cơ bản + mở rộng, dấu kết hợp, Latin mở rộng bổ sung (có đủ chữ Việt), dấu câu, chỉ số, tiền tệ,
# ký hiệu chữ, phân số, mũi tên, toán, hình học, dingbat (✓ ✨)
FONT_UNICODES = ("U+0020-007E,U+00A0-024F,U+0300-036F,U+1E00-1EFF,U+2000-206F,U+2070-209F,U+20A0-20CF,"
                 "U+2100-214F,U+2150-218F,U+2190-21FF,U+2200-22FF,U+25A0-25FF,U+2700-27BF,U+FFFD")


def kb(p: Path) -> int:
    return p.stat().st_size // 1024


def thumbs() -> None:
    src_dir = IMAGES / "home"
    out_dir = src_dir / "thumb"
    out_dir.mkdir(exist_ok=True)
    for src in sorted(src_dir.glob("*.jpg")):
        im = Image.open(src).convert("RGB")
        im.thumbnail((THUMB_LONG, THUMB_LONG), Image.Resampling.LANCZOS)
        dst = out_dir / src.name
        im.save(dst, "JPEG", quality=80, optimize=True, progressive=True)
        print(f"home/{src.name}: {kb(src)} KB -> thumb {kb(dst)} KB {im.size[0]}x{im.size[1]}")


def splash_logo() -> None:
    src = IMAGES / "logo.png"
    im = Image.open(src)
    im = im.resize((SPLASH_W, round(im.height * SPLASH_W / im.width)), Image.Resampling.LANCZOS)
    dst = IMAGES / "logo_splash.png"
    im.save(dst, optimize=True)          # giữ PNG đủ màu: bản 256 màu nhẹ hơn nhưng lộ vệt ở dải màu chữ
    print(f"logo.png: {kb(src)} KB -> logo_splash.png {kb(dst)} KB {im.size[0]}x{im.size[1]}")


def web_fonts() -> None:
    from fontTools import subset

    out_dir = FONTS / "web"
    out_dir.mkdir(exist_ok=True)
    for src in sorted(FONTS.glob("*.ttf")):
        dst = out_dir / src.name
        # bộ tính năng OpenType mặc định của fonttools (kern, liga, ccmp, mark/mkmk cho dấu...) là đủ:
        # app không dùng kiểu chữ thay thế (ss01, tnum...) nên bỏ các glyph đó cho nhẹ
        subset.main([str(src), f"--unicodes={FONT_UNICODES}", "--no-hinting",
                     "--name-IDs=*", "--name-languages=*", f"--output-file={dst}"])
        print(f"fonts/{src.name}: {kb(src)} KB -> web {kb(dst)} KB")


if __name__ == "__main__":
    thumbs()
    splash_logo()
    web_fonts()
