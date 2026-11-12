"""Màn Hỏi Aura — đối thoại Socrates quanh một bức tranh."""
from __future__ import annotations

import asyncio
import math
import re
import time

import flet as ft

from ..data import DEFAULT_ID, PAINTINGS, Painting
from ..socratic import STAGES, AuraTurn, Choice, Message
from ..theme import BEIGE, BORDER, INK, MUTED, PRIMARY, RADIUS, SURFACE, TINT, WHITE
from ..ui import (H, T, V, body, bottom_nav, bottom_sheet, cropped_image, icon, kicker, screen,
                  source_line, surface_field, top_bar)

ABOUT = ("AURA không đưa ra đáp án ngay. Theo phương pháp Socrates, AURA đặt câu hỏi để bạn tự "
         "quan sát, tách điều nhìn thấy khỏi điều suy đoán, rồi đối chiếu với nguồn của bảo tàng. "
         "Cuộc trò chuyện đi qua bốn chặng: Ấn tượng đầu → Tách chi tiết → Đối thoại → Mở rộng.")


def _painting_viewer(app, p: Painting) -> None:
    """Xem toàn bộ bức tranh ngay trong lúc chat (bảng trượt từ dưới lên, phóng to được).

    Không chuyển trang nên đóng lại vẫn ở đúng chỗ đang trò chuyện.
    """
    cw = app.content_width
    max_h = (app.page.height or 874) * 0.58
    w = min(cw, max_h * p.aspect)
    h = w / p.aspect

    def close(e=None):
        app.page.pop_dialog()

    def open_detail(key: str):
        app.page.pop_dialog()
        app.go(f"/detail/{p.id}/{key}")

    chips = [ft.Container(T(d.title, 11, 600, PRIMARY, no_wrap=True, lh=1.2), bgcolor=TINT,
                          border_radius=14, padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                          on_click=lambda e, k=d.key: open_detail(k))
             for d in p.details.values()]
    app.page.show_dialog(ft.BottomSheet(
        ft.Container(ft.Column([
            ft.Row([
                ft.Column([T(p.title, 20, 400, INK, serif=True, max_lines=1), V(3),
                           T(f"{p.artist} · {p.year}", 11, 400, MUTED, max_lines=1)],
                          spacing=0, tight=True, expand=True),
                ft.Container(icon("x", 22, INK), on_click=close, padding=4),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            V(14),
            ft.Container(
                ft.InteractiveViewer(ft.Image(src=p.image, width=w, height=h, fit=ft.BoxFit.FILL),
                                     min_scale=1, max_scale=5, boundary_margin=0),
                width=w, height=h, border_radius=4, clip_behavior=ft.ClipBehavior.HARD_EDGE),
            V(8),
            T("Chụm hai ngón tay để phóng to, kéo để di chuyển", 10, 400, MUTED),
            V(14),
            T("NHÌN KỸ MỘT CHI TIẾT", 9, 400, PRIMARY, ls=0.9),
            V(8),
            ft.Row(chips, spacing=6, run_spacing=6, wrap=True),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=24, right=24, top=18, bottom=24)),
        bgcolor=BG_OFF, scrollable=True, draggable=False, show_drag_handle=False,
    ))


def _painting_button(app, p: Painting) -> ft.Control:
    """Ảnh tranh nhỏ cạnh ô nhập: chạm để xem tranh mà không phải cuộn lên đầu."""
    return ft.Container(
        ft.Image(src=p.image, width=28, height=36, fit=ft.BoxFit.COVER),
        width=28, height=36, border_radius=4, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border=ft.Border.all(1, BORDER), tooltip="Xem tranh",
        on_click=lambda e: _painting_viewer(app, p))


def _context_card(app, p: Painting) -> ft.Control:
    return ft.Container(ft.Row([
        ft.Image(src=p.image, width=36, height=48, fit=ft.BoxFit.COVER),
        H(32),
        ft.Column([
            T("ĐANG CÙNG KHÁM PHÁ", 9, 400, PRIMARY, ls=0.9),
            V(1.2),
            T(p.title, 12, 600, INK, max_lines=1),
            V(3.5),
            T(f"{p.artist} · {p.year} · {p.museum}", 10, 400, MUTED, max_lines=1),
        ], spacing=0, tight=True, expand=True),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=BEIGE, border_radius=RADIUS, height=74, padding=ft.Padding.only(left=32, right=12),
        on_click=lambda e: _painting_viewer(app, p))


def _stage_chips(stage: int) -> ft.Row:
    chips = []
    for i, name in enumerate(STAGES):
        on = i <= stage
        chips.append(ft.Container(
            T(name, 10, 600, WHITE if on else PRIMARY, no_wrap=True, lh=1.2),
            padding=ft.Padding.symmetric(horizontal=7, vertical=7.5), border_radius=14,
            bgcolor=PRIMARY if on else BG_OFF, border=None if on else ft.Border.all(1, BORDER)))
    return ft.Row(chips, spacing=4, wrap=True, run_spacing=4)


BG_OFF = "#F6F2E8"


def _aura_header() -> ft.Control:
    return ft.Row([T("AURA", 22, 400, PRIMARY, serif=True, ls=0, lh=1.2), H(14),
                   ft.Container(T("Cùng bạn nhìn tranh", 10, 400, MUTED, lh=1.0),
                                padding=ft.Padding.only(top=4))],
                  spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _user_bubble(text: str) -> ft.Control:
    return ft.Row([
        ft.Container(
            T(text, 14, 400, WHITE), bgcolor=PRIMARY,
            padding=ft.Padding.only(left=15, right=11, top=13.5, bottom=16),
            border_radius=ft.BorderRadius.only(top_left=16, top_right=16, bottom_left=16,
                                               bottom_right=2),
            width=290,
        )], alignment=ft.MainAxisAlignment.END)


def _choice(c: Choice, *, picked: bool, enabled: bool, on_click) -> ft.Control:
    return ft.Container(ft.Row([
        T(c.label, 11, 400, PRIMARY, expand=True, lh=1.2),
        H(12), icon("arrow-up-right", 16, PRIMARY),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=TINT if picked else None, border=ft.Border.all(1, BORDER), border_radius=23,
        padding=ft.Padding.only(left=13, right=16, top=8, bottom=8),
        on_click=on_click if enabled else None, ink=enabled,      # gợn sóng khi chạm
        opacity=1.0 if (enabled or picked) else 0.55,
        animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT))


def _detail_card(app, p: Painting, att) -> ft.Control:
    w = app.content_width - 16
    return ft.Container(ft.Column([
        V(6.2),
        T(att.label.upper(), 9, 400, PRIMARY, ls=0.8),
        V(6.2),
        cropped_image(p.image, p.aspect, w, 180, att.crop, radius=4,
                      on_click=lambda e: app.go(f"/detail/{p.id}/{att.detail_key}")),
        V(7),
        ft.Container(ft.Row([T("Xem toàn bộ chi tiết", 11, 600, PRIMARY), H(12),
                             icon("arrow-up-right", 16, PRIMARY)], spacing=0, tight=True),
                     bgcolor=TINT, height=30, border_radius=15,
                     padding=ft.Padding.only(left=12, right=12), alignment=ft.Alignment.CENTER_LEFT,
                     on_click=lambda e: app.go(f"/detail/{p.id}/{att.detail_key}")),
        V(8),
    ], spacing=0, tight=True), bgcolor=BEIGE, border_radius=RADIUS,
        padding=ft.Padding.symmetric(horizontal=8))


def _summary_card(app, p: Painting, s) -> ft.Control:
    return ft.Container(ft.Column([
        T(s.title, 14, 600, INK),
        V(7.5),
        T(s.text, 12, 400, INK),
        V(12),
        ft.Container(ft.Row([T(s.action, 13, 600, WHITE), ft.Container(expand=True),
                             icon("arrow-up-right", 18, WHITE)], spacing=0),
                     height=40, bgcolor=PRIMARY, border_radius=20,
                     padding=ft.Padding.only(left=16, right=19), alignment=ft.Alignment.CENTER_LEFT,
                     on_click=lambda e: app.go(f"/quiz/{p.id}")),
    ], spacing=0, tight=True), bgcolor=BEIGE, border_radius=RADIUS,
        padding=ft.Padding.only(left=12, right=12, top=9, bottom=12))


MIN_THINK = 0.6          # giây: "đang suy nghĩ" hiện đủ lâu để không chớp tắt
DOT = 6
TYPE_TICK = 0.035        # giây giữa hai lần hiện thêm chữ (hiệu ứng "đang gõ")
TYPE_PARA_MAX = 1.6      # một đoạn dài cỡ nào cũng gõ xong trong khoảng chừng này giây
WORD_RE = re.compile(r"\S+\s*")


# Chờ càng lâu thì dòng chữ đổi dần, để người dùng biết app vẫn đang chạy chứ không bị treo.
THINK_LABELS = [(0, "AURA đang suy nghĩ"), (3, "AURA đang ngẫm kỹ câu của bạn"), (7, "Sắp xong rồi")]


def _thinking() -> tuple[ft.Control, list[ft.Container], ft.Text]:
    """Dòng "AURA đang suy nghĩ" với ba chấm nhấp nháy lần lượt."""
    dots = [ft.Container(width=DOT, height=DOT, border_radius=DOT / 2, bgcolor=PRIMARY,
                         opacity=0.25, animate_opacity=ft.Animation(260, ft.AnimationCurve.EASE_IN_OUT))
            for _ in range(3)]
    label = T(THINK_LABELS[0][1], 12, 600, PRIMARY)
    row = ft.Row([label, H(8), dots[0], H(4), dots[1], H(4), dots[2]],
                 spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return row, dots, label


def _appear(c: ft.Container) -> ft.Container:
    """Đặt trạng thái ban đầu (mờ, lệch xuống) để khi hiện ra có hiệu ứng trượt nhẹ lên."""
    c.opacity = 0
    c.offset = ft.Offset(0, 0.03)
    c.animate_opacity = ft.Animation(280, ft.AnimationCurve.EASE_OUT)
    c.animate_offset = ft.Animation(340, ft.AnimationCurve.EASE_OUT_CUBIC)
    return c


def build(app, q, pid: str = DEFAULT_ID) -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS[DEFAULT_ID]
    st = app.state.chat(p.id)
    engine = app.engine

    stage_holder = ft.Container(_stage_chips(st.stage))
    scroller = ft.Ref[ft.Column]()
    think_row, dots, think_label = _thinking()
    think_box = ft.Container(ft.Column([V(14), think_row], spacing=0, tight=True),
                             visible=st.thinking)
    # Mỗi tin nhắn là một khối riêng: tin mới chỉ THÊM khối mới, không vẽ lại cả cuộc trò chuyện.
    thread = ft.Column([think_box], spacing=0, tight=True,
                       horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    blocks: dict[int, ft.Container] = {}
    # Hiệu ứng gõ chữ: tin AURA mới hiện từng cụm từ; nút gợi ý/ảnh chi tiết hiện sau khi gõ xong.
    typing: dict[int, tuple[list[ft.Text], ft.Container]] = {}   # i -> (các đoạn chữ, khối phần phụ)
    fade_in: set[int] = set()

    def last_aura() -> int:
        return max((i for i, m in enumerate(st.messages) if m.role == "aura"), default=-1)

    def block_controls(i: int) -> ft.Column:
        m = st.messages[i]
        prev = st.messages[i - 1].role if i else None
        if m.role == "user":
            items = [V(12.5 if prev == "aura" else 9), _user_bubble(m.text)]
        else:
            first = next(j for j, x in enumerate(st.messages) if x.role == "aura")
            items = [V(17.8 if prev is None else 14),
                     *_aura_block(i, m, interactive=(i == last_aura()) and not st.thinking,
                                  header=(i == first))]
        return ft.Column(items, spacing=0, tight=True,
                         horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def sync(animate: bool) -> list[ft.Container]:
        """Thêm khối cho các tin nhắn chưa có trên màn hình; trả về các khối mới."""
        new = []
        for i in range(len(st.messages)):
            if i in blocks:
                continue
            c = ft.Container(block_controls(i), key=ft.ScrollKey(f"m{i}"))
            blocks[i] = _appear(c) if animate else c
            thread.controls.insert(len(thread.controls) - 1, c)   # luôn đứng trước think_box
            new.append(c)
        stage_holder.content = _stage_chips(st.stage)
        return new

    def refresh(i: int) -> None:
        """Vẽ lại riêng một khối (vd khoá các nút gợi ý của lượt vừa trả lời)."""
        if i in blocks:
            blocks[i].content = block_controls(i)

    async def reveal(new: list[ft.Container]) -> None:
        if not new:
            return
        await asyncio.sleep(0.03)          # để khung hình "mờ" kịp vẽ trước khi chạy hiệu ứng
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
                await scroller.current.scroll_to(offset=-1, duration=duration,
                                                 curve=ft.AnimationCurve.EASE_OUT_CUBIC)
        except Exception:                  # màn chat đã bị đóng
            pass

    async def pulse() -> None:
        k, t0 = 0, time.monotonic()
        while st.thinking and think_box.visible:
            waited = time.monotonic() - t0
            think_label.value = [s for after, s in THINK_LABELS if waited >= after][-1]
            for j, d in enumerate(dots):
                d.opacity = 1.0 if j == k % 3 else 0.25
            try:
                think_row.update()
            except Exception:
                return
            k += 1
            await asyncio.sleep(0.3)

    def set_thinking(on: bool) -> None:
        st.thinking = on
        think_box.visible = on

    def _aura_block(i: int, m: Message, interactive: bool, header: bool) -> list[ft.Control]:
        t: AuraTurn = m.turn
        # Tên "AURA" chỉ giới thiệu một lần ở tin nhắn đầu, các lượt sau không lặp lại.
        out: list[ft.Control] = [_aura_header(), V(10.3)] if header else []
        texts: list[ft.Text] = []
        for k, para in enumerate(t.paragraphs):
            if k:
                out.append(V(8))
            texts.append(T("" if i in typing else para, 14, 400, INK))
            out.append(texts[-1])
        # Phần phụ (ảnh chi tiết, nút gợi ý, thẻ tổng kết, nguồn) gom vào một khối để hiện sau chữ.
        extras = _aura_extras(i, t, interactive)
        box = ft.Container(ft.Column(extras, spacing=0, tight=True,
                                     horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                           visible=i not in typing, opacity=0 if i in fade_in else 1,
                           animate_opacity=ft.Animation(320, ft.AnimationCurve.EASE_OUT))
        if i in typing:
            typing[i] = (texts, box)
        return out + [box]

    async def type_out(i: int) -> None:
        """Hiện chữ của tin AURA thứ i dần dần theo từng cụm từ, như đang gõ."""
        texts, box = typing[i]
        paras = st.messages[i].turn.paragraphs
        for txt, para in zip(texts, paras):
            words = WORD_RE.findall(para)
            per_tick = max(1, math.ceil(len(words) * TYPE_TICK / TYPE_PARA_MAX))
            for n in range(per_tick, len(words) + per_tick, per_tick):
                txt.value = "".join(words[:n])
                try:
                    txt.update()
                except Exception:          # màn chat đã bị đóng giữa chừng
                    return
                await asyncio.sleep(TYPE_TICK)
            txt.value = para
        typing.pop(i, None)
        st.thinking = False
        fade_in.add(i)
        refresh(i)                         # dựng lại khối: nút gợi ý bấm được, phần phụ mờ -> rõ dần
        app.page.update()
        await asyncio.sleep(0.03)
        fade_in.discard(i)
        if i in blocks:
            blocks[i].content.controls[-1].opacity = 1
            app.page.update()

    def _aura_extras(i: int, t: AuraTurn, interactive: bool) -> list[ft.Control]:
        out: list[ft.Control] = []
        if t.attachment:
            out += [V(9.5), _detail_card(app, p, t.attachment)]
        if t.choices:
            out.append(V(10))
            for k, c in enumerate(t.choices):
                if k:
                    out.append(V(9))
                out.append(_choice(c, picked=st.picked.get(i) == k,
                                   enabled=interactive and not st.thinking,
                                   on_click=lambda e, c=c, k=k, i=i: app.page.run_task(
                                       send, c.text, i, k)))
        if t.summary:
            out += [V(13.5), _summary_card(app, p, t.summary)]
        if t.source:
            out += [V(10.5), source_line(t.source, lambda e: app.open_url(p.url))]
        return out

    async def send(text: str, msg_index: int | None = None, choice: int | None = None):
        text = (text or "").strip()
        if not text or st.thinking:
            return
        last = st.messages[-1].turn if st.messages and st.messages[-1].role == "aura" else None
        if last is not None and last.done:
            return
        if msg_index is not None:
            st.picked[msg_index] = choice
        prev_aura = last_aura()
        st.messages.append(Message("user", text))

        # 1) Tin của người dùng trượt lên, nút gợi ý cũ khoá lại, AURA bắt đầu "suy nghĩ"
        set_thinking(True)
        refresh(prev_aura)
        new = sync(animate=True)
        app.page.update()
        await reveal(new)
        await scroll()
        app.page.run_task(pulse)

        # 2) Chờ câu trả lời (tối thiểu MIN_THINK giây cho tự nhiên)
        t0 = time.monotonic()
        try:
            turn = await engine.reply(p, st.messages, text)
        except Exception as ex:            # engine lỗi: báo nhẹ, không treo màn chat
            print(f"[chat] engine.reply lỗi: {ex}")
            turn = AuraTurn(["Xin lỗi, mình vừa gặp trục trặc nhỏ. Bạn thử gửi lại nhé."],
                            stage=st.stage)
        wait = MIN_THINK - (time.monotonic() - t0)
        if wait > 0:
            await asyncio.sleep(wait)

        # 3) Câu trả lời hiện ra như đang gõ; cuộn để thấy cả tin vừa gửi lẫn đầu câu trả lời.
        #    Trong lúc gõ vẫn coi là "đang bận" (st.thinking) để không gửi chen ngang.
        think_box.visible = False
        st.messages.append(Message("aura", turn.paragraphs[0], turn))
        st.stage = max(st.stage, turn.stage)
        await show_typed(len(st.messages) - 1, scroll_key=f"m{len(st.messages) - 2}")

    async def show_typed(i: int, scroll_key: str | None = None) -> None:
        typing[i] = ([], ft.Container())
        try:
            new = sync(animate=True)
            app.page.update()
            await reveal(new)
            if scroll_key:
                await scroll(scroll_key)
            await type_out(i)
        finally:
            typing.pop(i, None)
            st.thinking = False

    async def start():
        if not st.messages and st.starting:
            # Một bản khác của màn này (vừa được dựng lại, vd khi đổi kích thước) đang lấy lời chào:
            # chờ nó xong rồi chỉ việc hiện tin nhắn, không xin lời chào lần nữa.
            while st.starting:
                await asyncio.sleep(0.05)
        elif not st.messages:
            st.starting = True
            try:
                turn = await engine.start(p)
            finally:
                st.starting = False
            st.messages.append(Message("aura", turn.paragraphs[0], turn))
            st.stage = turn.stage
            st.thinking = True
            await show_typed(0)
            return
        new = sync(animate=False)
        app.page.update()
        await reveal(new)
        await scroll(duration=0)           # quay lại cuộc trò chuyện cũ: về cuối ngay

    field = ft.TextField(hint_text="Bạn muốn hiểu thêm điều gì?", expand=True,
                         text_style=ft.TextStyle(size=13, color=INK, font_family="Inter",
                                                 letter_spacing=0),
                         hint_style=ft.TextStyle(size=13, color=MUTED, font_family="Inter",
                                                 letter_spacing=0),
                         shift_enter=True, min_lines=1, max_lines=4, **surface_field())

    async def submit(e=None):
        text = field.value
        field.value = ""
        field.update()
        try:
            await field.focus()            # giữ bàn phím để gõ tiếp
        except Exception:
            pass
        await send(text)

    field.on_submit = submit
    composer = ft.Container(ft.Row([
        _painting_button(app, p), H(10),
        field, H(10),
        ft.Container(icon("arrow-up", 16, WHITE), width=30, height=30, border_radius=15,
                     bgcolor=PRIMARY, alignment=ft.Alignment.CENTER, on_click=submit),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=26,
        padding=ft.Padding.only(left=10, right=10, top=8, bottom=8), height=52)

    content = body([
        V(14),
        _context_card(app, p),
        V(18.2),
        T("TIẾN TRÌNH TRÒ CHUYỆN", 9, 400, PRIMARY, ls=0.9),
        V(8.2),
        stage_holder,
        thread,
    ], bottom=11.5, ref=scroller)          # tự cuộn bằng scroll_to (mượt) thay cho auto_scroll
    footer = ft.Container(composer, padding=ft.Padding.only(left=24, right=24, top=10, bottom=20.5))
    sync(animate=False)                    # tin nhắn cũ (khi quay lại màn chat) hiện ngay
    app.page.run_task(start)
    return screen(f"/chat/{p.id}", content,
                  top=top_bar("Hỏi Aura", on_back=app.back_handler, trailing="info",
                              on_trailing=lambda e: bottom_sheet(app.page, "AURA hỏi, bạn nhìn", ABOUT)),
                  footer=footer, nav=bottom_nav(1, app.go))
