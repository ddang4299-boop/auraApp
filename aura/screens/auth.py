from __future__ import annotations

import flet as ft

from ..data import MONA_LISA
from ..theme import BORDER, BUTTON_H, INK, MUTED, PRIMARY, RADIUS, SURFACE
from ..ui import (H, T, V, body, cropped_image, divider, kicker, outline_button, primary_button,
                  screen, snack, surface_field, text_link, top_bar)

WELCOME_CROP = (0.0, 0.08, 1.0, 0.59)       # gương mặt và vai của Mona Lisa


def welcome(app, q) -> ft.View:
    p = MONA_LISA
    cw = app.content_width
    content = body([
        V(25),
        T("AURA", 37.5, 600, PRIMARY, logo=True, ls=-0.8, lh=1.0),
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
        V(26),
        outline_button("Tiếp tục với Google", lambda e: app.social_login("google")),
        V(12),
        outline_button("Tiếp tục với Facebook", lambda e: app.social_login("facebook")),
        V(12),
        primary_button("Tiếp tục bằng số điện thoại", lambda e: app.go("/login/phone")),
        V(19.5),
        text_link("Bỏ qua", lambda e: app.go("/home")),
    ], bottom=24)
    return screen("/", content)


def _legal_footer(lines: list[ft.Control], with_divider: bool = True, bottom: float = 19) -> ft.Container:
    return ft.Container(ft.Column(
        ([divider(), V(7.5)] if with_divider else []) + lines + [V(bottom)],
        spacing=0, tight=True), padding=ft.Padding.symmetric(horizontal=24))


def phone(app, q) -> ft.View:
    error = T("", 11, 400, PRIMARY)
    field = ft.TextField(
        value=app.state.phone, hint_text="9xx xxx 000", keyboard_type=ft.KeyboardType.PHONE,
        text_style=ft.TextStyle(size=14, color=INK, font_family="Inter", height=1.5, letter_spacing=0),
        hint_style=ft.TextStyle(size=14, color=MUTED, font_family="Inter", height=1.5, letter_spacing=0),
        expand=True, autofocus=False,
        input_filter=ft.InputFilter(regex_string=r"^[0-9 ]*$", allow=True, replacement_string=""),
        **surface_field(),
    )
    hint = T("Ví dụ định dạng · Bỏ số 0 đầu tiên sau mã +84.", 11, 400, MUTED)

    def submit(e=None):
        digits = "".join(ch for ch in (field.value or "") if ch.isdigit()).lstrip("0")
        if len(digits) < 9:
            hint.value = "Số điện thoại cần 9 chữ số sau mã +84."
            hint.style.color = PRIMARY
            hint.update()
            return
        app.state.phone = digits
        app.go("/login/otp")

    field.on_submit = submit
    box = ft.Container(
        ft.Row([T("+84", 14, 500, INK), H(13), ft.Container(width=1, height=24, bgcolor=BORDER),
                H(12.5), field], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=51, bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=RADIUS,
        padding=ft.Padding.only(left=14, right=14),
    )
    content = body([
        V(23.5), kicker("Đăng nhập cùng AURA"),
        V(8), T("Bắt đầu bằng số điện thoại.", 27, serif=True),
        V(14), T("Nhập số điện thoại để nhận mã xác thực gồm 6 chữ số và tiếp tục khám phá cùng AURA.",
                 14, 400, MUTED),
        V(30), T("Số điện thoại", 13, 500, INK),
        V(8), box,
        V(7.5), hint,
        V(33), primary_button("Nhận mã xác thực", submit),
    ])
    footer = _legal_footer([
        T("Bằng việc tiếp tục, bạn đồng ý với Điều khoản sử dụng và Chính sách bảo mật của AURA. "
          "Số điện thoại được dùng để xác thực đăng nhập.", 11, 400, MUTED),
        V(6),
        T("Điều khoản sử dụng · Chính sách bảo mật", 11, 400, PRIMARY),
    ])
    return screen("/login/phone", content, top=top_bar("Số điện thoại", on_back=app.back_handler),
                  footer=footer)


def _masked(phone: str) -> str:
    d = phone or "900000000"
    return f"+84 {d[0]}•• ••• {d[-3:]}"


def otp(app, q) -> ft.View:
    boxes: list[ft.TextField] = []
    hint = T("Nhập đủ 6 chữ số trong mã xác thực của bạn.", 11, 400, MUTED)

    def code() -> str:
        return "".join(b.value or "" for b in boxes)

    def submit(e=None):
        if len(code()) < 6:
            hint.value = "Mã xác thực cần đủ 6 chữ số."
            hint.style.color = PRIMARY
            hint.update()
            return
        app.phone_sign_in()

    async def on_change(e, i):
        v = "".join(ch for ch in (e.control.value or "") if ch.isdigit())
        if len(v) > 1:                         # dán cả mã vào một ô
            for j, ch in enumerate(v[:6 - i]):
                boxes[i + j].value = ch
            e.control.page.update()
            await boxes[min(5, i + len(v) - 1)].focus()
        else:
            e.control.value = v
            e.control.update()
            if v and i < 5:
                await boxes[i + 1].focus()
        if len(code()) == 6:
            submit()

    for i in range(6):
        boxes.append(ft.TextField(
            hint_text="—", text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER,
            text_style=ft.TextStyle(size=20, color=INK, font_family="InterSemiBold", letter_spacing=0),
            hint_style=ft.TextStyle(size=14, color=BORDER, font_family="Inter", letter_spacing=0),
            on_change=lambda e, i=i: app.page.run_task(on_change, e, i), **surface_field(),
        ))
    row = ft.Row([ft.Container(b, height=55, expand=True, bgcolor=SURFACE,
                               border=ft.Border.all(1, BORDER), border_radius=RADIUS,
                               alignment=ft.Alignment.CENTER) for b in boxes], spacing=9)
    content = body([
        V(23.5), kicker("Đăng nhập cùng AURA"),
        V(8), T("Nhập mã xác thực gồm 6 chữ số", 27, serif=True),
        V(14), T("Dùng mã xác thực cho số điện thoại của bạn để tiếp tục.", 14, 400, MUTED),
        V(10), T(_masked(app.state.phone), 14, 600, INK),
        V(28), T("Mã xác thực", 13, 500, INK),
        V(12), row,
        V(11.5), hint,
        V(33), primary_button("Xác nhận", submit),
        V(19.5), text_link("Gửi lại mã", lambda e: snack(app.page, "Đã gửi lại mã xác thực.")),
        V(30), text_link("Đổi số điện thoại", app.back_handler),
    ])
    footer = _legal_footer([T("Không chia sẻ mã xác thực với người khác để bảo vệ tài khoản của bạn.",
                              11, 400, MUTED)], with_divider=False, bottom=21)
    return screen("/login/otp", content,
                  top=top_bar("Xác thực số điện thoại", on_back=app.back_handler), footer=footer)
