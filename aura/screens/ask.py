"""Màn Hỏi Aura (tab trên thanh điều hướng): hỏi đáp mở về thời Phục Hưng và về mọi bức tranh.

- Hỏi kiến thức chung (họa sĩ, kỹ thuật, lịch sử...) hoặc về bất kỳ bức tranh nào trên thế giới.
- Tả một bức tranh ("người phụ nữ cười bí ẩn, hai tay đặt lên nhau"): AURA đoán tên; nếu bức đó có trong
  Kho tranh thì hiện thẻ tranh với nút mở thẳng bức đó (và nút trò chuyện về bức tranh).
- Câu hỏi khớp một bài ở trang Khám phá thì kèm nút "Đọc thêm".
Trò chuyện theo kiểu Socrates về MỘT bức tranh vẫn nằm ở trang tranh (/chat/<id>).
Cuộc hỏi đáp được cất trong bộ nhớ trình duyệt (app.save_ask) nên tải lại trang không mất.
"""
from __future__ import annotations

import asyncio
import time

import flet as ft

from ..data import ALL_PAINTINGS, PAINTINGS
from ..theme import BG, GLASS, GLASS_EDGE, INK, MAX_W, MUTED, PRIMARY, SHADOW_INK, TINT, WHITE, WINE_LIGHT
from ..topics import ALL as TOPICS
from ..ui import (H, NAV_ASK, T, V, body, glass, icon, kicker, logo, nav_bar, screen, surface_field, top_bar)
from .chat import _appear, _prompt_chip, _user_bubble

STARTERS = [
    "Bức tranh có người phụ nữ nở nụ cười bí ẩn, hai tay đặt lên nhau",
    "Phục Hưng bắt đầu từ đâu và vì sao?",
    "Tranh có chiếc gương lồi phản chiếu cả căn phòng",
    "Sfumato khác chiaroscuro thế nào?",
    "Michelangelo vẽ trần Nhà nguyện Sistine ra sao?",
    "Bức tranh có bầu trời xoáy và những ngôi sao vàng",
]
THINK_LABELS = [(0, "ĐANG ĐỌC CÂU HỎI CỦA BẠN"), (1.5, "ĐANG TRA CỨU"), (4, "ĐANG SOẠN CÂU TRẢ LỜI"),
                (9, "SẮP XONG RỒI")]
MIN_THINK = 0.5
SOURCE_LABEL = {"ai": ("sparkles", "AI TRẢ LỜI · KIẾN THỨC CHUNG"), "notes": ("book-open", "TƯ LIỆU CỦA AURA")}


def _guide(app):
    """Engine hỏi đáp: dùng chung AI với chatbot nếu có; không thì bản offline (chỉ tư liệu của app)."""
    if getattr(app.engine, "ask_general", None) is not None:
        return None
    g = getattr(app, "_offline_guide", None)
    if g is None:
        from Chatbot.general import GeneralGuide
        g = app._offline_guide = GeneralGuide(None, ALL_PAINTINGS, list(TOPICS.values()))
    return g


def _painting_card(app, pid: str, confidence: str) -> ft.Control:
    """Thẻ tranh có trong Kho tranh: ảnh nhỏ có khung + tên + hai nút dẫn thẳng tới bức tranh."""
    p = PAINTINGS[pid]
    thumb = ft.Container(ft.Image(src=p.image, width=46, height=round(46 / p.aspect), fit=ft.BoxFit.COVER),
                         border=ft.Border.all(2, "#6B4F3A"), bgcolor=WHITE, padding=2,
                         shadow=[ft.BoxShadow(blur_radius=6, offset=ft.Offset(0, 2), color=f"{SHADOW_INK},0.18")])

    def pill(text: str, route: str, main: bool) -> ft.Control:
        return ft.Container(ft.Row([T(text, 12, 600, WHITE if main else PRIMARY), H(6),
                                    icon("arrow-up-right", 14, WHITE if main else PRIMARY)], spacing=0, tight=True),
                            height=34, padding=ft.Padding.symmetric(horizontal=14), border_radius=17,
                            bgcolor=PRIMARY if main else TINT, alignment=ft.Alignment.CENTER,
                            on_click=lambda e: app.go(route))

    head = "CÓ THỂ LÀ BỨC NÀY" if confidence == "low" else "CÓ TRONG KHO TRANH AURA"
    return glass(ft.Column([
        ft.Row([thumb, H(14), ft.Column([
            T(head, 9, 600, PRIMARY, ls=1.0), V(4),
            T(p.title, 17, serif=True, max_lines=2), V(3),
            T(f"{p.artist} · {p.year}", 11, 400, MUTED, max_lines=1),
        ], spacing=0, tight=True, expand=True)], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(12),
        ft.Row([pill("Xem tranh", f"/painting/{p.id}", True), pill("Trò chuyện về tranh", f"/chat/{p.id}", False)],
               spacing=8, wrap=True, run_spacing=8),
    ], spacing=0, tight=True), radius=14, padding=ft.Padding.only(left=12, right=12, top=12, bottom=12))


def _identified_line(ident: dict) -> ft.Control:
    """Bức tranh AURA nhận ra nhưng chưa có trong Kho tranh: chỉ ghi tên, không có nút."""
    meta = " · ".join(x for x in (ident.get("artist"), ident.get("year")) if x)
    return ft.Container(ft.Row([
        icon("image", 16, MUTED), H(10),
        ft.Column([T(f"“{ident['title']}”", 13, 600, INK), V(2),
                   T((meta + " · " if meta else "") + "chưa có trong Kho tranh AURA", 11, 400, MUTED)],
                  spacing=0, tight=True, expand=True),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=GLASS, border=ft.Border.all(1, GLASS_EDGE), border_radius=12,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10))


def _topic_link(app, tid: str) -> ft.Control:
    t = TOPICS[tid]
    return ft.Container(ft.Row([icon("book-open", 14, PRIMARY), H(8), T(f"Đọc thêm: {t.title}", 12, 600, PRIMARY),
                                H(6), icon("arrow-up-right", 14, PRIMARY)], spacing=0, tight=True),
                        height=32, padding=ft.Padding.symmetric(horizontal=12), border_radius=16, bgcolor=TINT,
                        alignment=ft.Alignment.CENTER_LEFT, on_click=lambda e: app.go(f"/topic/{tid}"))


def _aura_block(app, m: dict, first: bool) -> list[ft.Control]:
    out: list[ft.Control] = []
    if first:
        out += [ft.Row([logo(21), H(12), T("Hỏi gì cũng được", 10, 400, MUTED)], spacing=0,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER), V(10)]
    inner: list[ft.Control] = []
    label = SOURCE_LABEL.get(m.get("source"))
    if label:
        inner += [ft.Row([icon(label[0], 12, PRIMARY), H(6), T(label[1], 9, 600, PRIMARY, ls=1.0)],
                         spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER), V(7)]
    inner.append(T(m.get("text", ""), 14, 400, INK))
    bubble = glass(ft.Column(inner, spacing=0, tight=True), radius=18,
                   padding=ft.Padding.only(left=15, right=15, top=12, bottom=14), margin=ft.Margin.only(right=18))
    bubble.border_radius = ft.BorderRadius.only(top_left=4, top_right=18, bottom_left=18, bottom_right=18)
    out.append(bubble)
    pid, ident, tid = m.get("painting"), m.get("identified"), m.get("topic")
    if pid in PAINTINGS:
        out += [V(10), _painting_card(app, pid, m.get("confidence", "high"))]
    elif isinstance(ident, dict) and ident.get("title"):
        out += [V(10), _identified_line(ident)]
    if tid in TOPICS:
        out += [V(8), ft.Row([_topic_link(app, tid)], spacing=0)]
    return out


def _starter(text: str, on_click) -> ft.Control:
    return ft.Container(ft.Row([T(text, 12, 500, PRIMARY, expand=True, lh=1.3), H(12),
                                icon("arrow-up-right", 16, PRIMARY)],
                               spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=GLASS, border=ft.Border.all(1, GLASS_EDGE), border_radius=23,
                        padding=ft.Padding.only(left=14, right=16, top=10, bottom=10), on_click=on_click, ink=True)


def build(app, q) -> ft.View:
    st = app.state.ask
    cw = app.content_width
    scroller = ft.Ref[ft.Column]()
    blocks: dict[int, ft.Container] = {}

    label = T(THINK_LABELS[0][1], 9.5, 600, PRIMARY, ls=1.0, lh=1.2)
    think_box = ft.Container(ft.Column([V(16), ft.Row([glass(ft.Column([
        ft.Row([logo(12), H(10), label], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER), V(9),
        ft.Container(ft.ProgressBar(bar_height=2.5, color=PRIMARY, bgcolor=TINT, border_radius=2), width=210),
    ], spacing=0, tight=True), radius=14, padding=ft.Padding.only(left=14, right=16, top=11, bottom=12))],
        spacing=0)], spacing=0, tight=True), visible=st.thinking)
    thread = ft.Column([think_box], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    prompts_row = ft.Row([], spacing=8, scroll=ft.ScrollMode.AUTO)
    prompts_box = ft.Container(ft.Column([prompts_row, V(8)], spacing=0, tight=True), visible=False)

    def block(i: int) -> ft.Column:
        m = st.messages[i]
        prev = st.messages[i - 1]["role"] if i else None
        if m["role"] == "user":
            items = [V(14 if prev == "aura" else 9), _user_bubble(m["text"], cw * 0.82)]
        else:
            first = next(j for j, x in enumerate(st.messages) if x["role"] == "aura") == i
            items = [V(16), *_aura_block(app, m, first)]
        return ft.Column(items, spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def sync(animate: bool) -> list[ft.Container]:
        new = []
        for i in range(len(st.messages)):
            if i in blocks:
                continue
            c = ft.Container(block(i), key=ft.ScrollKey(f"a{i}"))
            blocks[i] = _appear(c) if animate else c
            thread.controls.insert(len(thread.controls) - 1, c)      # luôn đứng trước think_box
            new.append(c)
        intro.visible = not st.messages
        head.visible = bool(st.messages)
        refresh_prompts()
        return new

    def refresh_prompts() -> None:
        asked = {m["text"] for m in st.messages if m["role"] == "user"}
        items = [x for x in STARTERS if x not in asked][:4] if st.messages and not st.thinking else []
        prompts_row.controls = [_prompt_chip(x, lambda e, x=x: app.page.run_task(send, x)) for x in items]
        prompts_box.visible = bool(items)

    async def reveal(new: list[ft.Container]) -> None:
        if not new:
            return
        await asyncio.sleep(0.03)
        for c in new:
            c.opacity = 1
            c.offset = ft.Offset(0, 0)
        app.page.update()

    async def scroll(key: str | None = None, duration: int = 380) -> None:
        try:
            if key:
                await scroller.current.scroll_to(scroll_key=key, duration=duration,
                                                 curve=ft.AnimationCurve.EASE_OUT_CUBIC)
            else:
                await scroller.current.scroll_to(offset=-1, duration=duration, curve=ft.AnimationCurve.EASE_OUT_CUBIC)
        except Exception:                      # màn đã đóng
            pass

    async def pulse() -> None:
        t0, shown = time.monotonic(), THINK_LABELS[0][1]
        label.value = shown
        while st.thinking and think_box.visible:
            now = [s for after, s in THINK_LABELS if time.monotonic() - t0 >= after][-1]
            if now != shown:
                shown = label.value = now
                try:
                    label.update()
                except Exception:
                    return
            await asyncio.sleep(0.25)

    async def send(text: str) -> None:
        text = (text or "").strip()
        if not text or st.thinking:
            return
        history = [{"role": m["role"], "text": m["text"]} for m in st.messages[-6:]]
        st.messages.append({"role": "user", "text": text})
        st.thinking = think_box.visible = True
        new = sync(animate=True)
        app.page.update()
        await reveal(new)
        await scroll()
        app.page.run_task(pulse)
        t0 = time.monotonic()
        try:
            guide = _guide(app)
            if guide is None:
                res = await app.engine.ask_general(text, history)
            else:
                res = await asyncio.to_thread(guide.reply, text, history)
        except Exception as ex:                # lỗi bất ngờ: báo nhẹ, không treo màn
            print(f"[ask] lỗi: {ex}")
            res = {"text": "Xin lỗi, mình vừa gặp trục trặc nhỏ. Bạn thử gửi lại nhé.", "source": "offline"}
        wait = MIN_THINK - (time.monotonic() - t0)
        if wait > 0:
            await asyncio.sleep(wait)
        st.messages.append({"role": "aura", **{k: res.get(k) for k in
                                                ("text", "painting", "identified", "topic", "source", "confidence")}})
        st.thinking = think_box.visible = False
        app.save_ask()
        new = sync(animate=True)
        try:
            app.page.update()
        except Exception:
            return
        await reveal(new)
        await scroll(f"a{len(st.messages) - 2}")   # thấy cả câu hỏi lẫn đầu câu trả lời

    async def start() -> None:
        await app.wait_chats()                 # đọc xong cuộc hỏi đáp cất từ lần trước (nếu có)
        new = sync(animate=False)
        try:
            app.page.update()
        except Exception:
            return
        await reveal(new)
        if st.messages:
            await scroll_end()

    async def scroll_end() -> None:
        if not app.page.views or app.page.views[-1].route != "/ask":
            return
        for wait in (0.05, 0.4, 1.2):
            await asyncio.sleep(wait)
            await scroll(duration=0)

    def confirm_clear(e=None) -> None:
        async def do(e2):
            app.page.pop_dialog()
            if st.thinking:
                return
            await asyncio.sleep(0.35)          # chờ hộp thoại đóng hẳn rồi mới dựng lại màn
            st.messages.clear()
            app.save_ask()
            app.rebuild()

        app.page.show_dialog(ft.AlertDialog(
            bgcolor=BG, title=T("Xoá cuộc hỏi đáp?", 21, serif=True),
            content=T("Các câu hỏi và câu trả lời ở đây sẽ được xoá để bắt đầu lại.", 13, 400, MUTED),
            actions=[ft.TextButton(content=T("Huỷ", 13, 600, MUTED), on_click=lambda e2: app.page.pop_dialog()),
                     ft.TextButton(content=T("Xoá", 13, 600, PRIMARY), on_click=do)]))

    intro = ft.Column([
        V(16),
        glass(ft.Column([
            ft.Row([icon("sparkles", 14, PRIMARY), H(7), kicker("Hỏi Aura", 10, 1.2)], spacing=0,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            V(8),
            T("Hỏi mọi điều về thời Phục Hưng", 23, serif=True),
            V(8),
            T("Họa sĩ, kỹ thuật, lịch sử hay bất kỳ bức tranh nào trên thế giới. Nhớ mang máng một bức tranh? "
              "Cứ tả lại, AURA sẽ đoán tên và đưa bạn tới đúng bức trong Kho tranh.", 13, 400, INK),
        ], spacing=0, tight=True), radius=16, padding=ft.Padding.only(left=16, right=16, top=14, bottom=16)),
        V(20),
        kicker("Thử hỏi", 9, 1.1),
        V(10),
        *[c for k, x in enumerate(STARTERS) for c in ([V(8)] if k else []) +
          [_starter(x, lambda e, x=x: app.page.run_task(send, x))]],
        V(14),
        T("AURA trả lời bằng AI và tư liệu của ứng dụng. Với kiến thức chung, hãy xem đó là điểm khởi đầu để "
          "tìm hiểu thêm.", 11, 400, MUTED),
    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, visible=not st.messages)
    head = ft.Column([V(14), ft.Row([
        T("CUỘC HỎI ĐÁP", 9, 600, PRIMARY, ls=1.0, expand=True),
        ft.Container(ft.Row([icon("rotate-ccw", 13, MUTED), H(5), T("Bắt đầu lại", 11, 500, MUTED)],
                            spacing=0, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                     on_click=confirm_clear, padding=ft.Padding.symmetric(vertical=4)),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)], spacing=0, tight=True,
        visible=bool(st.messages))

    field = ft.TextField(hint_text="Hỏi hoặc tả một bức tranh…", expand=True,
                         text_style=ft.TextStyle(size=13, color=INK, font_family="Inter", letter_spacing=0),
                         hint_style=ft.TextStyle(size=13, color=MUTED, font_family="Inter", letter_spacing=0),
                         shift_enter=True, min_lines=1, max_lines=4, **surface_field())

    async def submit(e=None):
        text = field.value
        if st.thinking or not (text or "").strip():
            return
        field.value = ""
        field.update()
        try:
            await field.focus()
        except Exception:
            pass
        await send(text)

    field.on_submit = submit
    composer = glass(ft.Row([
        ft.Container(icon("sparkles", 18, PRIMARY), width=32, height=32, border_radius=16, bgcolor=TINT,
                     alignment=ft.Alignment.CENTER), H(10),
        field, H(10),
        ft.Container(icon("arrow-up", 16, WHITE), width=32, height=32, border_radius=16,
                     gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                                colors=[WINE_LIGHT, PRIMARY]),
                     alignment=ft.Alignment.CENTER, on_click=submit),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        strong=True, shadow=True, radius=26, padding=ft.Padding.only(left=10, right=10, top=8, bottom=8), height=54)

    content = body([intro, head, thread], bottom=11.5, ref=scroller)
    docked = app.page_width <= MAX_W
    footer = ft.Container(ft.Column([prompts_box, composer], spacing=0, tight=True),
                          padding=ft.Padding.only(left=24, right=24, top=10, bottom=10 if docked else 20.5))
    sync(animate=False)
    app.on_reconnect = scroll_end
    app.page.run_task(start)
    return screen("/ask", content, top=top_bar("Hỏi Aura", on_back=app.back_handler),
                  footer=footer, nav=nav_bar(app, NAV_ASK))
