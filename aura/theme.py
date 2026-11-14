# ---- Màu -------------------------------------------------------------------
BG = "#F6F2E8"          # nền giấy ngà
INK = "#2F2A26"         # chữ chính
MUTED = "#6B6056"       # chữ phụ (đậm hơn bản cũ #796E64 để đạt độ tương phản ≥ 4.5:1 trên nền kem)
PRIMARY = "#772F3D"     # đỏ rượu vang (thương hiệu)
SURFACE = "#FFFBF2"     # ô nhập liệu, nút viền
BORDER = "#DBD1C3"      # viền, đường kẻ
BEIGE = "#EDE6D8"       # thẻ nền be
WHITE = "#FFFFFF"
TINT = "#EFE2DF"        # hồng nhạt: chip, vòng năm, nút đang chọn
GREEN = "#4BAF72"       # đúng
GREEN_BG = "#EBF6EF"
GREEN_INK = "#1D6B3B"
WHY_BG = "#F4F9F6"      # hộp "Vì sao?"
WHY_INK = "#2D5D3F"
WHY_BORDER = "#A9D9BA"
RED = "#D86B5B"         # sai / thử lại
GOLD = "#E8A84B"        # huy hiệu
SKELETON = "#E4DCCD"

# ---- Kính mờ (glassmorphism nhẹ) -------------------------------------------
# Lớp trắng trong suốt + viền trắng đặt trên nền kem có vầng màu mờ: tạo chiều sâu như kính mờ
# mà KHÔNG dùng hiệu ứng làm mờ thật (blur), vì blur trên trình duyệt điện thoại rất tốn,
# dễ làm cuộn bị giật. Màu nền và màu thương hiệu giữ nguyên.
GLASS = "#FFFFFF,0.58"          # thẻ, khung chat, khung tranh
GLASS_STRONG = "#FFFFFF,0.78"   # ô nhập, thanh dưới
GLASS_EDGE = "#FFFFFF,0.92"     # viền sáng của kính
GLASS_LINE = "#DBD1C3,0.75"     # viền be nhạt (để kính vẫn có mép rõ trên nền sáng)
SHADOW_INK = "#5A3A2A"          # màu bóng (nâu ấm)
MAT_BG = "#EDE6D8,0.72"          # nền "giấy bồi" quanh ảnh tranh trong thẻ
BLOB_ROSE = "#EBD7D3"           # vầng hồng đất trên nền
BLOB_GOLD = "#EEDFC2"           # vầng vàng nhạt
WINE_LIGHT = "#8E4352"          # đỏ rượu sáng hơn (đầu dải màu bong bóng người dùng)
MAX_W = 560                     # bề rộng cột nội dung tối đa trên màn hình lớn
WIDE_W = 980                    # từ bề rộng này trở lên: màn chat chia hai cột (tranh | chat)

# ---- Font ------------------------------------------------------------------
# Bản rút gọn trong fonts/web/ (chỉ chữ Latin + tiếng Việt, nhẹ hơn ~60%): trình duyệt tải hết font lúc mở
# app nên font gốc ~2,4 MB làm lần mở đầu chậm. Font gốc vẫn ở fonts/; đổi font thì chạy tools/optimize_assets.py.
FONTS = {
    "Inter": "fonts/web/Inter-Regular.ttf",
    "InterMedium": "fonts/web/Inter-Medium.ttf",
    "InterSemiBold": "fonts/web/Inter-SemiBold.ttf",
    "InterBold": "fonts/web/Inter-Bold.ttf",
    "InterItalic": "fonts/web/Inter-Italic.ttf",
    "Lora": "fonts/web/Lora-Regular.ttf",
    "LoraMedium": "fonts/web/Lora-Medium.ttf",
    "Montserrat": "fonts/web/Montserrat-SemiBold.ttf",
}

INTER_BY_WEIGHT = {400: "Inter", 500: "InterMedium", 600: "InterSemiBold", 700: "InterBold"}

# Khoảng cách dòng đo từ bản thiết kế.
SANS_LINE_HEIGHT = {9: 1.4, 10: 1.5, 11: 1.545, 12: 1.5, 13: 1.54, 14: 1.5}
SERIF_LINE_HEIGHT = {17: 1.3, 18: 1.2, 19: 1.316, 21: 1.19, 22: 1.2, 23: 1.26,
                     24: 1.208, 27: 1.185, 29: 1.207, 32: 1.1, 35: 1.2}

# ---- Bố cục ----------------------------------------------------------------
GUTTER = 24             # lề trái/phải
RADIUS = 8              # bo góc thẻ & nút chữ nhật
BUTTON_H = 52
TOP_BAR_H = 36
# Thanh điều hướng nổi dạng viên thuốc: nền màu đặc + bóng tĩnh (không làm mờ nền).
NAV_BG = SURFACE               # nền đặc màu kem sáng
NAV_ACTIVE_BG = "#EEDFC2"      # nút đang chọn: vàng ấm (chữ/icon đỏ rượu, tương phản 7:1)
NAV_PILL_H = 54                # chiều cao thanh nổi
NAV_GAP = 12                   # khoảng hở giữa thanh nổi và mép màn hình
NAV_CLEAR = NAV_PILL_H + NAV_GAP + 6   # chừa chỗ cuối trang để nội dung không bị thanh che
