"""Màn Thông tin tài khoản (mở từ Cài đặt): chỉnh sửa thông tin cá nhân, tài khoản liên kết.
Giới thiệu, quyền riêng tư và đăng xuất nằm ở màn Cài đặt (screens/settings.py)."""
from __future__ import annotations

import flet as ft

from .. import auth
from ..theme import BORDER, GREEN, GREEN_INK, INK, MUTED, PRIMARY, RADIUS, SURFACE, TINT, WHITE
from ..ui import (H, T, V, avatar, body, NAV_SETTINGS, nav_bar, card, divider, icon, kicker, primary_button,
                  screen, snack, surface_field, top_bar)

# "facebook"/"phone": chỉ để hiển thị hồ sơ cũ đã lưu trên máy từ trước khi bỏ hai cách đăng nhập này
PROVIDER_LABEL = {"google": "Google", "guest": "chế độ khách", "facebook": "Facebook",
                  "phone": "số điện thoại"}


def _field(label: str, value: str, *, hint: str = "", keyboard=None, multiline: bool = False,
           on_change=None) -> tuple[ft.Control, ft.TextField]:
    tf = ft.TextField(value=value, hint_text=hint, keyboard_type=keyboard, multiline=multiline,
                      min_lines=3 if multiline else 1, max_lines=5 if multiline else 1,
                      text_style=ft.TextStyle(size=14, color=INK, font_family="Inter",
                                              letter_spacing=0, height=1.5),
                      hint_style=ft.TextStyle(size=14, color=MUTED, font_family="Inter",
                                              letter_spacing=0, height=1.5),
                      on_change=on_change, **surface_field())
    box = ft.Container(tf, bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=RADIUS,
                       padding=ft.Padding.symmetric(horizontal=14, vertical=14 if multiline else 0),
                       height=None if multiline else 51, alignment=ft.Alignment.CENTER_LEFT)
    return ft.Column([T(label, 13, 500, INK), V(8), box], spacing=0, tight=True), tf


def build(app, q) -> ft.View:
    prof = app.profile
    page = app.page

    def stat(n: int, label: str) -> ft.Control:
        return ft.Column([T(str(n), 23, 400, PRIMARY, serif=True, ls=0, lh=1.1), V(2),
                          T(label, 10, 400, MUTED, align=ft.TextAlign.CENTER)],
                         spacing=0, tight=True, expand=True,
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    chats = sum(1 for c in app.state.chats.values() if any(m.role == "user" for m in c.messages))
    quizzes = sum(1 for qs in app.state.quizzes.values() if qs.phase == "graded")
    stats = card(ft.Row([stat(len(app.state.saved), "Tranh đã lưu"),
                         ft.Container(width=1, height=36, bgcolor=BORDER),
                         stat(chats, "Cuộc trò chuyện"),
                         ft.Container(width=1, height=36, bgcolor=BORDER),
                         stat(quizzes, "Quiz hoàn thành")],
                        spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                 padding=ft.Padding.symmetric(vertical=16))

    name_box, name_tf = _field("Họ và tên", prof.name if prof.name != "Khách" else "",
                               hint="Tên hiển thị của bạn")
    email_box, email_tf = _field("Email", prof.email, hint="ten@email.com",
                                 keyboard=ft.KeyboardType.EMAIL)
    phone_box, phone_tf = _field("Số điện thoại", prof.phone, hint="+84 9xx xxx 000",
                                 keyboard=ft.KeyboardType.PHONE)
    year_box, year_tf = _field("Năm sinh", prof.birth_year, hint="VD: 2001",
                               keyboard=ft.KeyboardType.NUMBER)
    bio_box, bio_tf = _field("Giới thiệu ngắn", prof.bio, multiline=True,
                             hint="Bạn thích bức tranh hay họa sĩ nào?")

    def save(e=None):
        email = (email_tf.value or "").strip()
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            snack(page, "Email chưa đúng định dạng.")
            return
        year = (year_tf.value or "").strip()
        if year and (not year.isdigit() or not 1900 <= int(year) <= 2026):
            snack(page, "Năm sinh chưa hợp lệ.")
            return
        prof.name = (name_tf.value or "").strip() or "Bạn"
        prof.email, prof.phone = email, (phone_tf.value or "").strip()
        prof.birth_year, prof.bio = year, (bio_tf.value or "").strip()
        page.run_task(app.save_profile)
        snack(page, "Đã lưu thông tin cá nhân.")
        app.rebuild()

    def linked_row(provider: str, first: bool) -> list[ft.Control]:
        label = auth.PROVIDERS[provider].label
        acc = prof.linked.get(provider)
        if acc:
            right: ft.Control = ft.Row([icon("check", 16, GREEN), H(6), T("Đã liên kết", 12, 600, GREEN_INK)],
                                       spacing=0, tight=True)
            sub = acc
        else:
            right = ft.Container(T("Liên kết", 12, 600, PRIMARY), bgcolor=TINT, border_radius=14,
                                 padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                 on_click=lambda e: app.social_login(provider, link=True))
            sub = "Chưa liên kết"
        row = ft.Container(ft.Row([
            ft.Container(T(label[0], 15, 700, WHITE, lh=1.0), width=32, height=32, border_radius=16,
                         bgcolor="#DB4437",
                         alignment=ft.Alignment.CENTER),
            H(12),
            ft.Column([T(label, 13, 600, INK), V(1), T(sub, 11, 400, MUTED, max_lines=1)],
                      spacing=0, tight=True, expand=True),
            right,
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=12))
        return ([] if first else [divider()]) + [row]

    provider_text = f"Đăng nhập bằng {PROVIDER_LABEL.get(prof.provider, prof.provider)}"
    content = body([
        V(20),
        ft.Row([
            avatar(prof, 72),
            H(16),
            ft.Column([
                T(prof.name or "Bạn", 23, serif=True),
                V(4),
                T(prof.email or prof.phone or "Chưa có email", 12, 400, MUTED, max_lines=1),
                V(8),
                ft.Container(T(provider_text, 10, 500, PRIMARY, lh=1.2), bgcolor=TINT, border_radius=9,
                             padding=ft.Padding.symmetric(horizontal=8, vertical=3)),
            ], spacing=0, tight=True, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(22),
        stats,
        V(28),
        kicker("Thông tin cá nhân"),
        V(14),
        name_box, V(14), email_box, V(14), phone_box, V(14), year_box, V(14), bio_box,
        V(20),
        primary_button("Lưu thay đổi", save),
        V(30),
        kicker("Tài khoản liên kết"),
        V(6),
        card(ft.Column(linked_row("google", True), spacing=0, tight=True),
             padding=ft.Padding.symmetric(horizontal=16)),
        V(16),
        T("Giới thiệu, quyền riêng tư và đăng xuất nằm ở mục Cài đặt.", 11, 400, MUTED,
          align=ft.TextAlign.CENTER),
    ], bottom=28)
    return screen("/profile", content, top=top_bar("Thông tin tài khoản", on_back=app.back_handler),
                  nav=nav_bar(app, NAV_SETTINGS))
