"""Điểm khởi chạy ứng dụng AURA.

Chạy trên máy tính (cửa sổ dạng điện thoại):   flet run main.py
Chạy trên điện thoại thật (app Flet):           flet run --android  /  flet run --ios
Đóng gói:                                        flet build apk  /  flet build ipa
"""
import os

import flet as ft

from aura.app import AuraApp


def main(page: ft.Page):  
    if page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX) \
            and not page.web:
        # đặt kích thước cửa sổ khi chạy
        page.window.width = 402 + 16
        page.window.height = 874
    AuraApp(page)


if __name__ == "__main__":
    port = os.environ.get("AURA_WEB_PORT")
    if port:   # chế độ wen
        ft.run(main, view=None, port=int(port), assets_dir="assets")
    else:
        ft.run(main, assets_dir="assets")
