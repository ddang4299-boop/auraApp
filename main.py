"""Điểm khởi chạy ứng dụng AURA.

Chạy trên máy tính (cửa sổ dạng điện thoại):   flet run main.py
Chạy trên điện thoại thật (app Flet):           flet run --android  /  flet run --ios
Đóng gói:                                        flet build apk  /  flet build ipa  /  flet build web
"""
import os

import flet as ft

from aura.app import AuraApp
from Chatbot.aura_adapter import AuraChatbotEngine


def main(page: ft.Page):
    if page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX) \
            and not page.web:
        # đặt kích thước cửa sổ khi chạy
        page.window.width = 402 + 16
        page.window.height = 874
    # Tranh có kịch bản trong Chatbot/scripts/ chạy bằng chatbot của nhóm,
    # tranh khác dùng kịch bản mẫu trong aura/socratic.py.
    AuraApp(page, engine=AuraChatbotEngine())


if __name__ == "__main__":
    # Máy chủ (Render...) cấp cổng qua biến PORT; chạy thử web trên máy thì đặt AURA_WEB_PORT.
    port = os.environ.get("AURA_WEB_PORT") or os.environ.get("PORT")
    if port:   # chế độ web: giao diện mở bằng trình duyệt, Python (và key AI) ở lại máy chủ
        os.environ.setdefault("FLET_FORCE_WEB_SERVER", "true")
        host = "0.0.0.0" if os.environ.get("PORT") else None   # máy chủ: nhận kết nối từ ngoài
        ft.run(main, view=None, host=host, port=int(port), assets_dir="assets")
    else:
        ft.run(main, assets_dir="assets")
