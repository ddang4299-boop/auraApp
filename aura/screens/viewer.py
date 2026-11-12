"""Xem tranh phóng to / kéo (zoom & pan), dùng chung cho màn tranh, màn chat và cột tranh trên máy tính."""
from __future__ import annotations

import flet as ft

from ..data import Painting
from ..theme import BG, INK, MUTED, PRIMARY, TINT
from ..ui import V, T, glass, icon

ZOOM_HINT = "Chụm hai ngón tay (hoặc cuộn chuột) để phóng to, kéo để di chuyển"


def zoomable(p: Painting, w: float, h: float, *, radius: float = 4) -> ft.Container:
    """Ảnh tranh giữ đúng tỉ lệ, phóng to tới 6 lần. Mọi thao tác chạy ngay trên máy người xem
    (không gửi gì về máy chủ) nên luôn mượt."""
    return ft.Container(
        ft.InteractiveViewer(
            ft.Image(src=p.image, width=w, height=h, fit=ft.BoxFit.FILL,
                     filter_quality=ft.FilterQuality.HIGH),
            min_scale=1, max_scale=6, boundary_margin=0),
        width=w, height=h, border_radius=radius, clip_behavior=ft.ClipBehavior.HARD_EDGE)


def framed(content: ft.Control, *, mat: float = 10) -> ft.Container:
    """Khung tranh kiểu phòng trưng bày: viền giấy (passe-partout) bằng kính mờ, bóng rất nhẹ."""
    return glass(content, radius=6, padding=mat, shadow=True)


def open_viewer(app, p: Painting, *, show_details: bool = True) -> None:
    """Bảng trượt từ dưới lên: xem toàn bộ bức tranh, phóng to được; không rời màn đang xem."""
    page_h = app.page.height or 874
    cw = app.content_width
    max_h = page_h * 0.62
    w = min(cw, max_h * p.aspect)
    h = w / p.aspect

    def close(e=None):
        app.page.pop_dialog()

    def open_detail(key: str):
        app.page.pop_dialog()
        app.go(f"/detail/{p.id}/{key}")

    items: list[ft.Control] = [
        ft.Row([
            ft.Column([T(p.title, 21, 400, INK, serif=True, max_lines=1), V(3),
                       T(f"{p.artist} · {p.year}", 11, 400, MUTED, max_lines=1)],
                      spacing=0, tight=True, expand=True),
            ft.Container(icon("x", 22, INK), on_click=close, padding=4),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        V(14),
        framed(zoomable(p, w, h), mat=8),
        V(10),
        T(ZOOM_HINT, 10, 400, MUTED, align=ft.TextAlign.CENTER),
    ]
    if show_details and p.details:
        chips = [ft.Container(T(d.title, 11, 600, PRIMARY, no_wrap=True, lh=1.2), bgcolor=TINT,
                              border_radius=14, padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                              on_click=lambda e, k=d.key: open_detail(k))
                 for d in p.details.values()]
        items += [V(14), T("NHÌN KỸ MỘT CHI TIẾT", 9, 400, PRIMARY, ls=0.9), V(8),
                  ft.Row(chips, spacing=6, run_spacing=6, wrap=True,
                         alignment=ft.MainAxisAlignment.CENTER)]
    app.page.show_dialog(ft.BottomSheet(
        ft.Container(ft.Column(items, spacing=0, tight=True,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                     padding=ft.Padding.only(left=24, right=24, top=18, bottom=24)),
        bgcolor=BG, scrollable=True, draggable=False, show_drag_handle=False,
    ))


def gallery_wall(app, p: Painting) -> ft.Control:
    """Cột trái trên máy tính (màn chat): bức tranh lớn ở trung tâm như treo trên tường triển lãm."""
    avail_w = max(240.0, app.page_width - app.width - 96)
    avail_h = max(240.0, (app.page.height or 800) - 190)
    h = min(avail_h, avail_w / p.aspect)
    w = h * p.aspect
    return ft.Container(ft.Column([
        framed(zoomable(p, w, h), mat=12),
        V(16),
        T(p.title, 24, 400, INK, serif=True, align=ft.TextAlign.CENTER),
        V(4),
        T(f"{p.artist} · {p.year} · {p.museum}", 11, 400, MUTED, align=ft.TextAlign.CENTER),
        V(8),
        T(ZOOM_HINT, 10, 400, MUTED, align=ft.TextAlign.CENTER),
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER),
        alignment=ft.Alignment.CENTER, padding=ft.Padding.symmetric(horizontal=32, vertical=24))
