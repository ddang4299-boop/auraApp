from __future__ import annotations

import os
from typing import Callable, Optional, Sequence

import flet as ft

from .theme import (BEIGE, BG, BORDER, BUTTON_H, GUTTER, INK, INTER_BY_WEIGHT, MUTED,
                    NAV_H, PRIMARY, RADIUS, SANS_LINE_HEIGHT, SERIF_LINE_HEIGHT, SURFACE,
                    TINT, TOP_BAR_H, WHITE)

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
    """Nút nền kem viền be, chữ đỏ rượu (đăng nhập Google/Facebook)."""
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
        right: ft.Control = T("AURA", 18, 400, PRIMARY, serif=True, ls=0)
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


NAV_ITEMS = [("compass", "Khám phá", "/home"), ("book-open", "Kho tranh", "/gallery"),
             ("bookmark", "Đã lưu", "/saved")]


def bottom_nav(active: int, go: Callable[[str], None]) -> ft.Container:
    """Thanh điều hướng dưới cùng (3 tab)."""
    items = []
    for i, (ic, label, route) in enumerate(NAV_ITEMS):
        on = i == active
        items.append(ft.Container(
            content=ft.Column([
                ft.Container(icon(ic, 22, PRIMARY if on else MUTED), width=50, height=28,
                             border_radius=14, bgcolor=TINT if on else None,
                             alignment=ft.Alignment.CENTER),
                V(4),
                T(label, 10, 600 if on else 500, PRIMARY if on else MUTED, lh=1.2),
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.Alignment.TOP_CENTER,
            on_click=(lambda e, r=route: go(r)),
        ))
    return ft.Container(
        content=ft.Row(items, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        height=NAV_H, bgcolor=BG, padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=9.5),
        border=ft.Border.only(top=ft.BorderSide(1, BORDER)),
    )


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


def screen(route: str, content: ft.Control, *, top: ft.Control | None = None,
           footer: ft.Control | None = None, nav: ft.Control | None = None) -> ft.View:
    """Lắp một màn hình hoàn chỉnh: (thanh trạng thái) + top bar + nội dung + footer + nav."""
    parts: list[ft.Control] = []
    if MOCK_DEVICE:
        parts.append(_status_bar())
    if top is not None:
        parts.append(top)
    parts.append(content)
    if footer is not None:
        parts.append(footer)
    if nav is not None:
        parts.append(nav)
    if MOCK_DEVICE:
        parts.append(_home_indicator())
    col = ft.Column(parts, spacing=0, expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    root: ft.Control = col if MOCK_DEVICE else ft.SafeArea(col, expand=True)
    return ft.View(route=route, controls=[root], padding=0, spacing=0, bgcolor=BG)


def card(content: ft.Control, *, bgcolor: str = WHITE, border: str | None = BORDER,
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
    """Ảnh đại diện tròn: ảnh từ Google/Facebook nếu có, không thì chữ cái đầu."""
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
