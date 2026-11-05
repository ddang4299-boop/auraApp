"""Màn Hỏi Aura — đối thoại Socrates quanh một bức tranh."""
from __future__ import annotations

import asyncio

import flet as ft

from ..app import ChatState
from ..data import PAINTINGS, Painting
from ..socratic import (ARNOLFINI_DEMO_REPLIES, STAGES, AuraTurn, Choice, Message,
                        ScriptedSocraticEngine)
from ..theme import BEIGE, BORDER, INK, MUTED, PRIMARY, RADIUS, SURFACE, TINT, WHITE
from ..ui import (H, T, V, body, bottom_nav, bottom_sheet, cropped_image, icon, kicker, screen,
                  source_line, surface_field, top_bar)

ABOUT = ("AURA không đưa ra đáp án ngay. Theo phương pháp Socrates, AURA đặt câu hỏi để bạn tự "
         "quan sát, tách điều nhìn thấy khỏi điều suy đoán, rồi đối chiếu với nguồn của bảo tàng. "
         "Cuộc trò chuyện đi qua bốn chặng: Ấn tượng đầu → Tách chi tiết → Đối thoại → Mở rộng.")


def _context_card(p: Painting) -> ft.Control:
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
        bgcolor=BEIGE, border_radius=RADIUS, height=74, padding=ft.Padding.only(left=32, right=12))


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
        on_click=on_click if enabled else None, opacity=1.0)


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


def _thinking() -> ft.Control:
    return ft.Row([T("AURA đang suy nghĩ…", 12, 600, PRIMARY), H(10), T("…", 12, 400, MUTED)],
                  spacing=0)


def build(app, q, pid: str = "arnolfini") -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS["arnolfini"]
    demo = q.get("demo") == "1"
    if demo:
        app.state.chats[p.id] = ChatState()
    st = app.state.chat(p.id)
    engine = ScriptedSocraticEngine(think_delay=0) if demo else app.engine

    stage_holder = ft.Container(_stage_chips(st.stage))
    thread = ft.Column(spacing=0, tight=True)

    def render():
        items: list[ft.Control] = []
        last_aura = max((i for i, m in enumerate(st.messages) if m.role == "aura"), default=-1)
        prev = None
        for i, m in enumerate(st.messages):
            if m.role == "user":
                items += [V(12.5 if prev == "aura" else 9), _user_bubble(m.text)]
            else:
                items.append(V(17.8 if prev is None else 9.8))
                items += _aura_block(i, m, interactive=(i == last_aura))
            prev = m.role
        if st.thinking:
            items += [V(9.5), _thinking()]
        thread.controls = items
        stage_holder.content = _stage_chips(st.stage)

    def _aura_block(i: int, m: Message, interactive: bool) -> list[ft.Control]:
        t: AuraTurn = m.turn
        out: list[ft.Control] = [_aura_header(), V(10.3)]
        for k, para in enumerate(t.paragraphs):
            if k:
                out.append(V(8))
            out.append(T(para, 14, 400, INK))
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

    async def send(text: str, msg_index: int | None = None, choice: int | None = None,
                   update: bool = True):
        text = (text or "").strip()
        if not text or st.thinking:
            return
        last = st.messages[-1].turn if st.messages and st.messages[-1].role == "aura" else None
        if last is not None and last.done:
            return
        if msg_index is not None:
            st.picked[msg_index] = choice
        st.messages.append(Message("user", text))
        st.thinking = not demo
        render()
        if update:
            app.page.update()
        turn = await engine.reply(p, st.messages, text)
        st.thinking = False
        st.messages.append(Message("aura", turn.paragraphs[0], turn))
        st.stage = max(st.stage, turn.stage)
        render()
        if update:
            app.page.update()

    async def start():
        if not st.messages:
            turn = await engine.start(p)
            st.messages.append(Message("aura", turn.paragraphs[0], turn))
            st.stage = turn.stage
        if demo:
            for r in ARNOLFINI_DEMO_REPLIES:
                last_i = len(st.messages) - 1
                if isinstance(r, int):
                    c = st.messages[last_i].turn.choices[r]
                    await send(c.text, last_i, r, update=False)
                else:
                    await send(r, update=False)
        render()
        app.page.update()

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
        await send(text)

    field.on_submit = submit
    composer = ft.Container(ft.Row([
        field, H(10),
        ft.Container(icon("arrow-up", 16, WHITE), width=30, height=30, border_radius=15,
                     bgcolor=PRIMARY, alignment=ft.Alignment.CENTER, on_click=submit),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE, border=ft.Border.all(1, BORDER), border_radius=26,
        padding=ft.Padding.only(left=16, right=10, top=10, bottom=10), height=52)

    content = body([
        V(14),
        _context_card(p),
        V(18.2),
        T("TIẾN TRÌNH TRÒ CHUYỆN", 9, 400, PRIMARY, ls=0.9),
        V(8.2),
        stage_holder,
        thread,
    ], bottom=11.5, auto_scroll=True)
    footer = ft.Container(composer, padding=ft.Padding.only(left=24, right=24, top=10, bottom=20.5))
    render()
    app.page.run_task(start)
    return screen(f"/chat/{p.id}", content,
                  top=top_bar("Hỏi Aura", on_back=app.back_handler, trailing="info",
                              on_trailing=lambda e: bottom_sheet(app.page, "AURA hỏi, bạn nhìn", ABOUT)),
                  footer=footer, nav=bottom_nav(1, app.go))
