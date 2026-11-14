"""Scan tác phẩm: nhận ảnh người dùng chụp / chọn, nhận diện, và màn /scan (chờ + kết quả).

Luồng (gọn như quét mã QR ở app ngân hàng):
1. Bấm nút Scan giữa thanh điều hướng: khung quét hiện NGAY, camera chạy trực tiếp, có khung ngắm, nút chụp
   và nút Thư viện ảnh (bản web: assets/aura-scan.js; app trên máy: hộp chọn ảnh của hệ điều hành).
   Đóng khung quét thì ở nguyên màn đang xem, không có gì thay đổi.
2. Chụp / chọn xong: on_photo mở màn này ở trạng thái chờ. Màn chờ cho người dùng thấy việc đang tới đâu
   (3 bước có dấu tích), một vệt sáng lướt qua các bức trong Kho tranh, và thẻ "Bạn có biết?" tự đổi để có
   cái đọc trong lúc chờ. Chờ lâu thì nói rõ lý do; lúc nào cũng có nút Huỷ.
3. Kết quả chỉ hiện bức tranh tìm được (không hiện lại ảnh người dùng chụp):
   - Chắc chắn: tranh + Xem tranh / Trò chuyện về tranh (+ "Xem kỹ chi tiết này" nếu chụp sát một chi tiết).
   - Chưa chắc: "Có phải bức này không?" + Đúng rồi / Không phải.
   - Không nhận ra: nói rõ lý do (ảnh mờ/rung, có thể tranh chưa có trong Kho...) + Quét lại / Tìm trong
     Kho tranh / Tả bằng lời ở Hỏi Aura. Không bao giờ đoán bừa.
"""
from __future__ import annotations

import asyncio
import time

import flet as ft

from .. import vision
from ..app import SCAN_MAX_BYTES
from ..data import ALL_PAINTINGS, PAINTINGS
from ..theme import BORDER, GOLD, INK, MUTED, PRIMARY, SHADOW_INK, TINT, WHITE
from ..topics import FACTS
from ..ui import (H, NAV_SCAN, T, V, body, compact, glass, icon, kicker, nav_bar, outline_button,
                  primary_button, screen, text_link, top_bar)

TIPS = [
    ("crop", "Không cần chụp đủ cả bức. Một phần thật rõ là đủ."),
    ("smartphone", "Giữ máy thật chắc: tựa khuỷu tay vào người khi bấm chụp."),
    ("zap-off", "Tắt đèn flash để mặt kính không bị lóa."),
]
NONE_MSG = {
    "blurry": "Ảnh hơi mờ hoặc bị rung nên AURA chưa thấy rõ các chi tiết. Bạn giữ máy thật chắc rồi quét lại nhé.",
    "declined": "Cảm ơn bạn đã báo. Bạn thử quét gần hơn vào một phần rõ nét của bức tranh, hoặc tìm bức "
                "tranh trong Kho tranh.",
    "none": "Có thể bức tranh này chưa có trong Kho tranh AURA, hoặc ảnh chưa đủ rõ. Bạn thử quét gần hơn, "
            "đủ sáng và giữ máy thật chắc nhé.",
    "bad_image": "AURA không đọc được tệp ảnh này. Bạn thử chụp lại, hoặc chọn ảnh dạng JPG hay PNG.",
    "too_big": "Ảnh lớn quá (trên 25 MB). Bạn chọn ảnh khác hoặc chụp lại nhé.",
    "upload": "Gửi ảnh chưa thành công, có thể do mạng chập chờn. Bạn thử lại nhé.",
    "unavailable": "Bộ nhận diện ảnh chưa sẵn sàng trên máy chủ này.",
}
NONE_TITLE = {"bad_image": "Không đọc được ảnh", "too_big": "Ảnh lớn quá", "upload": "Chưa gửi được ảnh",
              "unavailable": "Scan chưa sẵn sàng"}

# Màn chờ
STEPS = ["Nhận ảnh", "Tìm nét đặc trưng", f"So với Kho tranh ({len(ALL_PAINTINGS)} bức)"]
FEATURE_STEP_S = 0.8          # nhận diện được ngần này giây thì chuyển dấu sang bước "So với Kho tranh"
FACT_EVERY = 6.0              # đổi thẻ "Bạn có biết?" sau ngần này giây
SLOW_S, VERY_SLOW_S = 7.0, 20.0
MIN_WAIT = 0.9                # màn chờ hiện ít nhất ngần này (không chớp lên rồi tắt ngay)
WALL_BG = "#F1EADC"           # nền "bức tường" treo tranh


def _round_icon(name: str, size: float = 40, color: str = PRIMARY, bg: str = TINT) -> ft.Container:
    return ft.Container(icon(name, size * 0.5, color), width=size, height=size, border_radius=size / 2,
                        bgcolor=bg, alignment=ft.Alignment.CENTER)


def _framed(img: ft.Control, *, border: float = 2) -> ft.Container:
    return ft.Container(img, border=ft.Border.all(border, "#6B4F3A"), bgcolor=WHITE, padding=border,
                        shadow=[ft.BoxShadow(blur_radius=8, offset=ft.Offset(0, 3), color=f"{SHADOW_INK},0.2")])


def _painting_thumb(p, h: float, *, border: float = 2) -> ft.Container:
    return _framed(ft.Image(src=p.image, width=round(h * p.aspect), height=round(h), fit=ft.BoxFit.COVER),
                   border=border)


def _tip_rows(size: float = 15) -> list[ft.Control]:
    out: list[ft.Control] = []
    for k, (ic, text) in enumerate(TIPS):
        if k:
            out.append(V(12))
        out.append(ft.Row([_round_icon(ic, 40), H(14), T(text, size, 400, INK, expand=True, lh=1.35)],
                          spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    return out


def _corners(*, arm: float = 22, th: float = 3, color: str = GOLD) -> list[ft.Control]:
    """Bốn góc khung ngắm (mỗi góc là hai vạch), đặt vào một Stack có sẵn kích thước."""
    out: list[ft.Control] = []
    for left in (True, False):
        for top in (True, False):
            pos = {"left" if left else "right": 0, "top" if top else "bottom": 0}
            out.append(ft.Container(width=arm, height=th, bgcolor=color, border_radius=2, **pos))
            out.append(ft.Container(width=th, height=arm, bgcolor=color, border_radius=2, **pos))
    return out


# ---- nhận ảnh, nhận diện ---------------------------------------------------------------------------
async def warm() -> None:
    """Người dùng vừa mở khung quét: nạp sẵn OpenCV + điểm của tranh gốc trong luồng phụ."""
    if not vision.available() or vision.recognizer().ready:
        return
    try:
        await asyncio.to_thread(vision.preload)
    except Exception as ex:
        print(f"[scan] chuẩn bị lỗi: {ex}")


async def on_photo(app, f) -> None:
    """FilePicker.on_result. f = ảnh vừa chụp/chọn; None = người dùng đóng khung quét (không làm gì cả)."""
    st = app.state.scan
    if f is None:
        return
    st.job += 1
    job = st.job
    st.declined, st.result, st.error = False, None, None
    if not vision.available():
        st.phase, st.error = "result", "unavailable"
        _show(app, navigate=True)
        return
    if f.size and f.size > SCAN_MAX_BYTES:
        st.phase, st.error = "result", "too_big"
        _show(app, navigate=True)
        return
    st.phase, st.step, st.started = "working", 0, time.monotonic()
    _show(app, navigate=True)            # màn chờ hiện TRƯỚC khi ảnh được gửi (khung quét đóng lúc ảnh bắt đầu gửi)
    try:
        data = await app.receive_photo(f)
    except Exception as ex:
        if st.job == job:
            print(f"[scan] gửi ảnh lỗi: {ex}")
            st.phase, st.error = "result", "upload"
            _show(app)
        return
    if st.job != job:                    # người dùng đã huỷ / quét ảnh khác
        return
    st.step, st.step_at = 1, time.monotonic()
    _show(app, soft=True)
    try:
        res = await asyncio.to_thread(vision.recognizer().recognize, data)
    except Exception as ex:              # lỗi bất ngờ: báo như ảnh không đọc được
        print(f"[scan] nhận diện lỗi: {ex}")
        res = vision.ScanResult("bad_image")
    del data
    wait = MIN_WAIT - (time.monotonic() - st.started)
    if wait > 0:
        await asyncio.sleep(wait)
    if st.job != job:
        return
    st.phase, st.result = "result", res
    _show(app)


def _show(app, *, navigate: bool = False, soft: bool = False) -> None:
    """Vẽ lại màn /scan theo trạng thái. navigate=True: chưa mở thì mở (lúc vừa nhận ảnh); các lần sau chỉ
    cập nhật nếu người dùng còn ở màn này (đã đi chỗ khác thì không kéo họ quay lại)."""
    st = app.state.scan
    scr, views = st.screen, app.page.views
    if scr is not None and views and views[-1] is scr.view:
        scr.update_working() if soft else scr.refresh()
        return
    if not navigate:
        return
    in_stack = scr is not None and any(v is scr.view for v in views)
    app.go("/scan")
    if in_stack and views and views[-1] is scr.view:
        scr.refresh()


# ---- màn /scan ------------------------------------------------------------------------------------
class _Screen:
    def __init__(self, app):
        self.app = app
        self.st = app.state.scan
        self.ok = vision.available()
        self.holder = ft.Container()
        self.scroller = ft.Ref[ft.Column]()
        self.view: ft.View | None = None
        self._ticking = False
        # các phần của màn chờ được cập nhật tại chỗ
        self._rows: list[ft.Container] = []
        self._shown_step = -1
        self._note = T("", 12.5, 400, MUTED, lh=1.4)
        self._fact_i = int(time.time() // FACT_EVERY) % len(FACTS)
        self._fact = ft.AnimatedSwitcher(self._fact_body(), duration=450, reverse_duration=200,
                                         switch_in_curve=ft.AnimationCurve.EASE_OUT,
                                         transition=ft.AnimatedSwitcherTransition.FADE)

    # ---- dựng theo trạng thái ----
    def render(self) -> ft.Control:
        st = self.st
        if not self.ok:
            return self.not_found("unavailable")
        if st.phase == "working":
            return self.working()
        if st.phase == "result":
            res = st.result
            if st.error:
                return self.not_found(st.error)
            if res is None:
                return self.ready()
            if res.status == "sure" and res.painting in PAINTINGS:
                return self.found(res)
            if res.status == "ask" and res.painting in PAINTINGS and not st.declined:
                return self.maybe(res)
            if st.declined:
                return self.not_found("declined")
            if res.status in ("bad_image", "unavailable"):
                return self.not_found(res.status)
            return self.not_found("blurry" if res.blurry else "none")
        return self.ready()

    def refresh(self) -> None:
        content = self.render()
        compact(content)                       # bỏ control khoảng trống (xem ui.compact)
        self.holder.content = content
        try:
            self.holder.update()
        except Exception:                      # màn đã đóng
            return
        self.app.page.run_task(self._to_top)
        if self.st.phase == "working":
            self.start_ticker()

    async def _to_top(self) -> None:
        try:
            await self.scroller.current.scroll_to(offset=0, duration=250)
        except Exception:
            pass

    def cancel(self, e=None) -> None:
        """Nút quay lại / Huỷ: đang chờ thì bỏ lượt quét này (kết quả về sau bị bỏ qua) rồi quay lại."""
        if self.st.phase == "working":
            self.st.job += 1
            self.st.phase = "ready"
        self.app.back()

    def shoot_button(self, text: str, *, height: float = 54) -> ft.Control:
        # action: trình duyệt mở khung quét / hộp chọn ảnh NGAY trong cú chạm; ảnh về on_photo
        btn = primary_button(text, lambda e: self.app.page.run_task(warm), leading="camera", pill=True,
                             height=height, size=16)
        btn.action = self.app.pick_action()
        return btn

    def again_link(self) -> ft.Control:
        link = text_link("Quét bức khác", lambda e: None, size=14, color=PRIMARY)
        link.action = self.app.pick_action()
        return link

    def privacy_line(self) -> ft.Control:
        return ft.Row([icon("shield-check", 16, MUTED), H(8),
                       T("Ảnh chỉ dùng để nhận diện và được xoá ngay sau đó, không gửi cho bên nào khác.",
                         12, 400, MUTED, expand=True)], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

    @staticmethod
    def _card(controls: list[ft.Control], *, stretch: bool = True) -> ft.Container:
        return glass(ft.Column(controls, spacing=0, tight=True,
                               horizontal_alignment=ft.CrossAxisAlignment.STRETCH if stretch
                               else ft.CrossAxisAlignment.CENTER),
                     radius=18, padding=ft.Padding.only(left=16, right=16, top=16, bottom=18))

    # ---- chưa quét (mở thẳng /scan) ----
    def ready(self) -> ft.Control:
        n = len(ALL_PAINTINGS)
        w = self.app.content_width - 32
        h = 168
        fw, fh = 112, 136
        p = PAINTINGS.get("mona-lisa") or ALL_PAINTINGS[0]
        finder = ft.Container(ft.Stack([
            ft.Container(_painting_thumb(p, fh - 40, border=3), alignment=ft.Alignment.CENTER, left=0, right=0,
                         top=0, bottom=0),
            ft.Container(ft.Stack(_corners(), width=fw, height=fh), alignment=ft.Alignment.CENTER,
                         left=0, right=0, top=0, bottom=0),
        ]), width=w, height=h, bgcolor="#2A2220", border_radius=16)
        return ft.Column([
            V(12),
            self._card([
                finder,
                V(16),
                T("Quét một bức tranh", 22, serif=True, lh=1.2),
                V(8),
                T(f"Hướng camera về phía bức tranh rồi bấm chụp. AURA nhận ra {n} bức trong Kho tranh và mở "
                  "đúng trang của bức đó.", 14.5, 400, INK, lh=1.4),
                V(18),
                self.shoot_button("Mở khung quét"),
                V(8),
                T("Có sẵn nút Thư viện nếu bạn muốn chọn ảnh đã chụp.", 12, 400, MUTED,
                  align=ft.TextAlign.CENTER),
            ]),
            V(24),
            kicker("Mẹo quét tranh", 10, 1.2),
            V(12),
            *_tip_rows(),
            V(20),
            self.privacy_line(),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    # ---- đang tìm tranh ----
    def working(self) -> ft.Control:
        self._rows = [ft.Container() for _ in STEPS]
        self._shown_step = -1
        self.update_working(send=False)
        steps: list[ft.Control] = []
        for k, row in enumerate(self._rows):
            if k:
                steps.append(V(12))
            steps.append(row)
        return ft.Column([
            V(12),
            self._card([
                kicker("Đang tìm tranh", 10, 1.2),
                V(6),
                T("AURA đang xem ảnh của bạn", 22, serif=True, lh=1.2),
                V(16),
                self._wall(),
                V(18),
                *steps,
                V(16),
                self._note,
            ]),
            V(14),
            glass(ft.Column([
                ft.Row([icon("sparkles", 15, PRIMARY), H(8), kicker("Trong lúc chờ: bạn có biết?", 10, 1.0)],
                       spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                V(10),
                self._fact,
            ], spacing=0, tight=True), radius=16, padding=ft.Padding.only(left=16, right=16, top=14, bottom=16)),
            V(18),
            text_link("Huỷ", self.cancel, size=14, color=MUTED),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def _wall(self) -> ft.Control:
        """Các bức trong Kho tranh treo thành hàng, một vệt sáng lướt qua lướt lại như đang dò từng bức.
        Vệt sáng do trình duyệt tự chạy (Shimmer), máy chủ không phải gửi gì thêm."""
        ps = ALL_PAINTINGS
        gap, pad = 8, 12
        avail = self.app.content_width - 32 - 2 * pad - gap * (len(ps) - 1) - 8 * len(ps)
        h = max(34.0, min(72.0, avail / sum(p.aspect for p in ps)))
        row = ft.Row([_painting_thumb(p, h) for p in ps], spacing=gap, alignment=ft.MainAxisAlignment.CENTER,
                     vertical_alignment=ft.CrossAxisAlignment.END)
        wall = ft.Container(row, bgcolor=WALL_BG, border_radius=14, padding=pad)
        light = ft.Shimmer(ft.Container(bgcolor=WHITE, border_radius=14), base_color="#FFFFFF,0",
                           highlight_color="#FFFFFF,0.62", period=1700)
        return ft.Stack([wall, ft.Container(light, left=0, right=0, top=0, bottom=0)])

    def _visual_step(self) -> int:
        st = self.st
        if st.step == 0:
            return 0
        return 1 if time.monotonic() - st.step_at < FEATURE_STEP_S else 2

    def _step_row(self, k: int, cur: int) -> ft.Control:
        if k < cur:
            mark: ft.Control = ft.Container(icon("check", 13, WHITE), width=22, height=22, border_radius=11,
                                            bgcolor=PRIMARY, alignment=ft.Alignment.CENTER)
            text = T(STEPS[k], 14, 500, INK)
        elif k == cur:
            mark = ft.Container(ft.ProgressRing(width=16, height=16, stroke_width=2.2, color=PRIMARY, bgcolor=TINT),
                                width=22, height=22, alignment=ft.Alignment.CENTER)
            text = T(STEPS[k] + "…", 14, 600, INK)
        else:
            mark = ft.Container(width=22, height=22, border_radius=11, border=ft.Border.all(1.5, BORDER))
            text = T(STEPS[k], 14, 400, MUTED)
        return ft.Row([mark, H(12), ft.Container(text, expand=True)], spacing=0,
                      vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def update_working(self, send: bool = True) -> None:
        """Cập nhật dấu các bước + dòng trấn an theo thời gian chờ (chỉ gửi phần đổi)."""
        if self.st.phase != "working" or not self._rows:
            return
        changed: list[ft.Control] = []
        cur = self._visual_step()
        if cur != self._shown_step:
            self._shown_step = cur
            for k, row in enumerate(self._rows):
                row.content = self._step_row(k, cur)
            changed += self._rows
        waited = time.monotonic() - self.st.started
        if waited < SLOW_S:
            note = "Thường chỉ mất vài giây."
        elif waited < VERY_SLOW_S:
            note = ("Mạng hơi chậm nên ảnh gửi lâu hơn một chút, bạn chờ thêm nhé." if self.st.step == 0 else
                    "Máy chủ miễn phí đôi khi hơi chậm. AURA vẫn đang so từng nét, bạn chờ thêm chút nhé.")
        else:
            note = "Lâu hơn thường lệ. Bạn có thể chờ tiếp, hoặc bấm Huỷ rồi quét lại."
        if self._note.value != note:
            self._note.value = note
            changed.append(self._note)
        if send:
            for c in changed:
                try:
                    c.update()
                except Exception:
                    pass

    def _fact_body(self) -> ft.Control:
        q, a, _ = FACTS[self._fact_i]
        return ft.Column([T(q, 16, 500, INK, serif=True, lh=1.3), V(4), T(a, 13.5, 400, MUTED, lh=1.45)],
                         spacing=0, tight=True)

    def start_ticker(self) -> None:
        if not self._ticking:
            self._ticking = True
            self.app.page.run_task(self._tick)

    def _on_top(self) -> bool:
        views = self.app.page.views
        return bool(views) and views[-1] is self.view

    async def _tick(self) -> None:
        """Mỗi giây: cập nhật dấu các bước / dòng trấn an; vài giây đổi thẻ "Bạn có biết?" một lần."""
        last = time.monotonic()
        try:
            while self.st.phase == "working":
                await asyncio.sleep(1.0)
                if self.st.phase != "working" or not self._on_top():
                    break
                self.update_working()
                if time.monotonic() - last >= FACT_EVERY:
                    last = time.monotonic()
                    self._fact_i = (self._fact_i + 1) % len(FACTS)
                    self._fact.content = self._fact_body()
                    try:
                        self._fact.update()
                    except Exception:
                        pass
        finally:
            self._ticking = False

    # ---- kết quả ----
    def _hero(self, p, h: float) -> ft.Control:
        img = _painting_thumb(p, h, border=3)
        img.on_click = lambda e: self.app.go(f"/painting/{p.id}")
        return ft.Row([img], alignment=ft.MainAxisAlignment.CENTER)

    def _hero_h(self, cap: float) -> float:
        return min(cap, max(150.0, self.app.content_width * 0.62))

    def found(self, res) -> ft.Control:
        p = PAINTINGS[res.painting]
        d = p.details.get(res.detail) if res.detail else None
        detail_line: list[ft.Control] = []
        buttons: list[ft.Control] = [primary_button("Xem tranh", lambda e: self.app.go(f"/painting/{p.id}"),
                                                    leading="image", pill=True, height=52, size=15)]
        if d is not None:
            detail_line = [V(14), ft.Container(ft.Row([
                icon("zoom-in", 16, PRIMARY), H(8),
                T(f"Phần bạn chụp: {d.title}", 13, 500, PRIMARY, expand=True)], spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=TINT, border_radius=12, padding=ft.Padding.symmetric(horizontal=12, vertical=9))]
            buttons += [V(10), outline_button("Xem kỹ chi tiết này",
                                              lambda e: self.app.go(f"/detail/{p.id}/{d.key}"), height=50)]
        buttons += [V(10), outline_button("Trò chuyện về tranh", lambda e: self.app.go(f"/chat/{p.id}"),
                                          height=50)]
        museum = [V(2), T(p.museum, 12, 400, MUTED, align=ft.TextAlign.CENTER)] if p.museum else []
        return ft.Column([
            V(12),
            self._card([
                ft.Row([_round_icon("check", 28, WHITE, PRIMARY), H(10), kicker("Đã nhận ra", 10, 1.2)],
                       spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                V(18),
                self._hero(p, self._hero_h(232)),
                V(18),
                T(p.title, 24, serif=True, align=ft.TextAlign.CENTER, lh=1.2),
                V(6),
                T(f"{p.artist} · {p.year}", 13, 400, MUTED, align=ft.TextAlign.CENTER),
                *museum,
                *detail_line,
                V(18),
                *buttons,
            ]),
            V(16),
            self.again_link(),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def maybe(self, res) -> ft.Control:
        p = PAINTINGS[res.painting]

        def no(e):
            self.st.declined = True
            self.refresh()

        return ft.Column([
            V(12),
            self._card([
                kicker("Có phải bức này không?", 10, 1.2),
                V(8),
                T("Ảnh chưa đủ rõ để AURA chắc chắn. Bạn xem có đúng bức vừa quét không nhé.", 15, 400, INK,
                  lh=1.4),
                V(16),
                self._hero(p, self._hero_h(200)),
                V(16),
                T(p.title, 22, serif=True, align=ft.TextAlign.CENTER, lh=1.2),
                V(4),
                T(f"{p.artist} · {p.year}", 13, 400, MUTED, align=ft.TextAlign.CENTER),
                V(18),
                primary_button("Đúng rồi, mở tranh", lambda e: self.app.go(f"/painting/{p.id}"), leading="check",
                               pill=True, height=52, size=15),
                V(10),
                outline_button("Không phải", no, height=50),
            ]),
            V(16),
            self.again_link(),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def not_found(self, reason: str) -> ft.Control:
        return ft.Column([
            V(12),
            self._card([
                ft.Row([_round_icon("info", 40), H(12),
                        T(NONE_TITLE.get(reason, "Chưa nhận ra bức tranh"), 21, serif=True, expand=True)],
                       spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                V(12),
                T(NONE_MSG.get(reason, NONE_MSG["none"]), 15, 400, INK, lh=1.4),
                V(18),
                *([self.shoot_button("Quét lại", height=52), V(10)] if reason != "unavailable" else []),
                outline_button("Tìm trong Kho tranh", lambda e: self.app.go("/gallery"), height=50),
                V(10),
                outline_button("Tả bằng lời ở Hỏi Aura", lambda e: self.app.go("/ask"), height=50),
            ]),
            *([V(22), kicker("Mẹo quét tranh", 10, 1.2), V(12), *_tip_rows()]
              if reason in ("blurry", "none", "declined") else []),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def build(app, q) -> ft.View:
    scr = _Screen(app)
    app.state.scan.screen = scr
    scr.holder.content = scr.render()
    view = screen("/scan", body([scr.holder], ref=scr.scroller),
                  top=top_bar("Scan tác phẩm", on_back=scr.cancel), nav=nav_bar(app, NAV_SCAN))
    scr.view = view
    if scr.ok:
        app.page.run_task(warm)
    if app.state.scan.phase == "working":
        scr.start_ticker()
    return view
