"""Điểm khởi chạy ứng dụng AURA.

Chạy trên máy tính (cửa sổ dạng điện thoại):   flet run main.py
Chạy trên điện thoại thật (app Flet):           flet run --android  /  flet run --ios
Đóng gói:                                        flet build apk  /  flet build ipa  /  flet build web
"""
import os
import secrets
import tempfile

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


def _skip_send_log() -> None:
    """Bản web: bỏ một dòng log tốn CPU của Flet 1.0.5.

    Mỗi lần gửi giao diện xuống trình duyệt, Flet chạy `transport_log.debug(f"... {message}")`:
    chuỗi f-string được dựng (đổi CẢ cây giao diện thành chữ) kể cả khi log đang tắt, tốn
    khoảng 12% CPU mỗi lần chuyển màn. Máy chủ miễn phí chỉ có 0,1 CPU nên phần này đáng kể.
    Thay bằng bản giống hệt nhưng không có dòng log; chỉ áp dụng đúng phiên bản đã kiểm tra."""
    import logging

    import msgpack
    from flet.controls.base_control import BaseControl
    from flet.messaging.protocol import configure_encode_object_for_msgpack
    from flet_web.fastapi.flet_app import FletApp

    if ft.__version__ != "1.0.5" or logging.getLogger("flet_transport").isEnabledFor(logging.DEBUG):
        return
    encode = configure_encode_object_for_msgpack(BaseControl)

    def send_message(self, message):
        body = msgpack.packb([message.action, message.body], default=encode)
        self._FletApp__send_queue.put_nowait(b"\x00" + body)

    FletApp.send_message = send_message


if __name__ == "__main__":
    # Máy chủ (Render...) cấp cổng qua biến PORT; chạy thử web trên máy thì đặt AURA_WEB_PORT.
    port = os.environ.get("AURA_WEB_PORT") or os.environ.get("PORT")
    if port:   # chế độ web: giao diện mở bằng trình duyệt, Python (và key AI) ở lại máy chủ
        os.environ.setdefault("FLET_FORCE_WEB_SERVER", "true")
        _skip_send_log()
        host = "0.0.0.0" if os.environ.get("PORT") else None   # máy chủ: nhận kết nối từ ngoài
        # Scan ảnh: trình duyệt gửi ảnh lên máy chủ qua đường dẫn có chữ ký. Khoá ký được tạo ngẫu nhiên
        # mỗi lần chạy (không lưu ở đâu cả); ảnh nằm tạm trong thư mục tạm, nhận diện xong xoá ngay.
        upload_dir = os.path.join(tempfile.gettempdir(), "aura_uploads")
        os.environ.setdefault("FLET_SECRET_KEY", secrets.token_urlsafe(32))
        os.environ.setdefault("FLET_MAX_UPLOAD_SIZE", str(25 * 1024 * 1024))
        os.environ["AURA_UPLOAD_DIR"] = upload_dir
        ft.run(main, view=None, host=host, port=int(port), assets_dir="assets", upload_dir=upload_dir)
    else:
        ft.run(main, assets_dir="assets")
