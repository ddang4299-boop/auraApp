"""Màn Kho tranh và Đã lưu: trưng bày kiểu bảo tàng.

- Tab lọc tối giản (chữ + gạch chân) theo trường phái / chủ đề.
- "Tranh nổi bật": dải tranh treo tường trượt ngang.
- "Phòng trưng bày": mỗi tranh một khung lớn, đúng tỉ lệ, xếp so le trái – phải, có biển tên
  (chữ có chân cho tên tranh, chữ không chân cho thông tin và nút) và khoảng trống rộng.
- Chạm vào tranh: khung phóng nhẹ lên rồi mới mở trang tác phẩm (hiệu ứng chạy trên máy người xem).
Không dùng làm mờ nền hay hiệu ứng chạy liên tục: chỉ khung, viền và một lớp bóng tĩnh.
"""
from __future__ import annotations

import asyncio
import unicodedata

import flet as ft

from ..data import FEATURED, FILTERS, GRID, PAINTINGS, Painting
from ..theme import (BORDER, GLASS_EDGE, GLASS_STRONG, INK, MAT_BG, MUTED, PRIMARY, SHADOW_INK, SURFACE,
                     TINT)
from ..ui import (H, NAV_GALLERY, T, V, body, icon, kicker, nav_bar, primary_button, screen, surface_field,
                  top_bar)

FRAME_WOOD = "#6B4F3A"          # nẹp khung tranh: nâu gỗ ấm (cùng họ màu nâu của AURA)
WALL_SHADOW = [ft.BoxShadow(blur_radius=18, spread_radius=-6, offset=ft.Offset(0, 10),
                            color=f"{SHADOW_INK},0.24")]
FEATURED_W = 248


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def bookmark_icon(on: bool, size: float = 20, off_color: str = MUTED) -> ft.Control:
    """Đã lưu: dấu trang tô kín màu thương hiệu; chưa lưu: chỉ viền."""
    return icon("bookmark-filled" if on else "bookmark", size, PRIMARY if on else off_color)


def _bookmark(app, p: Painting, on_change=None) -> ft.Control:
    ic = ft.Container(bookmark_icon(p.id in app.state.saved), padding=6,
                      tooltip="Lưu / bỏ lưu tác phẩm")

    def toggle(e):
        on = app.toggle_saved(p.id)
        ic.content = bookmark_icon(on)
        if on_change is not None:          # vd đang ở phần Đã lưu: bỏ lưu thì tranh rời khỏi danh sách
            on_change()
        else:
            ic.update()
    ic.on_click = toggle
    return ic


def framed(p: Painting, max_w: float, max_h: float, mat: float = 10) -> ft.Container:
    """Tranh trong khung: nẹp gỗ mảnh + lớp giấy bồi + bóng tĩnh như tranh treo tường. Giữ đúng tỉ lệ ảnh."""
    inner_w = max_w - 2 * (mat + 3)
    inner_h = max_h - 2 * (mat + 3)
    w = min(inner_w, inner_h * p.aspect)
    h = w / p.aspect
    img = ft.Image(src=p.image, width=w, height=h, fit=ft.BoxFit.COVER, filter_quality=ft.FilterQuality.MEDIUM)
    return ft.Container(
        ft.Container(img, padding=mat, bgcolor=MAT_BG),
        border=ft.Border.all(3, FRAME_WOOD), shadow=WALL_SHADOW, bgcolor=MAT_BG)


async def _open(app, holder: ft.Container, route: str) -> None:
    """Phóng nhẹ khung tranh (Flutter tự chạy hiệu ứng) rồi mở trang tác phẩm."""
    holder.scale = 1.04
    try:
        holder.update()
    except Exception:
        pass
    await asyncio.sleep(0.17)
    holder.scale = 1                       # trở về cỡ cũ khi quay lại Kho tranh
    app.go(route)


def _zoomable(app, content: ft.Control, p: Painting) -> ft.Container:
    holder = ft.Container(content, scale=1, animate_scale=ft.Animation(170, ft.AnimationCurve.EASE_OUT))
    holder.on_click = lambda e: app.page.run_task(_open, app, holder, f"/painting/{p.id}")
    return holder


def featured_card(app, p: Painting) -> ft.Control:
    """Tranh nổi bật: treo trên "bức tường" kem, biển tên ngắn bên dưới."""
    frame = _zoomable(app, ft.Container(framed(p, FEATURED_W, 300), alignment=ft.Alignment.BOTTOM_CENTER,
                                        height=300), p)
    return ft.Container(ft.Column([
        frame,
        V(16),
        T(p.title, 19, serif=True, ls=0, max_lines=2, align=ft.TextAlign.CENTER),
        V(5),
        T(f"{p.artist} · {p.year}", 11, 400, MUTED, max_lines=1, align=ft.TextAlign.CENTER),
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), width=FEATURED_W)


def exhibit(app, p: Painting, width: float, k: int, on_change=None) -> ft.Control:
    """Một tác phẩm trong phòng trưng bày: khung lớn + biển tên kiểu bảo tàng, so le trái/phải."""
    card_w = width * 0.9
    frame = _zoomable(app, framed(p, card_w, 380), p)
    groups = " · ".join(f.upper() for f in p.filters)
    label = ft.Container(ft.Column([
        kicker(groups, 9, 1.0),
        V(6),
        T(p.title, 22, serif=True),
        V(4),
        T(f"{p.artist} · {p.year}", 12, 400, MUTED),
        V(2),
        T(p.museum, 11, 400, MUTED),
        V(10),
        T(p.teaser, 13, 400, INK, italic=True),
        V(12),
        ft.Row([
            ft.Container(ft.Row([T("Xem tác phẩm", 12, 600, PRIMARY), H(8), icon("arrow-up-right", 15, PRIMARY)],
                                spacing=0, tight=True),
                         height=34, padding=ft.Padding.symmetric(horizontal=14), border_radius=17,
                         bgcolor=TINT, alignment=ft.Alignment.CENTER,
                         on_click=lambda e: app.page.run_task(_open, app, frame, f"/painting/{p.id}")),
            ft.Container(expand=True),
            _bookmark(app, p, on_change),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
    ], spacing=0, tight=True), bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=6,
        padding=ft.Padding.only(left=16, right=10, top=14, bottom=12), width=card_w)
    left = k % 2 == 0
    col = ft.Column([frame, V(14), label], spacing=0, tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.START if left else ft.CrossAxisAlignment.END)
    return ft.Row([col], alignment=ft.MainAxisAlignment.START if left else ft.MainAxisAlignment.END)


def exhibit_list(app, items: list[Painting], width: float, on_change=None) -> ft.Control:
    rows: list[ft.Control] = []
    for k, p in enumerate(items):
        if k:
            rows.append(V(40))             # khoảng thở giữa hai tác phẩm, như trên tường bảo tàng
        rows.append(exhibit(app, p, width, k, on_change))
    return ft.Column(rows, spacing=0, tight=True)


def _segment(tab: str, n_saved: int, on_select) -> ft.Control:
    """Công tắc hai phần ở đầu Kho tranh: Bộ sưu tập | Đã lưu (kèm số tranh đã lưu)."""
    def part(key: str, text: str, ic: str) -> ft.Control:
        on = key == tab
        return ft.Container(ft.Row([icon(ic, 15, PRIMARY if on else MUTED), H(7),
                                    T(text, 13, 600 if on else 500, INK if on else MUTED, no_wrap=True)],
                                   spacing=0, tight=True, alignment=ft.MainAxisAlignment.CENTER),
                            expand=True, height=38, border_radius=19, alignment=ft.Alignment.CENTER,
                            bgcolor=SURFACE if on else None,
                            border=ft.Border.all(1, BORDER) if on else None,
                            on_click=lambda e: on_select(key))
    return ft.Container(ft.Row([part("all", "Bộ sưu tập", "image"),
                                part("saved", f"Đã lưu · {n_saved}", "bookmark")], spacing=4),
                        padding=4, border_radius=23, bgcolor=TINT)


def _saved_empty(app, on_browse) -> ft.Control:
    return ft.Container(ft.Column([
        icon("bookmark", 32, MUTED), V(12),
        T("Chưa có tranh nào được lưu.", 14, 600, INK), V(6),
        T("Chạm biểu tượng dấu trang trên một bức tranh để lưu lại và xem sau.", 13, 400, MUTED,
          align=ft.TextAlign.CENTER),
        V(20), primary_button("Xem bộ sưu tập", lambda e: on_browse(), pill=True, height=44),
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(vertical=40, horizontal=12),
        bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=8)


def _tabs(selected: str, on_select) -> ft.Row:
    """Tab lọc tối giản: chữ, gạch chân đỏ rượu dưới tab đang chọn."""
    tabs = []
    for f in FILTERS:
        on = f == selected
        tabs.append(ft.Container(
            T(f, 13, 600 if on else 500, INK if on else MUTED, no_wrap=True),
            padding=ft.Padding.only(bottom=7, top=4),
            border=ft.Border.only(bottom=ft.BorderSide(2, PRIMARY if on else "#00000000")),
            on_click=lambda e, f=f: on_select(f)))
    return ft.Row(tabs, spacing=22, scroll=ft.ScrollMode.AUTO)


def build(app, q, tab: str | None = None) -> ft.View:
    """Kho tranh gồm hai phần: Bộ sưu tập (mọi tác phẩm, có tìm kiếm và tab lọc) và Đã lưu (tranh đã bấm dấu
    trang). Đổi phần ngay trên màn, không mở màn mới; /saved mở thẳng phần Đã lưu."""
    tab = tab or ("saved" if q.get("tab") == "saved" else app.state.gallery_tab)
    app.state.gallery_tab = tab
    state = {"filter": q.get("filter", "Tất cả"), "query": "", "tab": tab}
    cw = app.content_width
    tabs_holder = ft.Container()
    featured_row = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO,
                          vertical_alignment=ft.CrossAxisAlignment.START)
    featured_row.data = "bleed"
    featured_box = ft.Column(spacing=0, tight=True)
    list_holder = ft.Container()
    count = T("", 11, 400, MUTED)
    empty = T("", 13, 400, MUTED)
    seg_holder = ft.Container()
    saved_box = ft.Container()
    head_kicker = kicker("", ls=1.2)
    head_title = T("", 29, serif=True)
    head_sub = T("", 14, 400, MUTED)

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

    def render_saved() -> None:
        items = [PAINTINGS[i] for i in PAINTINGS if i in app.state.saved]
        saved_box.content = (exhibit_list(app, items, cw, on_change=lambda: refresh()) if items
                             else _saved_empty(app, lambda: switch("all")))

    def refresh(update: bool = True):
        is_all = state["tab"] == "all"
        n = len(app.state.saved)
        seg_holder.content = _segment(state["tab"], n, switch)
        head_kicker.value = ("Phòng trưng bày AURA" if is_all else "Đã lưu").upper()
        head_title.value = "Dừng lại trước một bức tranh." if is_all else "Những bức tranh bạn muốn quay lại."
        head_sub.value = ("Những góc nhìn Phục Hưng, từ quen thuộc đến ít được biết." if is_all
                          else (f"{n} tác phẩm đã lưu" if n else "Lưu một bức tranh để xem lại sau."))
        all_head.visible = all_list.visible = is_all
        saved_box.visible = not is_all
        if is_all:
            items = visible()
            tabs_holder.content = _tabs(state["filter"], select)
            feats = [p for p in FEATURED if p in items]
            cards: list[ft.Control] = [H(24)]
            for p in feats:
                cards += [featured_card(app, p), H(28)]
            featured_row.controls = cards
            featured_box.visible = bool(feats) and state["filter"] == "Tất cả" and not state["query"]
            list_holder.content = exhibit_list(app, items, cw)
            count.value = f"{len(items)} tác phẩm"
            empty.value = "" if items else "Không tìm thấy tranh phù hợp. Thử từ khoá hoặc tab khác nhé."
        else:
            featured_box.visible = False
            render_saved()
        if update:
            app.page.update()

    def switch(t: str):
        state["tab"] = app.state.gallery_tab = t
        refresh()

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
        height=46, bgcolor=GLASS_STRONG, border=ft.Border.all(1, GLASS_EDGE), border_radius=23,
        padding=ft.Padding.only(left=19, right=16))

    featured_box.controls = [
        ft.Container(T("Tranh nổi bật", 23, serif=True), padding=ft.Padding.symmetric(horizontal=24)),
        V(18),
        ft.Container(featured_row, data="bleed"),
        V(36),
    ]
    featured_box.data = "bleed"            # hàng tranh trượt ngang tràn hết chiều ngang màn hình
    all_head = ft.Column([search, V(16), tabs_holder, V(26)], spacing=0, tight=True,
                         horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    all_list = ft.Column([
        ft.Row([T("Phòng trưng bày", 23, serif=True, expand=True), count],
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(22),
        list_holder,
        empty,
        V(24),
        T("Ảnh: Wikimedia Commons (tranh thuộc phạm vi công cộng)", 11, 400, MUTED),
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    refresh(update=False)
    content = body([
        V(22),
        head_kicker,
        V(8),
        head_title,
        V(10),
        head_sub,
        V(18),
        seg_holder,
        V(20),
        all_head,
        featured_box,
        all_list,
        saved_box,
    ], bottom=25)
    route = "/saved" if tab == "saved" else "/gallery"
    return screen(route, content, top=top_bar("Kho tranh", on_back=app.back_handler, trailing="bookmark",
                                               on_trailing=lambda e: switch("saved")),
                  nav=nav_bar(app, NAV_GALLERY))


def saved(app, q) -> ft.View:
    """/saved (vd từ Cài đặt › Đã lưu): Kho tranh mở sẵn phần Đã lưu."""
    return build(app, q, tab="saved")
