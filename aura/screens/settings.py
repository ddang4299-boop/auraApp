"""Màn Cài đặt (tab trên thanh điều hướng) và hai trang con: Giới thiệu (/about), Quyền riêng tư (/privacy).

Cài đặt gồm: thẻ tài khoản, Thông tin tài khoản (/profile), Đã lưu (/saved), Giới thiệu, Chính sách quyền
riêng tư, Xem lại hướng dẫn, phiên bản và Đăng xuất.
"""
from __future__ import annotations

import flet as ft

from ..app import APP_VERSION
from ..theme import BG, BORDER, INK, MUTED, PRIMARY, RADIUS, RED, TINT
from ..ui import (H, NAV_SETTINGS, T, V, avatar, body, card, divider, icon, kicker, nav_bar, primary_button,
                  screen, top_bar)

ABOUT = [
    ("AURA là gì?",
     "AURA (Art Understanding & Renaissance Analysis) là phòng trưng bày tranh Phục Hưng bỏ túi. Thay vì đưa "
     "đáp án ngay, AURA mời bạn nhìn chậm, tự nói ra điều mình thấy, rồi mới đối chiếu với tư liệu của bảo tàng."),
    ("Phương pháp Socrates",
     "Khi trò chuyện về một bức tranh, AURA hỏi trước, gợi ý sau. Cuộc trò chuyện đi qua bốn chặng: Ấn tượng "
     "đầu → Tách chi tiết → Đối thoại → Mở rộng. Câu nào bạn tự trả lời được, AURA không nói thay."),
    ("Hỏi Aura",
     "Tab Hỏi Aura dành cho câu hỏi mở: kiến thức về thời Phục Hưng, về bất kỳ bức tranh nào trên thế giới, "
     "hoặc tả một bức tranh để AURA đoán tên và dẫn bạn tới đúng bức trong Kho tranh. Câu trả lời do AI soạn "
     "nên có thể chưa hoàn hảo; thông tin ngoài tư liệu của ứng dụng luôn được ghi rõ là kiến thức chung."),
    ("Scan tác phẩm",
     "Bấm nút Scan ở giữa thanh điều hướng, khung quét mở ngay: hướng camera vào bức tranh (cả bức hay chỉ "
     "một phần) rồi bấm chụp, hoặc chọn ảnh có sẵn trong Thư viện. AURA so các điểm đặc trưng trong ảnh với "
     "tranh trong Kho tranh để nhận ra bức đó, kể cả khi ảnh nghiêng, thiếu góc hay hơi mờ. Khi chưa chắc, "
     "AURA hỏi lại thay vì đoán bừa. Scan không dùng AI bên ngoài: việc nhận diện chạy ngay trên máy chủ "
     "của AURA."),
    ("Nguồn & giấy phép",
     "Thông tin tác phẩm: Bảo tàng Louvre (Paris) và National Gallery (London). Ảnh tranh và ảnh minh hoạ: "
     "Wikimedia Commons, thuộc phạm vi công cộng. Icon: Lucide (giấy phép ISC). Phông chữ: Inter, Lora, "
     "Montserrat (SIL Open Font License). Nhận diện ảnh: OpenCV (giấy phép Apache 2.0)."),
]

PRIVACY = [
    ("Tóm tắt",
     "AURA không bán, không chia sẻ dữ liệu của bạn để quảng cáo và không yêu cầu thông tin nhạy cảm. "
     "Phần lớn dữ liệu nằm ngay trên thiết bị của bạn."),
    ("Thông tin tài khoản",
     "Nếu bạn đăng nhập Google, AURA nhận tên, email và ảnh đại diện từ Google để hiển thị hồ sơ. Những gì "
     "bạn tự điền ở Thông tin tài khoản (số điện thoại, năm sinh, giới thiệu) cũng chỉ dùng để hiển thị. "
     "Bạn có thể dùng AURA ở chế độ khách mà không cần đăng nhập."),
    ("Dữ liệu lưu trên thiết bị",
     "Hồ sơ, tranh đã lưu, các cuộc trò chuyện và câu hỏi ở Hỏi Aura được cất trong bộ nhớ của trình duyệt "
     "(hoặc của ứng dụng) trên chính thiết bị này, để lần sau bạn mở lại vẫn tiếp tục được."),
    ("Câu hỏi gửi tới AI",
     "Khi bạn gõ câu hỏi hay câu trả lời, nội dung đó được gửi qua máy chủ của AURA tới một dịch vụ AI bên "
     "thứ ba (hiện là Groq, Google Gemini, OpenRouter hoặc OpenAI, tuỳ dịch vụ nào đang sẵn sàng) để soạn câu "
     "trả lời. Máy chủ của AURA không ghi lại nội dung bạn gõ vào nhật ký. Vì vậy, đừng gõ thông tin cá nhân "
     "nhạy cảm vào ô trò chuyện."),
    ("Ảnh chụp ở Scan",
     "Camera chỉ bật khi khung quét đang mở và tắt ngay khi bạn chụp xong hoặc đóng khung. Ảnh vừa chụp (hay "
     "chọn) được thu nhỏ ngay trên máy bạn rồi gửi lên máy chủ của AURA để nhận diện bức tranh. Ảnh chỉ nằm "
     "tạm trên máy chủ trong lúc nhận diện rồi bị xoá ngay; AURA không lưu lại ảnh, không hiện lại ảnh, và "
     "không gửi ảnh cho dịch vụ AI hay bên thứ ba nào."),
    ("Xoá dữ liệu",
     "Nút Bắt đầu lại trong mỗi cuộc trò chuyện xoá cuộc trò chuyện đó. Đăng xuất xoá hồ sơ, tranh đã lưu và "
     "mọi cuộc trò chuyện trên thiết bị này. Bạn cũng có thể xoá dữ liệu trang web trong cài đặt trình duyệt."),
    ("Thay đổi",
     "AURA là dự án học tập; chính sách này có thể được cập nhật khi ứng dụng thêm tính năng. Mọi thay đổi "
     "sẽ được ghi tại đây."),
]


def _row(ic: str, title: str, *, sub: str = "", value: str = "", on_click=None, color: str = INK) -> ft.Control:
    right: ft.Control = T(value, 12, 400, MUTED) if value else icon("chevron-right", 18, MUTED)
    return ft.Container(ft.Row([
        ft.Container(icon(ic, 18, PRIMARY if color == INK else color), width=34, height=34, border_radius=17,
                     bgcolor=TINT, alignment=ft.Alignment.CENTER),
        H(12),
        ft.Column([T(title, 14, 500, color), *([V(2), T(sub, 11, 400, MUTED, max_lines=1)] if sub else [])],
                  spacing=0, tight=True, expand=True),
        right,
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(vertical=12), on_click=on_click)


def _group(rows: list[ft.Control]) -> ft.Control:
    items: list[ft.Control] = []
    for k, r in enumerate(rows):
        if k:
            items.append(divider())
        items.append(r)
    return card(ft.Column(items, spacing=0, tight=True), padding=ft.Padding.symmetric(horizontal=14))


def confirm_logout(app) -> None:
    page = app.page
    page.show_dialog(ft.AlertDialog(
        bgcolor=BG,
        title=T("Đăng xuất khỏi AURA?", 21, serif=True),
        content=T("Hồ sơ, tranh đã lưu và các cuộc trò chuyện trên thiết bị này sẽ được xoá.", 13, 400, MUTED),
        actions=[
            ft.TextButton(content=T("Huỷ", 13, 600, MUTED), on_click=lambda e: page.pop_dialog()),
            ft.TextButton(content=T("Đăng xuất", 13, 600, RED),
                          on_click=lambda e: (page.pop_dialog(), app.sign_out())),
        ]))


def build(app, q) -> ft.View:
    prof = app.profile
    guest = prof.provider == "guest"
    n_saved = len(app.state.saved)

    def replay_tour(e=None):
        from .onboarding import show
        show(app)

    account = card(ft.Row([
        avatar(prof, 56),
        H(14),
        ft.Column([
            T(prof.name or "Bạn", 20, serif=True, max_lines=1),
            V(3),
            T(prof.email or prof.phone or ("Đang dùng chế độ khách" if guest else "Chưa có email"),
              12, 400, MUTED, max_lines=1),
        ], spacing=0, tight=True, expand=True),
        icon("chevron-right", 18, MUTED),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.all(16), on_click=lambda e: app.go("/profile"))

    content = body([
        V(20),
        kicker("Cài đặt", ls=1.2),
        V(8),
        T("Tài khoản & ứng dụng", 29, serif=True),
        V(20),
        account,
        *([V(12), primary_button("Đăng nhập với Google", lambda e: app.social_login("google"), pill=True,
                                 height=44)] if guest else []),
        V(26),
        kicker("Tài khoản", 9, 1.1),
        V(8),
        _group([
            _row("user", "Thông tin tài khoản", sub="Tên, email, tài khoản liên kết",
                 on_click=lambda e: app.go("/profile")),
            _row("bookmark", "Đã lưu", sub=f"{n_saved} tác phẩm" if n_saved else "Chưa lưu tác phẩm nào",
                 on_click=lambda e: app.go("/saved")),
        ]),
        V(26),
        kicker("Về AURA", 9, 1.1),
        V(8),
        _group([
            _row("info", "Giới thiệu", sub="AURA, phương pháp Socrates, nguồn tư liệu",
                 on_click=lambda e: app.go("/about")),
            _row("shield-check", "Chính sách quyền riêng tư", sub="Dữ liệu nào được lưu, lưu ở đâu",
                 on_click=lambda e: app.go("/privacy")),
            _row("circle-help", "Xem lại hướng dẫn", sub="4 bước làm quen với AURA", on_click=replay_tour),
            _row("award", "Phiên bản", value=APP_VERSION),
        ]),
        V(26),
        ft.Container(ft.Row([icon("log-out", 18, RED), H(8), T("Đăng xuất", 14, 600, RED)], spacing=0,
                            tight=True, alignment=ft.MainAxisAlignment.CENTER),
                     height=50, border=ft.Border.all(1, RED), border_radius=RADIUS,
                     alignment=ft.Alignment.CENTER, on_click=lambda e: confirm_logout(app)),
        V(12),
        T("AURA · Nhìn chậm, hỏi nhiều hơn.", 11, 400, MUTED, align=ft.TextAlign.CENTER),
    ], bottom=28)
    return screen("/settings", content, top=top_bar("Cài đặt", on_back=app.back_handler),
                  nav=nav_bar(app, NAV_SETTINGS))


def _doc(app, route: str, bar: str, kick: str, title: str, sections: list[tuple[str, str]], note: str) -> ft.View:
    items: list[ft.Control] = [V(20), kicker(kick, ls=1.2), V(8), T(title, 27, serif=True), V(8),
                               T(note, 12, 400, MUTED)]
    for head, text in sections:
        items += [V(24), T(head, 18, serif=True), V(8), T(text, 14, 400, INK)]
    items += [V(28), ft.Container(height=1, bgcolor=BORDER), V(14),
              T(f"AURA phiên bản {APP_VERSION}", 11, 400, MUTED, align=ft.TextAlign.CENTER)]
    return screen(route, body(items, bottom=28), top=top_bar(bar, on_back=app.back_handler),
                  nav=nav_bar(app, NAV_SETTINGS))


def about(app, q) -> ft.View:
    return _doc(app, "/about", "Giới thiệu", "Giới thiệu", "Nhìn chậm, hỏi nhiều hơn.", ABOUT,
                "Ứng dụng giúp bạn cảm nhận tranh Phục Hưng qua đối thoại.")


def privacy(app, q) -> ft.View:
    return _doc(app, "/privacy", "Quyền riêng tư", "Chính sách quyền riêng tư", "Dữ liệu của bạn trong AURA",
                PRIVACY, "Viết bằng lời dễ hiểu: AURA lưu gì, lưu ở đâu, gửi đi đâu.")
