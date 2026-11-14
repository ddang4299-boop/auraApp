"""Hướng dẫn cho người dùng mới: hộp thoại 4 bước (hình minh hoạ + lời ngắn), có Tiếp theo / Quay lại / Bỏ qua.

Chỉ hiện ở lần đầu: đã xem hoặc bấm Bỏ qua thì ghi "aura.onboarded" vào bộ nhớ trình duyệt.
Hình minh hoạ dựng bằng chính ảnh tranh và thành phần giao diện của app (không cần thêm file ảnh).
"""
from __future__ import annotations

import flet as ft

from ..data import PAINTINGS
from ..theme import BG, BORDER, INK, MAT_BG, MUTED, PRIMARY, SHADOW_INK, SURFACE, TINT, WHITE, WINE_LIGHT
from ..ui import H, T, V, cropped_image, icon, kicker

ONBOARD_KEY = "aura.onboarded"
ILL_W, ILL_H = 264, 150


def _thumb(pid: str, w: float, h: float) -> ft.Control:
    p = PAINTINGS[pid]
    return ft.Container(cropped_image(p.image, p.aspect, w, h, (0, 0, 1, 1), radius=1), padding=4,
                        bgcolor=MAT_BG, border=ft.Border.all(2, "#6B4F3A"),
                        shadow=[ft.BoxShadow(blur_radius=8, offset=ft.Offset(0, 3), color=f"{SHADOW_INK},0.2")])


def _wall(*controls: ft.Control) -> ft.Container:
    return ft.Container(ft.Row(list(controls), alignment=ft.MainAxisAlignment.CENTER,
                               vertical_alignment=ft.CrossAxisAlignment.END, spacing=14),
                        width=ILL_W, height=ILL_H, bgcolor="#F1EADC", border_radius=12,
                        alignment=ft.Alignment.CENTER)


def _ill_welcome() -> ft.Control:
    p = PAINTINGS["mona-lisa"]
    face = ft.Container(cropped_image(p.image, p.aspect, 84, 104, (0.2, 0.08, 0.8, 0.5), radius=1), padding=5,
                        bgcolor=MAT_BG, border=ft.Border.all(2, "#6B4F3A"),
                        shadow=[ft.BoxShadow(blur_radius=10, offset=ft.Offset(0, 4), color=f"{SHADOW_INK},0.22")])
    return _wall(ft.Column([face, V(8), T("Mona Lisa · Leonardo da Vinci", 9, 500, MUTED)], spacing=0,
                           tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER))


def _ill_gallery() -> ft.Control:
    return _wall(_thumb("arnolfini", 52, 72), _thumb("madonna-pinks", 60, 76), _thumb("red-turban", 54, 70))


def _bubble(text: str, user: bool) -> ft.Control:
    box = ft.Container(T(text, 10.5, 500 if not user else 400, PRIMARY if not user else WHITE, lh=1.35),
                       padding=ft.Padding.symmetric(horizontal=11, vertical=8), width=170,
                       bgcolor=None if user else SURFACE,
                       gradient=ft.LinearGradient(colors=[WINE_LIGHT, PRIMARY]) if user else None,
                       border=None if user else ft.Border.all(1, BORDER),
                       border_radius=ft.BorderRadius.only(top_left=4 if not user else 14, top_right=14,
                                                          bottom_left=14, bottom_right=4 if user else 14))
    return ft.Row([box], alignment=ft.MainAxisAlignment.END if user else ft.MainAxisAlignment.START)


def _ill_chat() -> ft.Control:
    return ft.Container(ft.Column([
        _bubble("Điều gì giữ ánh mắt bạn lâu nhất?", False), V(8),
        _bubble("Nụ cười, khó đoán quá", True), V(8),
        _bubble("Vì sao nụ cười ấy khó đoán, theo bạn?", False),
    ], spacing=0, tight=True), width=ILL_W, height=ILL_H, bgcolor="#F1EADC", border_radius=12,
        padding=ft.Padding.symmetric(horizontal=14, vertical=12))


def _ill_ask() -> ft.Control:
    """Hỏi Aura: tả một bức tranh -> thẻ tranh dẫn thẳng vào Kho tranh; bên dưới là thanh điều hướng mới."""
    p = PAINTINGS["mona-lisa"]
    found = ft.Container(ft.Row([
        ft.Container(cropped_image(p.image, p.aspect, 22, 30, (0, 0, 1, 1), radius=1),
                     border=ft.Border.all(1.5, "#6B4F3A")),
        H(8),
        ft.Column([T("CÓ TRONG KHO TRANH", 7, 600, PRIMARY, ls=0.8), T("Mona Lisa", 12, serif=True)],
                  spacing=1, tight=True),
        H(10),
        ft.Container(T("Xem tranh", 8.5, 600, WHITE), bgcolor=PRIMARY, border_radius=9,
                     padding=ft.Padding.symmetric(horizontal=8, vertical=3)),
    ], spacing=0, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=10,
        padding=ft.Padding.symmetric(horizontal=8, vertical=6))

    def nav_icon(name: str, on: bool = False) -> ft.Control:
        ic = icon(name, 14, PRIMARY if on else MUTED)
        return ft.Container(ic, bgcolor="#EEDFC2", border_radius=10,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=3)) if on else ic
    nav = ft.Container(ft.Row([nav_icon("compass"), nav_icon("image"),
                               ft.Container(icon("scan-camera", 13, WHITE), width=24, height=24, border_radius=12,
                                            bgcolor=PRIMARY, alignment=ft.Alignment.CENTER),
                               nav_icon("message-circle", True), nav_icon("settings")],
                              spacing=12, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                       bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=20,
                       padding=ft.Padding.symmetric(horizontal=12, vertical=5))
    return ft.Container(ft.Column([
        ft.Row([_bubble("Tranh người phụ nữ cười bí ẩn?", True)], alignment=ft.MainAxisAlignment.END),
        V(6), found, V(10), nav,
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=ILL_W, height=ILL_H, bgcolor="#F1EADC", border_radius=12,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8), alignment=ft.Alignment.CENTER)


STEPS = [
    (_ill_welcome, "Chào mừng đến AURA",
     "Phòng trưng bày tranh Phục Hưng bỏ túi: nhìn chậm, tự cảm nhận, rồi đối chiếu với tư liệu của bảo tàng."),
    (_ill_gallery, "Dạo Kho tranh",
     "Lọc theo trường phái, chạm một bức để xem kỹ từng chi tiết. Bấm dấu trang để lưu, xem lại ở phần Đã lưu."),
    (_ill_chat, "Trò chuyện kiểu Socrates",
     "Ở mỗi bức tranh, AURA không đưa đáp án ngay mà hỏi để bạn tự quan sát. Bấm gợi ý hoặc gõ tự do."),
    (_ill_ask, "Hỏi Aura mọi điều",
     "Hỏi về thời Phục Hưng, hoặc tả một bức tranh: AURA đoán tên và dẫn bạn tới đúng bức trong Kho tranh."),
]


def show(app) -> None:
    """Mở hướng dẫn (bước 1)."""
    st = {"i": 0}
    dlg = ft.AlertDialog(bgcolor=BG, modal=True, content_padding=ft.Padding.only(left=20, right=20, top=20, bottom=4),
                         actions_padding=ft.Padding.only(left=12, right=12, bottom=12))

    def close(e=None):
        app.page.pop_dialog()
        app.page.run_task(_remember, app)

    def go(delta: int):
        st["i"] = max(0, min(len(STEPS) - 1, st["i"] + delta))
        render()
        dlg.update()

    def render():
        i = st["i"]
        ill, title, text = STEPS[i]
        dots = ft.Row([ft.Container(width=18 if k == i else 6, height=6, border_radius=3,
                                    bgcolor=PRIMARY if k == i else BORDER) for k in range(len(STEPS))],
                      spacing=5, alignment=ft.MainAxisAlignment.CENTER)
        dlg.content = ft.Container(ft.Column([
            ill(),
            V(16),
            kicker(f"Bước {i + 1}/{len(STEPS)}", 9, 1.1),
            V(6),
            T(title, 21, serif=True),
            V(8),
            T(text, 13, 400, INK),
            V(16),
            dots,
        ], spacing=0, tight=True), width=ILL_W)
        last = i == len(STEPS) - 1
        nxt = ft.Container(T("Bắt đầu khám phá" if last else "Tiếp theo", 13, 600, WHITE),
                           bgcolor=PRIMARY, border_radius=18, height=36,
                           padding=ft.Padding.symmetric(horizontal=16), alignment=ft.Alignment.CENTER,
                           on_click=close if last else (lambda e: go(1)))
        back = ft.TextButton(content=T("Quay lại", 13, 600, PRIMARY), on_click=lambda e: go(-1),
                             visible=i > 0)
        dlg.actions = [ft.Row([
            ft.TextButton(content=T("Bỏ qua", 13, 600, MUTED), on_click=close),
            ft.Container(expand=True), back, H(4), nxt,
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)]

    render()
    app.page.show_dialog(dlg)


async def _remember(app) -> None:
    try:
        await app.prefs.set(ONBOARD_KEY, "1")
    except Exception as e:                # trình duyệt chặn bộ nhớ: lần sau hướng dẫn hiện lại, không sao
        print(f"[onboarding] Không lưu được: {e}")


async def maybe_show(app) -> None:
    """Gọi khi app vừa mở: chưa xem hướng dẫn lần nào thì mở."""
    try:
        seen = await app.prefs.get(ONBOARD_KEY)
    except Exception:
        seen = None
    if not seen:
        show(app)
