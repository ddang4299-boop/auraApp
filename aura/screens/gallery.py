"""Màn Kho tranh và Đã lưu."""
from __future__ import annotations

import unicodedata

import flet as ft

from ..data import FEATURED, FILTERS, GRID, PAINTINGS, Painting
from ..theme import BEIGE, BORDER, INK, MUTED, PRIMARY, RADIUS, SURFACE, WHITE
from ..ui import (H, T, V, body, bottom_nav, card, chip, framed_image, icon, primary_button,
                  screen, surface_field, tag, top_bar)

FEATURED_W = 266
FEATURED_IMG_W = 182
FEATURED_IMG_H = 249
GRID_IMG_W = 134


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def bookmark_icon(on: bool, size: float = 20, off_color: str = MUTED) -> ft.Control:
    """Đã lưu: dấu trang tô kín màu thương hiệu; chưa lưu: chỉ viền."""
    return icon("bookmark-filled" if on else "bookmark", size, PRIMARY if on else off_color)


def _bookmark(app, p: Painting) -> ft.Control:
    ic = ft.Container(bookmark_icon(p.id in app.state.saved))

    def toggle(e):
        on = app.toggle_saved(p.id)
        ic.content = bookmark_icon(on)
        ic.update()
    ic.on_click = toggle
    return ic


def featured_card(app, p: Painting) -> ft.Control:
    # Ảnh nằm vừa trong khung 182×249 (giữ tỉ lệ), vùng nền be cao cố định.
    img_w = min(FEATURED_IMG_W, FEATURED_IMG_H * p.aspect)
    img_h = img_w / p.aspect
    return ft.Container(card(ft.Column([
        ft.Container(framed_image(p.image, img_w - 4, img_h - 4), bgcolor=BEIGE,
                     height=FEATURED_IMG_H + 48, alignment=ft.Alignment.CENTER),
        ft.Container(ft.Column([
            T(p.title, 19, serif=True, ls=0),
            V(9.5),
            T(f"{p.artist} · {p.year}", 10, 400, MUTED),
            V(10),
            ft.Row([tag(p.tag), ft.Container(expand=True), _bookmark(app, p)], spacing=0),
        ], spacing=0, tight=True), padding=ft.Padding.only(left=12, right=12, top=9.5, bottom=11.5)),
    ], spacing=0, tight=True), width=FEATURED_W, on_click=lambda e: app.go(f"/painting/{p.id}")),
        alignment=ft.Alignment.TOP_LEFT)


def grid_card(app, p: Painting, width: float) -> ft.Control:
    img_w = width - 28
    img_h = img_w / p.aspect
    return card(ft.Column([
        ft.Container(framed_image(p.image, img_w - 4, img_h - 4), bgcolor=BEIGE,
                     padding=ft.Padding.symmetric(vertical=15), alignment=ft.Alignment.CENTER),
        ft.Container(ft.Column([
            T(p.title, 13, 600, INK, lh=1.31),
            V(8.5),
            T(f"{p.artist} · {p.year}", 10, 400, MUTED),
            V(9),
            ft.Row([tag(p.tag), ft.Container(expand=True), _bookmark(app, p)], spacing=0,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=0, tight=True), padding=ft.Padding.only(left=12, right=10, top=9.5, bottom=12)),
    ], spacing=0, tight=True), on_click=lambda e: app.go(f"/painting/{p.id}"))


def masonry(app, items: list[Painting], total_w: float, gap: float = 13) -> ft.Control:
    """Lưới 2 cột so le (masonry): thẻ xếp xen kẽ trái – phải theo thứ tự."""
    col_w = (total_w - gap) / 2
    cols: list[list[ft.Control]] = [[], []]
    for k, p in enumerate(items):
        i = k % 2
        if cols[i]:
            cols[i].append(V(gap))
        cols[i].append(grid_card(app, p, col_w))
    return ft.Row([ft.Column(c, spacing=0, width=col_w, tight=True) for c in cols],
                  spacing=gap, vertical_alignment=ft.CrossAxisAlignment.START)


def build(app, q) -> ft.View:
    state = {"filter": q.get("filter", "Tất cả"), "query": ""}
    cw = app.content_width
    chips_row = ft.Row(spacing=8)
    featured_row = ft.Row(spacing=0, scroll=ft.ScrollMode.HIDDEN,
                          vertical_alignment=ft.CrossAxisAlignment.START)
    featured_row.data = "bleed"
    counter = T("", 11, 400, MUTED)
    dots = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.CENTER)
    grid_holder = ft.Container()
    grid_count = T("", 10, 400, MUTED)
    empty = T("", 13, 400, MUTED)

    def visible() -> list[Painting]:
        f, qq = state["filter"], _norm(state["query"])
        out = []
        for p in GRID:
            if f != "Tất cả" and f not in p.filters:
                continue
            if qq and qq not in _norm(p.title + " " + p.artist):
                continue
            out.append(p)
        return out

    def set_index(i: int, n: int):
        counter.value = f"{i + 1} / {n}" if n else "0 / 0"
        dots.controls = [ft.Container(width=6, height=6, border_radius=3,
                                      bgcolor=PRIMARY if j == i else BORDER) for j in range(n)]

    def on_scroll(e: ft.OnScrollEvent):
        n = len([c for c in featured_row.controls if getattr(c, "data", None) == "card"])
        i = max(0, min(n - 1, round(e.pixels / (FEATURED_W + 16))))
        set_index(i, n)
        counter.update()
        dots.update()

    featured_row.on_scroll = on_scroll

    def refresh(update: bool = True):
        items = visible()
        chips_row.controls = [chip(f, selected=f == state["filter"],
                                   on_click=lambda e, f=f: select(f)) for f in FILTERS]
        feats = [p for p in FEATURED if p in items]
        cards = []
        for p in feats:
            c = featured_card(app, p)
            c.data = "card"
            cards += [c, H(16)]
        featured_row.controls = [H(24)] + cards + [H(8)]
        set_index(0, len(feats))
        grid_holder.content = masonry(app, items, cw)
        grid_count.value = f"{len(items)} tác phẩm"
        empty.value = "" if items else "Không tìm thấy tranh phù hợp. Thử từ khoá khác nhé."
        if update:
            app.page.update()

    def select(f: str):
        state["filter"] = f
        refresh()

    def on_search(e):
        state["query"] = e.control.value or ""
        refresh()

    search = ft.Container(ft.Row([
        icon("search", 20, MUTED), H(14),
        ft.TextField(hint_text="Tìm tên tranh, họa sĩ…", on_change=on_search, expand=True,
                     text_style=ft.TextStyle(size=13, color=INK, font_family="Inter", letter_spacing=0),
                     hint_style=ft.TextStyle(size=13, color=MUTED, font_family="Inter", letter_spacing=0),
                     **surface_field()),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=46, bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=23,
        padding=ft.Padding.only(left=19, right=16))

    refresh(update=False)
    content = body([
        V(22),
        T("Dừng lại trước một bức tranh.", 29, serif=True),
        V(10.5),
        T("Những góc nhìn Phục Hưng, từ quen thuộc đến ít được biết.", 14, 400, MUTED),
        V(18.5),
        search,
        V(17),
        chips_row,
        V(21),
        ft.Row([T("Tranh nổi bật", 23, serif=True, expand=True), counter],
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(15),
        featured_row,
        V(12),
        dots,
        V(20.8),
        ft.Row([T("Mỗi tranh, một góc nhìn", 23, serif=True, expand=True), grid_count],
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(19.2),
        grid_holder,
        empty,
        V(15.6),
        T("Ảnh: Wikimedia Commons (tranh thuộc phạm vi công cộng)", 11, 400, MUTED),
    ], bottom=25.4)
    return screen("/gallery", content, top=top_bar("Kho tranh", on_back=app.back_handler),
                  nav=bottom_nav(1, app.go))


def saved(app, q) -> ft.View:
    items = [PAINTINGS[i] for i in PAINTINGS if i in app.state.saved]
    cw = app.content_width
    if items:
        main: list[ft.Control] = [masonry(app, items, cw)]
    else:
        main = [ft.Container(ft.Column([
            icon("bookmark", 32, MUTED), V(12),
            T("Chưa có tranh nào được lưu.", 14, 600, INK), V(6),
            T("Chạm biểu tượng dấu trang trên một bức tranh để lưu lại và xem sau.", 13, 400, MUTED,
              align=ft.TextAlign.CENTER),
            V(20), primary_button("Vào kho tranh", lambda e: app.go("/gallery"), pill=True,
                                  height=44),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=40, horizontal=12),
            bgcolor=WHITE, border=ft.Border.all(1, BORDER), border_radius=RADIUS)]
    content = body([
        V(22),
        T("Những bức tranh bạn muốn quay lại.", 29, serif=True),
        V(10.5),
        T(f"{len(items)} tác phẩm đã lưu", 14, 400, MUTED),
        V(24),
        *main,
    ], bottom=25)
    return screen("/saved", content, top=top_bar("Đã lưu", on_back=app.back_handler),
                  nav=bottom_nav(2, app.go))
