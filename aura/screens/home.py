"""Màn Khám phá (trang chủ)."""
from __future__ import annotations

import flet as ft

from ..data import ARNOLFINI, CONCEPTS, FACTS, TIMELINE
from ..theme import INK, MUTED, PRIMARY, TINT, WHITE
from ..ui import (H, T, V, avatar, body, bottom_nav, bottom_sheet, card, cropped_image, divider,
                  icon, kicker, primary_button, screen)

QUESTION_CROP = (0.0, 0.273, 1.0, 0.729)


def _timeline() -> ft.Control:
    rows: list[ft.Control] = []
    for i, (year, title, text) in enumerate(TIMELINE):
        if i:
            rows.append(divider())
        rows.append(ft.Container(ft.Row([
            ft.Container(T(year, 12, 600, PRIMARY), width=44, height=44, border_radius=22,
                         bgcolor=TINT, alignment=ft.Alignment.CENTER),
            H(12),
            ft.Column([T(title, 13, 600, INK), V(2.5), T(text, 11, 400, MUTED)],
                      spacing=0, tight=True, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(top=10, bottom=13)))
    return card(ft.Column(rows, spacing=0, tight=True),
                padding=ft.Padding.only(left=16, right=16, top=3, bottom=3))


def _concept(app, title: str, short: str, long: str) -> ft.Control:
    return card(ft.Row([
        icon("book-open", 24, PRIMARY), H(11),
        ft.Column([T(title, 13, 600, INK), V(3.5), T(short, 11, 400, MUTED)],
                  spacing=0, tight=True, expand=True),
        H(12), icon("arrow-up-right", 20, PRIMARY),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.only(left=11, right=12, top=10, bottom=11.5),
        on_click=lambda e: bottom_sheet(app.page, title, long))


def _fact(title: str, text: str) -> ft.Control:
    return card(ft.Column([T(title, 13, 600, INK), V(8.5), T(text, 11, 400, MUTED)],
                          spacing=0, tight=True),
                width=188, padding=ft.Padding.only(left=12, right=12, top=9, bottom=11.5))


def build(app, q) -> ft.View:
    cw = app.content_width
    facts = ft.Row([H(24)] + [x for f in FACTS for x in (_fact(*f), H(12))] + [H(12)],
                   spacing=0, scroll=ft.ScrollMode.HIDDEN,
                   vertical_alignment=ft.CrossAxisAlignment.START)
    facts.data = "bleed"
    content = body([
        V(7.5),
        ft.Row([
            T("AURA", 37.5, 600, PRIMARY, logo=True, ls=-0.8, lh=1.0),
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
        cropped_image(ARNOLFINI.image, ARNOLFINI.aspect, cw, 220, QUESTION_CROP,
                      on_click=lambda e: app.go("/painting/arnolfini")),
        V(8.5),
        ft.Container(T("Tại sao Phục Hưng lại bắt đầu bằng việc nhìn kỹ hơn?", 24, serif=True),
                     on_click=lambda e: app.go("/chat/arnolfini")),
        V(7.5),
        T("Jan van Eyck · Chi tiết từ Chân dung vợ chồng Arnolfini", 11, 400, MUTED),
        V(25.5),
        divider(),
        V(21.5),
        T("1400–1600: những mốc thời gian chính", 21, serif=True),
        V(18.5),
        _timeline(),
        V(21.5),
        T("Khái niệm chính", 21, serif=True),
        V(15.5),
        *[x for i, c in enumerate(CONCEPTS) for x in ((V(12.5),) if i else ()) + (_concept(app, *c),)],
        V(21.5),
        T("Bạn có biết?", 21, serif=True),
        V(15.5),
        facts,
    ], bottom=24.5)
    return screen("/home", content, nav=bottom_nav(0, app.go))
