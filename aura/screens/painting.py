"""Màn Tổng quan tranh: ảnh có điểm gợi ý, mô tả, ba gợi ý nhìn, câu chuyện."""
from __future__ import annotations

import flet as ft

from ..data import PAINTINGS
from ..theme import BEIGE, INK, MUTED, PRIMARY, RADIUS, TINT, WHITE
from ..ui import (H, T, V, body, bottom_nav, cropped_image, divider, icon, kicker,
                  primary_button, screen, source_line, top_bar)

HOTSPOT = 25
NUM_WORDS = {1: "Một", 2: "Hai", 3: "Ba", 4: "Bốn"}


def _hotspot(app, p, h, w, img_h) -> ft.Control:
    return ft.Container(
        T(str(h.n), 11, 600, WHITE, lh=1.0), width=HOTSPOT, height=HOTSPOT,
        border_radius=HOTSPOT / 2, bgcolor=PRIMARY, border=ft.Border.all(2, WHITE),
        alignment=ft.Alignment.CENTER,
        left=h.x * w - HOTSPOT / 2, top=h.y * img_h - HOTSPOT / 2,
        on_click=lambda e: app.go(f"/detail/{p.id}/{h.detail}"),
    )


def _look_point(n: int, title: str, text: str) -> ft.Control:
    return ft.Row([
        ft.Column([V(1), ft.Container(T(str(n), 10, 500, PRIMARY, lh=1.0), width=23, height=23,
                                      border_radius=12, bgcolor=TINT,
                                      alignment=ft.Alignment.CENTER)], spacing=0, tight=True),
        H(12),
        ft.Column([T(title, 13, 600, INK), V(3), T(text, 13, 400, MUTED)],
                  spacing=0, tight=True, expand=True),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)


def build(app, q, pid: str = "arnolfini") -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS["arnolfini"]
    cw = app.content_width
    img_h = cw / p.aspect
    first_detail = next(iter(p.details))
    image = cropped_image(p.image, p.aspect, cw, img_h,
                          overlays=[_hotspot(app, p, h, cw, img_h) for h in p.hotspots],
                          on_click=lambda e: app.go(f"/detail/{p.id}/{first_detail}"))
    looks: list[ft.Control] = []
    for i, lp in enumerate(p.look_points):
        if i:
            looks.append(V(16))
        looks.append(_look_point(i + 1, lp.title, lp.text))

    saved = {"on": p.id in app.state.saved}

    def toggle_save(e):
        saved["on"] = app.toggle_saved(p.id)
        bar.content.controls[2] = ft.Container(
            icon("bookmark", 24, PRIMARY if saved["on"] else INK), on_click=toggle_save)
        bar.update()

    bar = top_bar("Tổng quan tranh", on_back=app.back_handler, trailing="bookmark",
                  trailing_color=PRIMARY if saved["on"] else INK, on_trailing=toggle_save,
                  offset_top=11)
    content = body([
        V(23.5),
        T(f"Nhìn chậm một chút · {p.read_time}".upper(), 10, 600, PRIMARY),
        V(5.5),
        T(p.title, 29, serif=True),
        V(10),
        T(f"{p.artist} · {p.year}", 12, 400, MUTED),
        V(27),
        image,
        V(6.5),
        T(f"{NUM_WORDS.get(len(p.hotspots), len(p.hotspots))} điểm để bắt đầu nhìn · Chạm ảnh để phóng to ↗",
          10, 400, MUTED),
        V(19.5),
        T("Bạn đang thấy gì?", 23, serif=True),
        V(11.5),
        T(p.seeing, 14, 400, INK),
        V(24),
        T("Thử nhìn theo ba gợi ý".upper(), 10, 600, PRIMARY),
        V(16),
        *looks,
        V(16),
        T("Đây là gợi ý cảm nhận, không phải đáp án duy nhất.", 10, 400, PRIMARY, italic=True),
        V(26),
        divider(),
        V(19.5),
        T("Một chút chuyện phía sau", 23, serif=True),
        V(11.5),
        T(p.story, 14, 400, INK),
        V(25.5),
        ft.Container(ft.Column([
            T(p.word[0], 12, 600, INK), V(5), T(p.word[1], 12, 400, MUTED),
        ], spacing=0, tight=True), bgcolor=BEIGE, border_radius=RADIUS,
            padding=ft.Padding.only(left=16, right=16, top=14, bottom=17)),
        V(24),
        ft.Container(ft.Column([T(p.footnote[0], 10, 400, MUTED, lh=1.6),
                                T(p.footnote[1], 10, 400, MUTED, lh=1.6)], spacing=0, tight=True),
                     on_click=lambda e: app.open_url(p.url)),
        V(15.5),
        source_line(f"Thông tin & ảnh: {p.museum} ↗", lambda e: app.open_url(p.url)),
        V(17.5),
        primary_button("Bạn tò mò điều gì? Trò chuyện với AURA", lambda e: app.go(f"/chat/{p.id}"),
                       leading="message-circle"),
    ], bottom=24.5)
    return screen(f"/painting/{p.id}", content, top=bar, nav=bottom_nav(1, app.go))
