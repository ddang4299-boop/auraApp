"""Màn Khám phá (trang chủ)."""
from __future__ import annotations

import re

import flet as ft

from ..data import MONA_LISA
from ..theme import INK, MUTED, PRIMARY, WHITE
from ..topics import (ALL, CONCEPTS, CONCEPTS_ON_HOME, FACTS, INTRO, PERIODS, TIMELINE,
                      TIMELINE_HIGHLIGHTS, Topic)
from ..ui import (H, T, V, avatar, body, NAV_HOME, nav_bar, bottom_sheet, card, cropped_image, divider, logo,
                  icon, kicker, primary_button, screen)
from .topics import concept_grid, more_button, thumb

QUESTION_CROP = (0.0, 0.12, 1.0, 0.54)      # gương mặt Mona Lisa
ON_WINE = "#F3E6E8"                          # chữ phụ trên nền đỏ rượu


def _intro(app) -> ft.Control:
    """Thẻ "Phục Hưng là gì?": đoạn tóm tắt + nút đọc thêm (bảng trượt)."""
    title, short, long = INTRO
    return card(ft.Column([
        T(short, 14, 400, INK),
        V(12),
        ft.Row([T("Đọc thêm", 13, 600, PRIMARY), H(6), icon("arrow-up-right", 16, PRIMARY)],
               spacing=0, tight=True),
    ], spacing=0, tight=True), padding=ft.Padding.only(left=16, right=16, top=14, bottom=14),
        on_click=lambda e: bottom_sheet(app.page, title, long))


def _periods(app) -> ft.Control:
    """Ba chặng của Phục Hưng: mỗi chặng một hàng có ảnh, bấm để đọc kỹ."""
    rows: list[ft.Control] = []
    for i, t in enumerate(PERIODS):
        if i:
            rows.append(divider())
        rows.append(ft.Container(ft.Row([
            thumb(t, 58, 58),
            H(12),
            ft.Column([
                T(t.label, 11, 500, PRIMARY),
                V(2),
                T(t.title, 14, 600, INK),
                V(3),
                T(t.short, 11, 400, MUTED, max_lines=2),
            ], spacing=0, tight=True, expand=True),
            H(8), icon("arrow-up-right", 18, PRIMARY),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(top=12, bottom=12),
            on_click=lambda e, t=t: app.go(f"/topic/{t.id}")))
    return card(ft.Column(rows, spacing=0, tight=True),
                padding=ft.Padding.only(left=12, right=12, top=2, bottom=2))


def _timeline_banner(app) -> ft.Control:
    """Khối nổi bật "1300 – 1600": vài mốc tiêu biểu + nút xem toàn bộ dòng thời gian."""
    rows: list[ft.Control] = []
    picks: list[Topic] = [ALL[k] for k in TIMELINE_HIGHLIGHTS]
    for i, t in enumerate(picks):
        last = i == len(picks) - 1
        rows.append(ft.Container(ft.Row([
            ft.Container(T(re.search(r"\d{4}", t.label).group(0), 12, 600, PRIMARY, lh=1.0),
                         width=56, height=28, bgcolor=WHITE,
                         border_radius=14, alignment=ft.Alignment.CENTER),
            H(12),
            ft.Column([T(t.title, 13, 600, WHITE, max_lines=2), V(2),
                       T(t.short, 11, 400, ON_WINE, max_lines=2)],
                      spacing=0, tight=True, expand=True),
            H(8), icon("arrow-up-right", 16, ON_WINE),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=ft.Padding.only(top=11, bottom=11),
            border=None if last else ft.Border.only(bottom=ft.BorderSide(1, "#8E4A57")),
            on_click=lambda e, t=t: app.go(f"/topic/{t.id}")))
    return ft.Container(ft.Column([
        T("DÒNG THỜI GIAN", 10, 400, ON_WINE, ls=1.4),
        V(6),
        T("1300 – 1600", 40, 400, WHITE, serif=True, lh=1.1),
        V(6),
        T("Ba thế kỷ con người học cách nhìn lại thế giới: từ Petrarch đến Caravaggio.",
          13, 400, ON_WINE),
        V(10),
        *rows,
        V(14),
        ft.Container(ft.Row([T(f"Xem toàn bộ {len(TIMELINE)} mốc", 13, 600, PRIMARY), H(8),
                             icon("arrow-up-right", 16, PRIMARY)],
                            spacing=0, tight=True, alignment=ft.MainAxisAlignment.CENTER),
                     height=44, bgcolor=WHITE, border_radius=22, alignment=ft.Alignment.CENTER,
                     on_click=lambda e: app.go("/timeline"), ink=True),
    ], spacing=0, tight=True), bgcolor=PRIMARY, border_radius=12,
        padding=ft.Padding.only(left=18, right=18, top=18, bottom=18))


def _fact(app, title: str, short: str, more: str) -> ft.Control:
    return card(ft.Column([
        T(title, 13, 600, INK), V(8.5), T(short, 11, 400, MUTED), V(10),
        ft.Row([T("Tìm hiểu thêm", 11, 600, PRIMARY), H(4), icon("arrow-up-right", 14, PRIMARY)],
               spacing=0, tight=True),
    ], spacing=0, tight=True), width=200, padding=ft.Padding.only(left=12, right=12, top=10, bottom=12),
        on_click=lambda e: bottom_sheet(app.page, title, f"{short}\n\n{more}"))


def build(app, q) -> ft.View:
    cw = app.content_width
    facts = ft.Row([H(24)] + [x for f in FACTS for x in (_fact(app, *f), H(12))] + [H(12)],
                   spacing=0, scroll=ft.ScrollMode.HIDDEN,
                   vertical_alignment=ft.CrossAxisAlignment.START)
    facts.data = "bleed"
    rest = len(CONCEPTS) - CONCEPTS_ON_HOME
    content = body([
        V(7.5),
        ft.Row([
            logo(36),
            ft.Container(expand=True),
            avatar(app.profile, 38, on_click=lambda e: app.go("/profile")),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(31),
        T("Phục Hưng:\nkhi con người học\ncách nhìn lại thế giới.", 35, serif=True),
        V(15),
        T("Khám phá thời kỳ nghệ thuật trở lại với con người, không gian và ánh sáng.", 14, 400, MUTED),
        V(13.5),
        primary_button("Vào kho tranh", lambda e: app.go("/gallery"), leading="book-open"),
        V(21.5),
        kicker("Câu hỏi hôm nay", ls=1.0),
        V(11.5),
        cropped_image(MONA_LISA.image, MONA_LISA.aspect, cw, 220, QUESTION_CROP,
                      on_click=lambda e: app.go(f"/painting/{MONA_LISA.id}")),
        V(8.5),
        ft.Container(T("Tại sao Phục Hưng lại bắt đầu bằng việc nhìn kỹ hơn?", 24, serif=True),
                     on_click=lambda e: app.go(f"/chat/{MONA_LISA.id}")),
        V(7.5),
        T(f"{MONA_LISA.artist} · Chi tiết từ {MONA_LISA.title}", 11, 400, MUTED),
        V(25.5),
        divider(),
        V(21.5),
        T(INTRO[0], 21, serif=True),
        V(15.5),
        _intro(app),
        V(26),
        _timeline_banner(app),
        V(26),
        T("Ba chặng của Phục Hưng", 21, serif=True),
        V(15.5),
        _periods(app),
        V(26),
        ft.Row([T("Khái niệm chính", 21, serif=True, expand=True),
                ft.Container(T("Xem tất cả", 12, 600, PRIMARY), on_click=lambda e: app.go("/concepts"))],
               spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(15.5),
        concept_grid(app, CONCEPTS[:CONCEPTS_ON_HOME], cw),
        V(14),
        more_button(f"Xem thêm {rest} khái niệm", lambda e: app.go("/concepts")),
        V(26),
        T("Bạn có biết?", 21, serif=True),
        V(15.5),
        facts,
    ], bottom=24.5)
    return screen("/home", content, nav=nav_bar(app, NAV_HOME))
