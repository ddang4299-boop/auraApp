from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Callable, Optional, Sequence

import flet as ft

from .theme import (BEIGE, BG, BLOB_GOLD, BLOB_ROSE, BORDER, BUTTON_H, GLASS, GLASS_EDGE,
                    GLASS_STRONG, GUTTER, INK, INTER_BY_WEIGHT, MUTED, NAV_ACTIVE_BG, NAV_BG,
                    NAV_CLEAR, NAV_GAP, NAV_PILL_H, PRIMARY, RADIUS, SANS_LINE_HEIGHT,
                    SERIF_LINE_HEIGHT, SHADOW_INK, SURFACE, TINT, TOP_BAR_H, WHITE)

# Bề rộng cột nội dung khi màn hình rộng hơn MAX_W (máy tính, iPad ngang). App đặt giá trị này
# ngay trước khi dựng một màn (xem AuraApp._build); None = điện thoại, cột chiếm hết bề ngang.
FRAME_W: ContextVar[Optional[float]] = ContextVar("aura_frame_w", default=None)

# Khi chụp màn hình để so với bản mẫu, vẽ thêm thanh trạng thái iOS giả
# (trên điện thoại thật hệ điều hành tự vẽ, SafeArea lo phần lề).
MOCK_DEVICE = os.environ.get("AURA_MOCK_DEVICE") == "1"
STATUS_BAR_H = 44
HOME_INDICATOR_H = 34

Handler = Optional[Callable]


# ---- Chữ ---------------------------------------------------------------------

def T(value: str = "", size: float = 14, weight: int = 400, color: str = INK, *,
      serif: bool = False, logo: bool = False, italic: bool = False,
      lh: float | None = None, ls: float | None = None, align: ft.TextAlign | None = None,
      underline: bool = False, max_lines: int | None = None, spans=None,
      expand=None, width=None, on_tap: Handler = None, no_wrap: bool = False) -> ft.Text:
    """Tạo Text với font/khoảng cách dòng đúng theo hệ thiết kế."""
    if logo:
        family = "Montserrat"
    elif serif:
        family = "LoraMedium" if weight >= 500 else "Lora"
    elif italic:
        family = "InterItalic"
    else:
        family = INTER_BY_WEIGHT.get(weight, "Inter")
    if lh is None:
        table = SERIF_LINE_HEIGHT if serif else SANS_LINE_HEIGHT
        lh = table.get(int(size), 1.2 if (serif or logo) else 1.5)
    if ls is None:
        # Material 3 mặc định cộng letter-spacing 0.25 → luôn đặt rõ ràng.
        ls = -0.02 * size if (serif and size >= 20) else 0
    style = ft.TextStyle(
        size=size, color=color, font_family=family, height=lh, letter_spacing=ls,
        decoration=ft.TextDecoration.UNDERLINE if underline else None,
        decoration_color=color if underline else None,
    )
    return ft.Text(value, style=style, text_align=align, max_lines=max_lines,
                   overflow=ft.TextOverflow.ELLIPSIS if max_lines else None,
                   spans=spans, expand=expand, width=width, on_tap=on_tap, no_wrap=no_wrap)


LOGO_WORD = "images/logo_word.png"     # chữ AURA vẽ riêng của nhóm, tô màu đỏ rượu (nền trong suốt)
LOGO_WORD_ASPECT = 3.636               # rộng / cao
LOGO_FULL = "images/logo.png"          # chữ AURA + ngôi sao + "Art Understanding & Renaissance Analysis"
LOGO_FULL_ASPECT = 1000 / 439


def logo(height: float, *, full: bool = False) -> ft.Control:
    """Logo AURA dạng ảnh, luôn giữ đúng kích thước và nằm bên trái (kể cả trong cột co giãn).
    full=True: kèm ngôi sao và dòng chữ phụ."""
    src, aspect = (LOGO_FULL, LOGO_FULL_ASPECT) if full else (LOGO_WORD, LOGO_WORD_ASPECT)
    img = ft.Image(src=src, height=height, width=height * aspect, fit=ft.BoxFit.CONTAIN,
                   filter_quality=ft.FilterQuality.HIGH)
    return ft.Row([img], spacing=0, tight=True)


def kicker(text: str, size: float = 10, ls: float = 1.2, color: str = PRIMARY) -> ft.Text:
    """Dòng nhãn nhỏ viết hoa màu đỏ rượu (VD: ĐĂNG NHẬP CÙNG AURA)."""
    return T(text.upper(), size, 600, color, ls=ls)


def V(h: float) -> ft.Container:
    """Khoảng trống dọc."""
    return ft.Container(height=h)


def H(w: float) -> ft.Container:
    """Khoảng trống ngang."""
    return ft.Container(width=w)


def icon(name: str, size: float = 22, color: str = INK) -> ft.Image:
    """Icon nét mảnh (Lucide, giấy phép ISC) nằm trong assets/icons."""
    return ft.Image(src=f"icons/{name}.svg", width=size, height=size, color=color)


def zoom_badge(size: float = 26, **pos) -> ft.Container:
    """Huy hiệu kính lúp tròn đặt ở góc ảnh: báo cho người xem biết ảnh phóng to được.
    pos: vị trí trong Stack (right=, top=, bottom=...)."""
    return ft.Container(icon("zoom-in", size * 0.58, PRIMARY), width=size, height=size, border_radius=size / 2,
                        bgcolor=GLASS_STRONG, border=ft.Border.all(1, GLASS_EDGE),
                        alignment=ft.Alignment.CENTER,
                        shadow=[ft.BoxShadow(blur_radius=6, offset=ft.Offset(0, 1), color=f"{SHADOW_INK},0.16")],
                        **pos)


def zoom_hint(text: str) -> ft.Row:
    """Dòng hướng dẫn phóng to có kính lúp phía trước."""
    # wrap=True: màn hẹp thì chữ tự xuống dòng thay vì tràn ra ngoài
    return ft.Row([icon("zoom-in", 13, MUTED), T(text, 10, 400, MUTED, align=ft.TextAlign.CENTER)],
                  spacing=6, run_spacing=2, alignment=ft.MainAxisAlignment.CENTER,
                  vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True)


def divider(color: str = BORDER) -> ft.Container:
    return ft.Container(height=1, bgcolor=color)


# ---- Nút ---------------------------------------------------------------------

def primary_button(text: str, on_click: Handler = None, *, leading: str | None = None,
                   pill: bool = False, height: float = BUTTON_H, size: float = 14,
                   trailing_arrow: bool = False, left_aligned: bool = False,
                   padding_h: float = 18, expand_width: bool = True) -> ft.Container:
    """Nút nền đỏ rượu. Hỗ trợ icon trái, mũi tên ↗ phải, dạng viên thuốc."""
    label = T(text, size, 600, WHITE)
    items: list[ft.Control] = []
    if leading:
        items += [icon(leading, 20, WHITE), H(11)]
    items.append(label)
    if trailing_arrow:
        items += [ft.Container(expand=True), icon("arrow-up-right", 20, WHITE)]
    row = ft.Row(items, spacing=0, tight=not (trailing_arrow or left_aligned),
                 alignment=ft.MainAxisAlignment.START if (trailing_arrow or left_aligned)
                 else ft.MainAxisAlignment.CENTER,
                 vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Container(
        content=row, height=height, bgcolor=PRIMARY,
        border_radius=height / 2 if pill else RADIUS,
        padding=ft.Padding.symmetric(horizontal=padding_h),
        alignment=ft.Alignment.CENTER_LEFT if (trailing_arrow or left_aligned) else ft.Alignment.CENTER,
        on_click=on_click, ink=False, width=None if expand_width else None,
    )


def outline_button(text: str, on_click: Handler = None, height: float = BUTTON_H) -> ft.Container:
    """Nút nền kem viền be, chữ đỏ rượu."""
    return ft.Container(
        content=T(text, 14, 600, PRIMARY), height=height, bgcolor=SURFACE,
        border=ft.Border.all(1, BORDER), border_radius=RADIUS,
        alignment=ft.Alignment.CENTER, on_click=on_click,
    )


def text_link(text: str, on_click: Handler = None, size: float = 12, color: str = MUTED) -> ft.Container:
    """Liên kết chữ gạch chân căn giữa."""
    return ft.Container(
        content=T(text, size, 400, color, underline=True),
        alignment=ft.Alignment.CENTER, on_click=on_click,
    )


def chip(text: str, *, selected: bool = False, on_click: Handler = None,
         height: float = 33, size: float = 11, padding_h: float = 13) -> ft.Container:
    """Chip lọc dạng viên thuốc."""
    return ft.Container(
        content=T(text, size, 500, WHITE if selected else PRIMARY, no_wrap=True),
        height=height, padding=ft.Padding.symmetric(horizontal=padding_h),
        bgcolor=PRIMARY if selected else BG,
        border=None if selected else ft.Border.all(1, BORDER),
        border_radius=height / 2, alignment=ft.Alignment.CENTER, on_click=on_click,
    )


def tag(text: str) -> ft.Container:
    """Nhãn nhỏ nền hồng (Nổi tiếng, Viên ngọc ẩn, Tự họa?)."""
    return ft.Container(
        content=T(text, 9, 400, PRIMARY, lh=1.2), height=18,
        padding=ft.Padding.symmetric(horizontal=8), bgcolor=TINT,
        border_radius=9, alignment=ft.Alignment.CENTER,
    )


# ---- Ảnh -----------------------------------------------------------------------

def cropped_image(src: str, img_aspect: float, width: float, height: float,
                  crop: tuple[float, float, float, float] = (0, 0, 1, 1),
                  radius: float = 2, on_click: Handler = None,
                  overlays: Sequence[ft.Control] = ()) -> ft.Container:
    """Hiển thị một vùng (crop) của ảnh tranh trong khung width×height.

    crop = (x0, y0, x1, y1) theo tỉ lệ 0..1 của ảnh gốc; img_aspect = rộng/cao.
    Vùng crop được phóng sao cho phủ kín khung (giống BoxFit.COVER).
    """
    x0, y0, x1, y1 = crop
    sw = width / (x1 - x0)                  # bề rộng ảnh sau khi phóng
    sh = sw / img_aspect
    if sh * (y1 - y0) < height:             # vùng crop thấp hơn khung → phóng theo chiều cao
        sh = height / (y1 - y0)
        sw = sh * img_aspect
    left = -x0 * sw - max(0.0, (sw * (x1 - x0) - width) / 2)
    top = -y0 * sh
    img = ft.Image(src=src, width=sw, height=sh, fit=ft.BoxFit.FILL, left=left, top=top,
                   filter_quality=ft.FilterQuality.MEDIUM)
    return ft.Container(
        content=ft.Stack([img, *overlays], width=width, height=height,
                         clip_behavior=ft.ClipBehavior.HARD_EDGE),
        width=width, height=height, border_radius=radius,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, on_click=on_click,
    )


def framed_image(src: str, width: float, height: float, border: float = 2) -> ft.Container:
    """Ảnh tranh có viền mảnh màu be (thẻ trong kho tranh)."""
    return ft.Container(
        content=ft.Image(src=src, width=width, height=height, fit=ft.BoxFit.COVER),
        border=ft.Border.all(border, BORDER), width=width + 2 * border,
        height=height + 2 * border,
    )


def painting_strip(painting, *, on_click: Handler = None) -> ft.Container:
    """Thẻ be nhỏ: ảnh thu nhỏ + tên tranh + tác giả (Quiz, Kết quả)."""
    return ft.Container(
        content=ft.Row([
            ft.Container(ft.Image(src=painting.image, width=49, height=66, fit=ft.BoxFit.COVER),
                         border_radius=2, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
            H(12.5),
            ft.Column([
                T(painting.title, 13, 600, INK),
                V(4.5),
                T(f"{painting.artist} · {painting.year}", 11, 400, MUTED),
            ], spacing=0, tight=True, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=BEIGE, border_radius=RADIUS, height=90,
        padding=ft.Padding.symmetric(horizontal=12), on_click=on_click,
    )


# ---- Khung màn hình ------------------------------------------------------------

def top_bar(title: str, *, on_back: Handler = None, leading: str = "arrow-left",
            trailing: str | None = "aura", on_trailing: Handler = None,
            trailing_color: str = INK, offset_top: float = 0) -> ft.Container:
    """Thanh tiêu đề: nút quay lại + tiêu đề + logo AURA / icon bên phải."""
    if trailing == "aura":
        right: ft.Control = logo(17)
    elif trailing:
        size = 22 if trailing == "info" else 24
        right = ft.Container(icon(trailing, size, trailing_color), on_click=on_trailing)
    else:
        right = ft.Container()
    return ft.Container(
        content=ft.Row([
            ft.Container(icon(leading, 24, INK), on_click=on_back, width=40,
                         alignment=ft.Alignment.CENTER_LEFT),
            T(title, 14, 500, INK, expand=True, max_lines=1),
            right,
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=TOP_BAR_H, margin=ft.Margin.only(top=offset_top),
        padding=ft.Padding.only(left=22, right=GUTTER if trailing == "aura" else 22),
    )


# Các mục trên thanh điều hướng (tham số `active` của nav_bar). Nút Scan ở giữa không phải một mục.
NAV_HOME, NAV_GALLERY, NAV_ASK, NAV_SETTINGS = range(4)
# Màn của một bức tranh (tổng quan, chi tiết, trò chuyện, tư liệu, quiz...) thuộc mục Kho tranh
NAV_PAINTING = NAV_GALLERY

NAV_ITEMS = [("compass", "Khám phá", "/home"),
             ("image", "Kho tranh", "/gallery"),
             ("message-circle", "Hỏi Aura", "/ask"),
             ("settings", "Cài đặt", "/settings")]


def nav_bar(app, active: int) -> ft.Container:
    """Thanh điều hướng nổi dạng viên thuốc (bo tròn hẳn hai đầu): Khám phá · Kho tranh · [Scan] ·
    Hỏi Aura · Cài đặt, icon nét mảnh + nhãn nhỏ.

    Điện thoại: nổi ở cạnh dưới, nội dung cuộn bên dưới thanh. Máy tính: gọn ở góc trên (xem screen).
    Chỉ dùng nền màu đặc và một lớp bóng tĩnh: KHÔNG làm mờ nền (blur), không có hiệu ứng chạy liên
    tục, nên nhẹ cho điện thoại yếu và cho máy chủ miễn phí."""
    items = []
    w = app.page_width
    # điện thoại hẹp (320-360px): chữ nhỏ hơn một chút, bỏ khe giữa các mục, và chừa lề hai đầu thanh
    # rộng hơn để chữ "Khám phá" / "Cài đặt" không lấn vào phần bo tròn
    narrow = w < 360
    pad = 12 if w >= 400 else (9 if w >= 370 else 7)
    label_size = 9.5 if narrow else 10
    for i, (ic, label, route) in enumerate(NAV_ITEMS):
        on = i == active
        color = PRIMARY if on else MUTED
        items.append(ft.Container(
            ft.Column([icon(ic, 20, color), V(3),
                       T(label, label_size, 600 if on else 500, color, lh=1.1, no_wrap=True)],
                      spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            height=NAV_PILL_H - 10, border_radius=(NAV_PILL_H - 10) / 2,
            padding=ft.Padding.symmetric(horizontal=pad), alignment=ft.Alignment.CENTER,
            bgcolor=NAV_ACTIVE_BG if on else None,
            on_click=lambda e, r=route: app.go(r)))
    # Nút Scan ở giữa thanh: chưa có chức năng thật, bấm vào báo "sắp ra mắt"
    items.insert(2, ft.Container(icon("scan-camera", 21, WHITE), width=44, height=44, border_radius=22,
                                 bgcolor=PRIMARY, alignment=ft.Alignment.CENTER,
                                 tooltip="Scan ảnh tác phẩm (sắp ra mắt)",
                                 on_click=lambda e: scan_soon(app.page)))
    return ft.Container(
        ft.Row(items, spacing=0 if narrow else 2, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=NAV_PILL_H, padding=ft.Padding.symmetric(horizontal=10 if narrow else 4, vertical=4),
        bgcolor=NAV_BG, border_radius=NAV_PILL_H / 2,
        border=ft.Border.all(1, BORDER),
        shadow=[ft.BoxShadow(blur_radius=16, spread_radius=-4, offset=ft.Offset(0, 6),
                             color=f"{SHADOW_INK},0.16")])


def scan_soon(page: ft.Page) -> None:
    """Hộp thông báo nhẹ cho nút Scan ảnh (tính năng chưa ra mắt), cùng tông màu với app."""
    page.show_dialog(ft.AlertDialog(
        bgcolor=BG,
        content=ft.Column([
            ft.Container(icon("scan-camera", 30, PRIMARY), width=64, height=64, border_radius=32,
                         bgcolor=TINT, alignment=ft.Alignment.CENTER),
            V(14),
            T("Scan ảnh tác phẩm", 21, serif=True, align=ft.TextAlign.CENTER),
            V(8),
            T("Tính năng Scan ảnh tác phẩm sẽ ra mắt trong bản cập nhật tới!", 13, 400, MUTED,
              align=ft.TextAlign.CENTER),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        actions=[ft.TextButton(content=T("Đã hiểu", 13, 600, PRIMARY), on_click=lambda e: page.pop_dialog())],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    ))


def _status_bar() -> ft.Container:
    """Thanh trạng thái iOS giả lập — chỉ dùng khi chụp so sánh với bản mẫu."""
    bars = ft.Row([ft.Container(width=3, height=h, bgcolor=INK, border_radius=1)
                   for h in (4, 6, 8.5, 11)], spacing=1.6,
                  vertical_alignment=ft.CrossAxisAlignment.END)
    battery = ft.Row([
        ft.Container(ft.Container(bgcolor=INK, border_radius=2), width=25, height=12,
                     padding=2, border=ft.Border.all(1, ft.Colors.with_opacity(0.4, INK)),
                     border_radius=4),
        ft.Container(width=1.5, height=4, bgcolor=ft.Colors.with_opacity(0.4, INK)),
    ], spacing=1, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Container(
        content=ft.Row([
            T("9:41", 14, 600, INK, lh=1.0), ft.Container(expand=True),
            bars, H(6), ft.Icon(ft.Icons.WIFI, size=16, color=INK), H(6), battery,
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=STATUS_BAR_H, padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=4),
    )


def _home_indicator() -> ft.Container:
    return ft.Container(
        content=ft.Container(width=120, height=4.5, bgcolor=INK, border_radius=3),
        height=HOME_INDICATOR_H, alignment=ft.Alignment(0, 0.25),
    )


def pad(control: ft.Control, h: float = GUTTER) -> ft.Container:
    return ft.Container(control, padding=ft.Padding.symmetric(horizontal=h))


def body(controls: Sequence[ft.Control], *, scroll: bool = True, bottom: float = 0,
         auto_scroll: bool = False, ref: ft.Ref | None = None) -> ft.Column:
    """Phần nội dung cuộn. Control có data='bleed' được tràn hết chiều ngang."""
    wrapped = [c if getattr(c, "data", None) == "bleed" else pad(c) for c in controls]
    if bottom:
        wrapped.append(V(bottom))
    return ft.Column(wrapped, spacing=0, expand=True, ref=ref,
                     scroll=ft.ScrollMode.HIDDEN if scroll else None,
                     auto_scroll=auto_scroll,
                     horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def backdrop(content: ft.Control) -> ft.Container:
    """Nền kem có vài vầng màu rất mờ (hồng đất, vàng nhạt) để lớp kính phía trên có chiều sâu.
    Chỉ là gradient tĩnh, vẽ một lần: không tốn gì khi cuộn."""
    layer = ft.Container(content, expand=True, gradient=ft.RadialGradient(
        center=ft.Alignment(-1.1, 1.05), radius=0.95, colors=[BLOB_GOLD, f"{BLOB_GOLD},0"]))
    layer = ft.Container(layer, expand=True, gradient=ft.RadialGradient(
        center=ft.Alignment(1.15, -0.85), radius=0.8, colors=[BLOB_ROSE, f"{BLOB_ROSE},0"]))
    return ft.Container(layer, expand=True, bgcolor=BG)


def glass(content: ft.Control | None = None, *, radius: float = 16, padding=None, strong: bool = False,
          shadow: bool = False, on_click: Handler = None, **kw) -> ft.Container:
    """Khung kính mờ: nền trắng trong suốt, viền sáng mảnh, bóng nâu rất nhẹ (tuỳ chọn)."""
    return ft.Container(
        content, bgcolor=GLASS_STRONG if strong else GLASS, border_radius=radius, padding=padding,
        border=ft.Border.all(1, GLASS_EDGE),
        shadow=[ft.BoxShadow(blur_radius=22, spread_radius=-8, offset=ft.Offset(0, 8),
                             color=f"{SHADOW_INK},0.16")] if shadow else None,
        on_click=on_click, **kw)


def screen(route: str, content: ft.Control, *, top: ft.Control | None = None,
           footer: ft.Control | None = None, nav: ft.Control | None = None,
           aside: ft.Control | None = None) -> ft.View:
    """Lắp một màn hình hoàn chỉnh: (thanh trạng thái) + top bar + nội dung + footer + nav.

    Màn hình rộng (máy tính): cột nội dung rộng tối đa MAX_W đặt giữa; nếu có `aside`
    (vd tranh lớn ở màn chat) thì aside chiếm phần bên trái, cột nội dung bên phải.
    Thanh điều hướng (nav): máy tính đặt gọn ở góc trên; điện thoại nổi ở cạnh dưới. Màn có footer
    (ô chat) thì thanh nằm ngay dưới footer, không đè lên ô nhập."""
    fw = FRAME_W.get()
    floating = nav is not None and not fw and footer is None
    if floating and isinstance(content, ft.Column) and content.scroll:
        content.controls.append(V(NAV_CLEAR))     # cuộn hết trang thì mục cuối vẫn nằm trên thanh nổi
    parts: list[ft.Control] = []
    if MOCK_DEVICE:
        parts.append(_status_bar())
    if top is not None:
        parts.append(top)
    parts.append(content)
    if footer is not None:
        parts.append(footer)
    if nav is not None and not fw and footer is not None:
        parts.append(ft.Container(ft.Row([nav], alignment=ft.MainAxisAlignment.CENTER),
                                  padding=ft.Padding.only(bottom=NAV_GAP)))
    if MOCK_DEVICE:
        parts.append(_home_indicator())
    col = ft.Column(parts, spacing=0, expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    if fw:
        main = ft.Container(col, width=fw)
        if aside is not None:
            layout: ft.Control = ft.Row([ft.Container(aside, expand=True), main], spacing=0,
                                        vertical_alignment=ft.CrossAxisAlignment.STRETCH, expand=True)
        else:
            layout = ft.Row([main], spacing=0, alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH, expand=True)
        if nav is not None:
            header = ft.Container(ft.Row([nav], alignment=ft.MainAxisAlignment.END),
                                  padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=12, bottom=4))
            layout = ft.Column([header, layout], spacing=0, expand=True,
                               horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    else:
        layout = col
    if floating:
        # Thanh nổi đè lên nội dung; phần trống hai bên thanh vẫn chạm xuyên xuống nội dung bên dưới.
        dock = ft.Container(ft.Row([nav], alignment=ft.MainAxisAlignment.CENTER),
                            left=0, right=0, bottom=NAV_GAP)
        layout = ft.Stack([layout, dock], expand=True, fit=ft.StackFit.EXPAND)
    root: ft.Control = layout if MOCK_DEVICE else ft.SafeArea(layout, expand=True)
    return ft.View(route=route, controls=[backdrop(root)], padding=0, spacing=0, bgcolor=BG)


def card(content: ft.Control, *, bgcolor: str = GLASS, border: str | None = GLASS_EDGE,
         padding=None, radius: float = RADIUS, on_click: Handler = None, **kw) -> ft.Container:
    return ft.Container(content, bgcolor=bgcolor,
                        border=ft.Border.all(1, border) if border else None,
                        border_radius=radius, padding=padding, on_click=on_click,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, **kw)


def source_line(text: str, on_click: Handler = None, size: float = 10) -> ft.Container:
    """Dòng nguồn có icon sách: '📖 Thông tin & ảnh: Bảo tàng Louvre, Paris ↗'."""
    return ft.Container(ft.Row([icon("book-open", 15, MUTED), H(8.5), T(text, size, 400, MUTED,
                                                                       expand=True)],
                               spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        on_click=on_click)


def surface_field(**kw) -> dict:
    """Thuộc tính chung cho TextField không viền đặt trong khung tự vẽ."""
    return dict(border=ft.InputBorder.NONE, dense=True, filled=False,
                cursor_color=PRIMARY, content_padding=ft.Padding.all(0), **kw)


def snack(page: ft.Page, message: str) -> None:
    page.show_dialog(ft.SnackBar(T(message, 13, 500, WHITE), bgcolor=INK,
                                 behavior=ft.SnackBarBehavior.FLOATING))


def bottom_sheet(page: ft.Page, title: str, text: str) -> None:
    """Bảng trượt từ dưới lên, cao vừa đúng nội dung (scrollable=True cho phép cao hơn
    mức mặc định 9/16 màn hình khi nội dung dài)."""
    page.show_dialog(ft.BottomSheet(
        ft.Container(ft.Column([
            ft.Container(ft.Container(width=36, height=4, bgcolor=BORDER, border_radius=2),
                         alignment=ft.Alignment.CENTER),
            V(18), T(title, 23, 400, INK, serif=True), V(10), T(text, 14, 400, INK), V(12),
        ], spacing=0, tight=True), padding=ft.Padding.only(left=24, right=24, top=12, bottom=24)),
        bgcolor=BG, show_drag_handle=False, scrollable=True,
    ))


__all__ = [n for n in dir() if not n.startswith("_")] + ["_status_bar"]


def avatar(profile, size: float = 36, on_click: Handler = None) -> ft.Container:
    """Ảnh đại diện tròn: ảnh từ tài khoản Google nếu có, không thì chữ cái đầu."""
    if profile is not None and getattr(profile, "avatar_url", ""):
        inner: ft.Control = ft.Image(src=profile.avatar_url, width=size, height=size,
                                     fit=ft.BoxFit.COVER,
                                     error_content=T(profile.initials, size * 0.4, 400, PRIMARY,
                                                     serif=True, ls=0, lh=1.0))
    else:
        initials = profile.initials if profile is not None else "A"
        inner = T(initials, size * 0.4, 400, PRIMARY, serif=True, ls=0, lh=1.0)
    return ft.Container(inner, width=size, height=size, border_radius=size / 2, bgcolor=TINT,
                        border=ft.Border.all(1.5, PRIMARY), alignment=ft.Alignment.CENTER,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, on_click=on_click)
