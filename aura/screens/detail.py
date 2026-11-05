"""Màn Chi tiết tranh — phóng to một vùng, kèm vị trí trong toàn bức tranh."""
from __future__ import annotations

import flet as ft

from ..data import PAINTINGS
from ..theme import BEIGE, BORDER, INK, MUTED, PRIMARY, RADIUS, SURFACE, WHITE
from ..ui import (H, T, V, body, bottom_nav, cropped_image, icon, kicker, screen, top_bar)

ZOOMS = [1, 2, 3, 4]
BASE_ZOOM = 2            # vùng crop trong dữ liệu tương ứng mức 2×
THUMB_W, THUMB_H = 80, 110


def _crop_at(base, zoom: float, aspect_box: float, img_aspect: float):
    """Tính vùng crop ở mức phóng `zoom`, giữ tâm của vùng gốc."""
    x0, y0, x1, y1 = base
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = min(1.0, (x1 - x0) * BASE_ZOOM / zoom)
    h = w * img_aspect / aspect_box               # giữ tỉ lệ khung
    if h > 1.0:
        h = 1.0
        w = h * aspect_box / img_aspect
    cx = min(max(cx, w / 2), 1 - w / 2)
    cy = min(max(cy, h / 2), 1 - h / 2)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def build(app, q, pid: str = "arnolfini", key: str = "") -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS["arnolfini"]
    d = p.details.get(key) or next(iter(p.details.values()))
    cw = app.content_width
    box_h = 370
    state = {"zoom": BASE_ZOOM}
    img_holder = ft.Container()
    thumb_holder = ft.Container()
    zoom_label = T("", 12, 600, PRIMARY, lh=1.0)

    def refresh(update=True):
        crop = _crop_at(d.crop, state["zoom"], cw / box_h, p.aspect)
        img_holder.content = cropped_image(p.image, p.aspect, cw, box_h, crop)
        x0, y0, x1, y1 = crop
        thumb_holder.content = ft.Stack([
            ft.Image(src=p.image, width=THUMB_W, height=THUMB_H, fit=ft.BoxFit.FILL),
            ft.Container(left=x0 * THUMB_W, top=y0 * THUMB_H, width=(x1 - x0) * THUMB_W,
                         height=(y1 - y0) * THUMB_H, border=ft.Border.all(2, WHITE)),
        ], width=THUMB_W, height=THUMB_H)
        zoom_label.value = f"{state['zoom']}×"
        if update:
            app.page.update()

    def change(step: int):
        i = ZOOMS.index(state["zoom"]) + step
        if 0 <= i < len(ZOOMS):
            state["zoom"] = ZOOMS[i]
            refresh()

    refresh(update=False)
    zoom = ft.Container(ft.Row([
        ft.Container(icon("minus", 18, INK), on_click=lambda e: change(-1), padding=4),
        H(12), zoom_label, H(12),
        ft.Container(icon("plus", 18, INK), on_click=lambda e: change(1), padding=4),
    ], spacing=0, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=39.5, bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=20,
        padding=ft.Padding.symmetric(horizontal=12))
    content = body([
        V(23.5),
        kicker(d.kicker),
        V(8),
        T(d.title, 27, serif=True),
        V(27.5),
        ft.InteractiveViewer(img_holder, min_scale=1, max_scale=4, boundary_margin=0),
        V(14),
        ft.Row([T("Chi tiết tác phẩm", 11, 400, MUTED, expand=True), zoom],
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(25.5),
        ft.Container(ft.Row([
            thumb_holder, H(16),
            ft.Column([T("Vị trí trong bức tranh", 13, 600, INK), V(6.5),
                       T(d.location, 11, 400, MUTED)], spacing=0, tight=True, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BEIGE, border_radius=RADIUS, padding=ft.Padding.only(left=12, right=12, top=13, bottom=11.5)),
        V(23),
        T(d.note, 14, 400, MUTED),
        V(12.5),
        T(f"{p.title} · {p.artist} · {p.year}", 11, 500, INK),
        V(12),
        T(f"Ảnh: {p.museum}", 11, 400, MUTED),
    ], bottom=25)
    return screen(f"/detail/{p.id}/{d.key}", content,
                  top=top_bar("Chi tiết tranh", on_back=app.back_handler, leading="x"),
                  nav=bottom_nav(1, app.go))
