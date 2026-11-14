"""Điểm khởi chạy ứng dụng AURA.

Chạy trên máy tính (cửa sổ dạng điện thoại):   flet run main.py
Chạy trên điện thoại thật (app Flet):           flet run --android  /  flet run --ios
Đóng gói:                                        flet build apk  /  flet build ipa  /  flet build web
"""
import os
import secrets
import sys
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


def _tune_memory() -> None:
    """Máy chủ Linux (Render, 512 MB RAM): bớt RAM "phình" của bộ cấp phát bộ nhớ glibc.

    - glibc tạo một vùng nhớ riêng ("arena") cho mỗi luồng hay giành nhau cấp phát; máy chủ có nhiều luồng
      (gọi AI, Scan...) nên RAM phình dần dù dữ liệu thật không nhiều. Giới hạn còn 2 arena.
    - Phần RAM đã giải phóng (phiên hết hạn, ảnh Scan...) không tự trả về hệ điều hành: 5 phút trả một lần."""
    if not sys.platform.startswith("linux"):
        return
    try:
        import ctypes
        import threading
        import time
        libc = ctypes.CDLL("libc.so.6")
        libc.mallopt(-8, 2)                    # M_ARENA_MAX = 2

        def trim_forever():
            while True:
                time.sleep(300)
                libc.malloc_trim(0)

        threading.Thread(target=trim_forever, name="aura-malloc-trim", daemon=True).start()
    except Exception as e:                     # không phải glibc (vd Alpine): bỏ qua
        print(f"[mem] bỏ qua tinh chỉnh bộ nhớ: {e}")


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
        # Người dùng đóng tab: Flet giữ phiên (cả cây giao diện) thêm 1 giờ mặc định rồi mới xoá. Rút
        # còn 15 phút cho đỡ RAM; quay lại sau đó thì hồ sơ, tranh đã lưu, các cuộc trò chuyện vẫn được
        # đọc lại từ bộ nhớ trình duyệt.
        os.environ.setdefault("FLET_SESSION_TIMEOUT", "900")
        _tune_memory()
        ft.run(main, view=None, host=host, port=int(port), assets_dir="assets", upload_dir=upload_dir)
    else:
        ft.run(main, assets_dir="assets")
