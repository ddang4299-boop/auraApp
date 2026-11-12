"""Các màn về thời Phục Hưng: dòng thời gian đầy đủ, toàn bộ khái niệm, trang chi tiết một mục.

/timeline        dòng thời gian 1300–1600 (mọi mốc)
/concepts        lưới tất cả khái niệm
/topic/<id>      trang chi tiết: ảnh minh hoạ, bài viết, gợi ý "Nhìn kỹ", mục trước/sau
"""
from __future__ import annotations

import flet as ft

from ..theme import GLASS_EDGE, GLASS_STRONG, BEIGE, BORDER, INK, MUTED, PRIMARY, TINT, WHITE
from ..topics import ALL, CONCEPTS, GROUPS, KIND_NAME, TIMELINE, Topic
from ..ui import (H, T, V, body, bottom_nav, card, cropped_image, icon, kicker, screen,
                  top_bar)


# ---------------------------------------------------------------------------- thẻ dùng chung
def thumb(t: Topic, w: float, h: float, radius: float = 6) -> ft.Control:
    """Ảnh nhỏ của một mục; mục không có ảnh thì hiện nhãn năm trên nền hồng."""
    if t.image:
        return cropped_image(t.image, t.aspect, w, h, t.crop, radius=radius)
    return ft.Container(T(t.label, 15 if w < 90 else 22, 400, PRIMARY, serif=True), width=w, height=h,
                        bgcolor=TINT, border_radius=radius, alignment=ft.Alignment.CENTER)


def concept_tile(app, t: Topic, w: float) -> ft.Control:
    """Ô khái niệm cỡ lớn: ảnh phía trên, tên + mô tả ngắn phía dưới."""
    return card(ft.Column([
        thumb(t, w, w * 0.72, radius=0),
        ft.Container(ft.Column([
            T(t.label.upper(), 9, 400, PRIMARY, ls=0.9),
            V(4),
            T(t.title, 14, 600, INK, max_lines=2),
            V(4),
            T(t.short, 11, 400, MUTED, max_lines=3),
        ], spacing=0, tight=True), padding=ft.Padding.only(left=12, right=12, top=10, bottom=12)),
    ], spacing=0, tight=True), width=w, on_click=lambda e: app.go(f"/topic/{t.id}"))


def concept_grid(app, items: list[Topic], width: float, gap: float = 12) -> ft.Control:
    w = (width - gap) / 2
    rows = []
    for i in range(0, len(items), 2):
        pair = [concept_tile(app, t, w) for t in items[i:i + 2]]
        if len(pair) == 1:
            pair.append(ft.Container(width=w))
        if rows:
            rows.append(V(gap))
        rows.append(ft.Row([pair[0], H(gap), pair[1]], spacing=0,
                           vertical_alignment=ft.CrossAxisAlignment.START))
    return ft.Column(rows, spacing=0, tight=True)


def more_button(text: str, on_click) -> ft.Control:
    """Nút viền "Xem thêm ..." căn giữa."""
    return ft.Container(ft.Row([T(text, 13, 600, PRIMARY), H(8), icon("arrow-up-right", 16, PRIMARY)],
                               spacing=0, tight=True, alignment=ft.MainAxisAlignment.CENTER),
                        height=46, border=ft.Border.all(1, GLASS_EDGE), border_radius=23, bgcolor=GLASS_STRONG,
                        alignment=ft.Alignment.CENTER, on_click=on_click, ink=True)


def timeline_item(app, t: Topic, last: bool) -> ft.Control:
    """Một mốc trên đường thời gian dọc: chấm + đường kẻ bên trái, thẻ có ảnh bên phải."""
    content = card(ft.Row([
        thumb(t, 72, 72),
        H(12),
        ft.Column([
            T(t.label, 12, 600, PRIMARY),
            V(2),
            T(t.title, 13, 600, INK, max_lines=3),
            V(3),
            T(t.short, 11, 400, MUTED, max_lines=3),
        ], spacing=0, tight=True, expand=True),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        padding=10, on_click=lambda e: app.go(f"/topic/{t.id}"))
    # đường kẻ = viền trái của khung chứa thẻ; chấm tròn đặt đè lên đường kẻ
    line = ft.Container(content, margin=ft.Margin.only(left=5),
                        padding=ft.Padding.only(left=17, bottom=0 if last else 12),
                        border=ft.Border.only(left=ft.BorderSide(2, "#00000000" if last else BORDER)))
    dot = ft.Container(width=12, height=12, border_radius=6, bgcolor=PRIMARY,
                       border=ft.Border.all(3, TINT), left=0, top=18)
    return ft.Stack([line, dot])


# ---------------------------------------------------------------------------- /timeline
def timeline(app, q) -> ft.View:
    items = [timeline_item(app, t, i == len(TIMELINE) - 1) for i, t in enumerate(TIMELINE)]
    content = body([
        V(12),
        kicker("Dòng thời gian", ls=1.0),
        V(8),
        T("1300 – 1600", 34, 400, PRIMARY, serif=True),
        V(6),
        T(f"{len(TIMELINE)} mốc đáng nhớ của thời Phục Hưng. Chạm vào từng mốc để đọc kỹ hơn.",
          13, 400, MUTED),
        V(20),
        *items,
    ], bottom=24)
    return screen("/timeline", content, top=top_bar("Dòng thời gian", on_back=app.back_handler),
                  nav=bottom_nav(0, app.go))


# ---------------------------------------------------------------------------- /concepts
def concepts(app, q) -> ft.View:
    content = body([
        V(12),
        kicker("Khái niệm chính", ls=1.0),
        V(8),
        T("Những ý tưởng làm nên Phục Hưng", 26, serif=True),
        V(6),
        T("Tư tưởng, kỹ thuật, chất liệu: chạm vào một ô để xem giải thích và tranh minh hoạ.",
          13, 400, MUTED),
        V(18),
        concept_grid(app, CONCEPTS, app.content_width),
    ], bottom=24)
    return screen("/concepts", content, top=top_bar("Khái niệm chính", on_back=app.back_handler),
                  nav=bottom_nav(0, app.go))


# ---------------------------------------------------------------------------- /topic/<id>
def _viewer(app, t: Topic) -> None:
    """Xem ảnh minh hoạ toàn khung, chụm hai ngón để phóng to."""
    cw = app.content_width
    max_h = (app.page.height or 874) * 0.62
    w = min(cw, max_h * t.aspect)
    h = w / t.aspect
    app.page.show_dialog(ft.BottomSheet(
        ft.Container(ft.Column([
            ft.Row([T(t.title, 16, 400, INK, serif=True, expand=True, max_lines=2),
                    ft.Container(icon("x", 22, INK), padding=4,
                                 on_click=lambda e: app.page.pop_dialog())],
                   spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            V(12),
            ft.Container(ft.InteractiveViewer(ft.Image(src=t.image, width=w, height=h, fit=ft.BoxFit.FILL),
                                              min_scale=1, max_scale=5, boundary_margin=0),
                         width=w, height=h, border_radius=4, clip_behavior=ft.ClipBehavior.HARD_EDGE),
            V(8),
            T(t.caption, 10, 400, MUTED, align=ft.TextAlign.CENTER),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=24, right=24, top=18, bottom=24)),
        bgcolor="#F6F2E8", scrollable=True, draggable=False, show_drag_handle=False))


def _hero(app, t: Topic) -> list[ft.Control]:
    if not t.image:
        return [ft.Container(T(t.label, 44, 400, PRIMARY, serif=True), height=140, bgcolor=TINT,
                             border_radius=8, alignment=ft.Alignment.CENTER), V(18)]
    cw = app.content_width
    h = min(cw / t.aspect, 340)
    return [
        ft.Container(ft.Image(src=t.image, fit=ft.BoxFit.CONTAIN, height=h), height=h, bgcolor=BEIGE,
                     border_radius=8, alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                     on_click=lambda e: _viewer(app, t)),
        V(7),
        ft.Row([T(t.caption, 10, 400, MUTED, expand=True), H(8),
                ft.Container(ft.Row([icon("search", 13, PRIMARY), H(4), T("Phóng to", 10, 600, PRIMARY)],
                                    spacing=0, tight=True), on_click=lambda e: _viewer(app, t))],
               spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        V(18),
    ]


def _look_box(text: str) -> ft.Control:
    return ft.Container(ft.Column([
        ft.Row([icon("search", 16, PRIMARY), H(8), T("NHÌN KỸ", 10, 600, PRIMARY, ls=1.0)],
               spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(8),
        T(text, 13, 400, INK),
    ], spacing=0, tight=True), bgcolor=TINT, border_radius=8,
        padding=ft.Padding.only(left=14, right=14, top=12, bottom=14))


def _nav_card(app, t: Topic | None, prev: bool) -> ft.Control:
    if t is None:
        return ft.Container(expand=True)
    return ft.Container(card(ft.Column([
        T("← Trước" if prev else "Tiếp theo →", 10, 600, PRIMARY,
          align=ft.TextAlign.LEFT if prev else ft.TextAlign.RIGHT),
        V(4),
        T(t.title, 12, 600, INK, max_lines=2, align=ft.TextAlign.LEFT if prev else ft.TextAlign.RIGHT),
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.START if prev
        else ft.CrossAxisAlignment.END), padding=12,
        on_click=lambda e: app.go(f"/topic/{t.id}")), expand=True)


def build(app, q, tid: str = "") -> ft.View:
    t = ALL.get(tid) or TIMELINE[0]
    group = GROUPS[t.kind]
    i = group.index(t)
    prev_t = group[i - 1] if i > 0 else None
    next_t = group[i + 1] if i + 1 < len(group) else None
    paras: list[ft.Control] = []
    for k, p in enumerate(t.body):
        if k:
            paras.append(V(12))
        paras.append(T(p, 14, 400, INK))
    extra: list[ft.Control] = []
    if t.look:
        extra += [V(20), _look_box(t.look)]
    if t.link:
        label, route = t.link
        extra += [V(16), ft.Container(
            ft.Row([T(label, 13, 600, WHITE, expand=True), icon("arrow-up-right", 18, WHITE)], spacing=0),
            height=46, bgcolor=PRIMARY, border_radius=23, padding=ft.Padding.only(left=18, right=16),
            alignment=ft.Alignment.CENTER_LEFT, on_click=lambda e: app.go(route), ink=True)]
    see_all = {"event": ("Xem toàn bộ dòng thời gian", "/timeline"),
               "concept": ("Xem tất cả khái niệm", "/concepts")}.get(t.kind)
    content = body([
        V(10),
        *_hero(app, t),
        T(f"{KIND_NAME[t.kind]} · {t.label}".upper(), 10, 400, PRIMARY, ls=1.0),
        V(8),
        T(t.title, 26, serif=True),
        V(10),
        T(t.short, 15, 400, MUTED, italic=True),
        V(16),
        *paras,
        *extra,
        V(24),
        ft.Row([_nav_card(app, prev_t, True), H(10), _nav_card(app, next_t, False)], spacing=0,
               vertical_alignment=ft.CrossAxisAlignment.START),
        *([V(12), more_button(see_all[0], lambda e: app.go(see_all[1]))] if see_all else []),
    ], bottom=24)
    return screen(f"/topic/{t.id}", content,
                  top=top_bar(KIND_NAME[t.kind], on_back=app.back_handler),
                  nav=bottom_nav(0, app.go))
