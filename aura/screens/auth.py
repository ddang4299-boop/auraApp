"""Màn chào: đăng nhập bằng Google hoặc bỏ qua (dùng như khách)."""
from __future__ import annotations

import flet as ft

from ..data import MONA_LISA
from ..theme import MUTED
from ..ui import T, V, body, cropped_image, logo, primary_button, screen, text_link

WELCOME_CROP = (0.0, 0.08, 1.0, 0.59)       # gương mặt và vai của Mona Lisa


def welcome(app, q) -> ft.View:
    p = MONA_LISA
    cw = app.content_width
    content = body([
        V(25),
        logo(40),
        V(13.5),
        T("Mỗi bức tranh, một câu chuyện.", 27, serif=True),
        V(27.5),
        cropped_image(p.image, p.aspect, cw, 270, WELCOME_CROP, on_click=lambda e: app.go("/home")),
        V(6.5),
        T(f"{p.artist} · {p.year} · {p.museum}", 10, 400, MUTED),
        V(21.5),
        T("Cùng nhìn chậm một chút.", 23, serif=True),
        V(9.5),
        T("Khám phá nghệ thuật Phục Hưng, từ một nếp vải đến những câu chuyện phía sau bức tranh.",
          14, 400, MUTED),
        V(30),
        primary_button("Tiếp tục với Google", lambda e: app.social_login("google")),
        V(19.5),
        text_link("Bỏ qua", lambda e: app.go("/home")),
    ], bottom=24)
    return screen("/", content)
