"""Màn Scan ảnh tác phẩm (nút tròn giữa thanh điều hướng, /scan).

Luồng: hướng dẫn chụp (chữ to, dễ đọc) -> người dùng chụp/chọn ảnh -> ảnh được gửi lên máy chủ ->
aura/vision.py nhận diện bằng cách "nhớ điểm" -> một trong ba kết quả:
- Chắc chắn: thẻ tranh + nút Xem tranh / Trò chuyện về tranh (+ "Xem kỹ chi tiết này" nếu chụp sát
  một chi tiết).
- Chưa chắc: "Có phải bức này không?" đặt ảnh của bạn cạnh tranh gốc để tự so; Đúng / Không phải.
- Không nhận ra: nói rõ lý do (ảnh mờ/rung, có thể tranh chưa có trong Kho...) + Chụp lại / Tìm trong
  Kho tranh / Tả bằng lời ở Hỏi Aura. Không bao giờ đoán bừa.
"""
from __future__ import annotations

import asyncio

import flet as ft

from .. import vision
from ..app import SCAN_MAX_BYTES
from ..data import ALL_PAINTINGS, PAINTINGS
from ..theme import INK, MUTED, PRIMARY, SHADOW_INK, TINT, WHITE
from ..ui import (H, NAV_SCAN, T, V, body, glass, icon, kicker, logo, nav_bar, outline_button, primary_button,
                  screen, text_link, top_bar)

TIPS = [
    ("crop", "Không cần chụp đủ cả bức. Một phần thật rõ là đủ."),
    ("smartphone", "Giữ máy thật chắc: tựa khuỷu tay vào người khi chụp."),
    ("focus", "Chạm vào bức tranh trên màn hình để máy lấy nét, rồi mới chụp."),
    ("zap-off", "Tắt đèn flash để mặt kính không bị lóa."),
]
NONE_MSG = {
    "blurry": "Ảnh hơi mờ hoặc bị rung nên AURA chưa thấy rõ các chi tiết. Bạn giữ máy thật chắc, chạm vào "
              "bức tranh để lấy nét rồi chụp lại nhé.",
    "declined": "Cảm ơn bạn đã báo. Bạn thử chụp gần hơn vào một phần rõ nét của bức tranh, hoặc tìm bức "
                "tranh trong Kho tranh.",
    "none": "Có thể bức tranh này chưa có trong Kho tranh AURA, hoặc ảnh chưa đủ rõ. Bạn thử chụp gần hơn, "
            "đủ sáng và giữ máy thật chắc nhé.",
    "bad_image": "AURA không đọc được tệp ảnh này. Bạn thử chụp lại, hoặc chọn ảnh dạng JPG hay PNG.",
    "too_big": "Ảnh lớn quá (trên 25 MB). Bạn chọn ảnh khác hoặc chụp lại nhé.",
    "upload": "Gửi ảnh chưa thành công, có thể do mạng chập chờn. Bạn thử lại nhé.",
    "unavailable": "Bộ nhận diện ảnh chưa sẵn sàng trên máy chủ này.",
}
NONE_TITLE = {"bad_image": "Không đọc được ảnh", "too_big": "Ảnh lớn quá", "upload": "Chưa gửi được ảnh",
              "unavailable": "Scan chưa sẵn sàng"}


def _round_icon(name: str, size: float = 40, color: str = PRIMARY, bg: str = TINT) -> ft.Container:
    return ft.Container(icon(name, size * 0.5, color), width=size, height=size, border_radius=size / 2,
                        bgcolor=bg, alignment=ft.Alignment.CENTER)


def _framed(img: ft.Control) -> ft.Container:
    return ft.Container(img, border=ft.Border.all(2, "#6B4F3A"), bgcolor=WHITE, padding=2,
                        shadow=[ft.BoxShadow(blur_radius=8, offset=ft.Offset(0, 3), color=f"{SHADOW_INK},0.2")])


def _painting_thumb(p, h: float) -> ft.Container:
    return _framed(ft.Image(src=p.image, width=round(h * p.aspect), height=h, fit=ft.BoxFit.COVER))


def _photo_thumb(res, h: float) -> ft.Control | None:
    if not getattr(res, "thumb", None):
        return None
    return ft.Container(ft.Image(src=res.thumb, width=round(h * res.thumb_aspect), height=h, fit=ft.BoxFit.COVER),
                        border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        border=ft.Border.all(1, "#D9CBB8"))


def _labeled(control: ft.Control, label: str) -> ft.Column:
    return ft.Column([control, V(6), T(label, 10, 500, MUTED)], spacing=0, tight=True,
                     horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def _compare(res, p, h: float = 112) -> ft.Control:
    """Ảnh người dùng chụp đặt cạnh tranh gốc (để tự so khi AURA chưa chắc)."""
    mine = _photo_thumb(res, h)
    items: list[ft.Control] = []
    if mine is not None:
        items += [_labeled(mine, "Ảnh của bạn"), H(10),
                  ft.Container(icon("arrow-up-right", 18, MUTED), rotate=ft.Rotate(0.785)), H(10)]
    items.append(_labeled(_painting_thumb(p, h), "Trong Kho tranh"))
    return ft.Row(items, spacing=0, alignment=ft.MainAxisAlignment.CENTER,
                  vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _tip_rows(size: float = 15) -> list[ft.Control]:
    out: list[ft.Control] = []
    for k, (ic, text) in enumerate(TIPS):
        if k:
            out.append(V(12))
        out.append(ft.Row([_round_icon(ic, 40), H(14), T(text, size, 400, INK, expand=True, lh=1.35)],
                          spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    return out


def build(app, q) -> ft.View:
    st = app.state.scan
    holder = ft.Container()
    scroller = ft.Ref[ft.Column]()
    ok_engine = vision.available()

    # ---- các khối giao diện theo trạng thái ----------------------------------------------------------
    def intro() -> ft.Control:
        n = len(ALL_PAINTINGS)
        return ft.Column([
            V(12),
            glass(ft.Column([
                _round_icon("scan-camera", 56),
                V(14),
                kicker("Scan tác phẩm", 10, 1.2),
                V(8),
                T("Chụp một bức tranh, AURA nhận ra ngay", 24, serif=True, lh=1.2),
                V(10),
                T(f"Hướng máy về phía bức tranh và chụp. AURA nhận ra {n} bức trong Kho tranh và đưa bạn tới "
                  "đúng trang của bức đó.", 15, 400, INK, lh=1.4),
            ], spacing=0, tight=True), radius=18, padding=ft.Padding.only(left=18, right=18, top=18, bottom=20)),
            V(18),
            shoot_button("Chụp hoặc chọn ảnh"),
            V(8),
            T("Trên điện thoại, chọn “Chụp ảnh” để mở camera.", 12, 400, MUTED, align=ft.TextAlign.CENTER),
            V(24),
            kicker("Mẹo chụp ảnh", 10, 1.2),
            V(12),
            *_tip_rows(),
            V(20),
            privacy_line(),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def privacy_line() -> ft.Control:
        return ft.Row([icon("shield-check", 16, MUTED), H(8),
                       T("Ảnh chỉ dùng để nhận diện và được xoá ngay sau đó, không gửi cho bên nào khác.",
                         12, 400, MUTED, expand=True)], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

    def shoot_button(text: str) -> ft.Control:
        return primary_button(text, lambda e: app.page.run_task(start_scan), leading="camera", pill=True,
                              height=56, size=16)

    label = T("ĐANG GỬI ẢNH", 10, 600, PRIMARY, ls=1.0)

    def working() -> ft.Control:
        return ft.Column([
            V(12),
            glass(ft.Column([
                ft.Row([logo(14), H(10), label], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                V(12),
                ft.ProgressBar(bar_height=3, color=PRIMARY, bgcolor=TINT, border_radius=2),
                V(12),
                T("Thường chỉ mất vài giây. Ảnh lớn hoặc mạng chậm thì lâu hơn một chút.", 13, 400, MUTED),
            ], spacing=0, tight=True), radius=16, padding=ft.Padding.only(left=16, right=16, top=16, bottom=16)),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def found(res) -> ft.Control:
        p = PAINTINGS[res.painting]
        d = p.details.get(res.detail) if res.detail else None
        detail_line: list[ft.Control] = []
        buttons: list[ft.Control] = [primary_button("Xem tranh", lambda e: app.go(f"/painting/{p.id}"),
                                                    leading="image", pill=True, height=52, size=15)]
        if d is not None:
            detail_line = [V(12), ft.Container(ft.Row([
                icon("zoom-in", 16, PRIMARY), H(8),
                T(f"Phần bạn chụp: {d.title}", 13, 500, PRIMARY, expand=True)], spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=TINT, border_radius=12, padding=ft.Padding.symmetric(horizontal=12, vertical=9))]
            buttons += [V(10), outline_button("Xem kỹ chi tiết này",
                                              lambda e: app.go(f"/detail/{p.id}/{d.key}"), height=50)]
        buttons += [V(10), outline_button("Trò chuyện về tranh", lambda e: app.go(f"/chat/{p.id}"), height=50)]
        return ft.Column([
            V(12),
            glass(ft.Column([
                ft.Row([_round_icon("check", 28, WHITE, PRIMARY), H(10), kicker("Đã nhận ra", 10, 1.2)],
                       spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                V(16),
                _compare(res, p),
                V(16),
                T(p.title, 24, serif=True, align=ft.TextAlign.CENTER, lh=1.2),
                V(6),
                T(f"{p.artist} · {p.year}", 13, 400, MUTED, align=ft.TextAlign.CENTER),
                *detail_line,
                V(18),
                *buttons,
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), radius=18,
                padding=ft.Padding.only(left=16, right=16, top=16, bottom=18)),
            V(16),
            again_link(),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def maybe(res) -> ft.Control:
        p = PAINTINGS[res.painting]

        def no(e):
            st.declined = True
            refresh()

        return ft.Column([
            V(12),
            glass(ft.Column([
                kicker("Có phải bức này không?", 10, 1.2),
                V(8),
                T("Ảnh chưa đủ rõ để AURA chắc chắn. Bạn so thử hai ảnh nhé.", 15, 400, INK, lh=1.4),
                V(16),
                _compare(res, p),
                V(14),
                T(p.title, 22, serif=True, align=ft.TextAlign.CENTER, lh=1.2),
                V(4),
                T(f"{p.artist} · {p.year}", 13, 400, MUTED, align=ft.TextAlign.CENTER),
                V(18),
                primary_button("Đúng rồi, mở tranh", lambda e: app.go(f"/painting/{p.id}"), leading="check",
                               pill=True, height=52, size=15),
                V(10),
                outline_button("Không phải", no, height=50),
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), radius=18,
                padding=ft.Padding.only(left=16, right=16, top=16, bottom=18)),
            V(16),
            again_link(),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def not_found(reason: str, res=None) -> ft.Control:
        mine = _photo_thumb(res, 96) if res is not None else None
        return ft.Column([
            V(12),
            glass(ft.Column([
                ft.Row([_round_icon("info", 40), H(12),
                        T(NONE_TITLE.get(reason, "Chưa nhận ra bức tranh"), 21, serif=True, expand=True)],
                       spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                V(12),
                T(NONE_MSG.get(reason, NONE_MSG["none"]), 15, 400, INK, lh=1.4),
                *([V(14), ft.Row([_labeled(mine, "Ảnh của bạn")], alignment=ft.MainAxisAlignment.CENTER)]
                  if mine is not None else []),
                V(18),
                *([shoot_button("Chụp lại"), V(10)] if reason != "unavailable" else []),
                outline_button("Tìm trong Kho tranh", lambda e: app.go("/gallery"), height=50),
                V(10),
                outline_button("Tả bằng lời ở Hỏi Aura", lambda e: app.go("/ask"), height=50),
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), radius=18,
                padding=ft.Padding.only(left=16, right=16, top=16, bottom=18)),
            *([V(22), kicker("Mẹo chụp ảnh", 10, 1.2), V(12), *_tip_rows()]
              if reason in ("blurry", "none", "declined") else []),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def again_link() -> ft.Control:
        return text_link("Chụp bức khác", lambda e: app.page.run_task(start_scan), size=14, color=PRIMARY)

    def render() -> ft.Control:
        if not ok_engine:
            return not_found("unavailable")
        if st.phase == "working":
            return working()
        if st.phase == "result":
            res = st.result
            if st.error:
                return not_found(st.error, res)
            if res is None:
                return intro()
            if res.status == "sure" and res.painting in PAINTINGS:
                return found(res)
            if res.status == "ask" and res.painting in PAINTINGS and not st.declined:
                return maybe(res)
            if st.declined:
                return not_found("declined", res)
            if res.status in ("bad_image", "unavailable"):
                return not_found(res.status, res)
            return not_found("blurry" if res.blurry else "none", res)
        return intro()

    def refresh() -> None:
        holder.content = render()
        try:
            app.page.update()
        except Exception:                      # màn đã đóng
            return
        app.page.run_task(to_top)

    async def to_top() -> None:
        try:
            await scroller.current.scroll_to(offset=0, duration=250)
        except Exception:
            pass

    # ---- chụp / chọn ảnh rồi nhận diện ---------------------------------------------------------------
    async def start_scan() -> None:
        if st.phase == "working" or not ok_engine:
            return
        try:
            f = await app.pick_photo()
        except Exception as ex:
            print(f"[scan] không mở được hộp chọn ảnh: {ex}")
            f = None
        if f is None:                          # người dùng huỷ
            return
        st.declined = False
        if f.size and f.size > SCAN_MAX_BYTES:
            st.phase, st.result, st.error = "result", None, "too_big"
            refresh()
            return
        st.phase, st.error = "working", None
        label.value = "ĐANG GỬI ẢNH"
        refresh()
        try:
            data = await app.receive_photo(f)
        except Exception as ex:
            print(f"[scan] gửi ảnh lỗi: {ex}")
            st.phase, st.result, st.error = "result", None, "upload"
            refresh()
            return
        label.value = "ĐANG NHẬN DIỆN BỨC TRANH"
        try:
            label.update()
        except Exception:
            pass
        try:
            res = await asyncio.to_thread(vision.recognizer().recognize, data)
        except Exception as ex:                # lỗi bất ngờ: báo như ảnh không đọc được
            print(f"[scan] nhận diện lỗi: {ex}")
            res = vision.ScanResult("bad_image")
        del data
        st.phase, st.result = "result", res
        refresh()

    async def warm() -> None:
        """Mở màn là tính sẵn điểm của các bức tranh gốc (chỉ lần đầu), để lúc chụp xong khỏi chờ."""
        rec = vision.recognizer()
        if not rec.ready:
            try:
                await asyncio.to_thread(rec.warm)
            except Exception as ex:
                print(f"[scan] chuẩn bị lỗi: {ex}")

    holder.content = render()
    if ok_engine:
        app.page.run_task(warm)
    content = body([holder], ref=scroller)
    return screen("/scan", content, top=top_bar("Scan tác phẩm", on_back=app.back_handler),
                  nav=nav_bar(app, NAV_SCAN))
