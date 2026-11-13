"""Màn Hỏi Aura — đối thoại Socrates quanh một bức tranh."""
from __future__ import annotations

import asyncio
import math
import re
import time

import flet as ft

from ..data import DEFAULT_ID, PAINTINGS, Painting
from ..socratic import STAGES, AuraTurn, Choice, Info, Message
from ..theme import (BORDER, GLASS, GLASS_EDGE, GLASS_LINE, INK, MUTED, PRIMARY, SHADOW_INK, TINT,
                     WHITE, WIDE_W, WINE_LIGHT)
from ..ui import (H, T, V, body, bottom_nav, bottom_sheet, cropped_image, glass, icon, logo, screen,
                  source_line, surface_field, top_bar, zoom_badge)
from .viewer import gallery_wall, open_viewer

INFO_BG = "#F3EADB,0.86"     # thẻ tư liệu: be ấm, hơi đậm hơn bong bóng AURA

ABOUT = ("AURA không đưa ra đáp án ngay. Theo phương pháp Socrates, AURA đặt câu hỏi để bạn tự "
         "quan sát, tách điều nhìn thấy khỏi điều suy đoán, rồi đối chiếu với nguồn của bảo tàng. "
         "Cuộc trò chuyện đi qua bốn chặng: Ấn tượng đầu → Tách chi tiết → Đối thoại → Mở rộng.")


def _painting_button(app, p: Painting) -> ft.Control:
    """Ảnh tranh nhỏ cạnh ô nhập: chạm để xem tranh (phóng to được) mà không phải cuộn lên đầu."""
    thumb = ft.Container(
        ft.Image(src=p.image, width=28, height=36, fit=ft.BoxFit.COVER),
        width=28, height=36, border_radius=4, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border=ft.Border.all(1, BORDER), left=0, top=0)
    # kính lúp nhỏ ở góc: báo ảnh này mở ra phóng to được
    return ft.Container(ft.Stack([thumb, zoom_badge(17, right=0, bottom=0)], width=35, height=43),
                        width=35, height=43, tooltip="Xem tranh (phóng to được)",
                        on_click=lambda e: open_viewer(app, p))


def _context_card(app, p: Painting) -> ft.Control:
    """Thẻ kính "Đang cùng khám phá": ảnh tranh có khung + tên tranh (chữ có chân)."""
    return glass(ft.Row([
        ft.Container(ft.Image(src=p.image, width=40, height=54, fit=ft.BoxFit.COVER),
                     border=ft.Border.all(2, WHITE), border_radius=3,
                     clip_behavior=ft.ClipBehavior.HARD_EDGE,
                     shadow=[ft.BoxShadow(blur_radius=8, offset=ft.Offset(0, 2),
                                          color=f"{SHADOW_INK},0.18")]),
        H(16),
        ft.Column([
            T("ĐANG CÙNG KHÁM PHÁ", 9, 600, PRIMARY, ls=1.0),
            V(3),
            T(p.title, 18, 400, INK, serif=True, max_lines=1),
            V(2),
            T(f"{p.artist} · {p.year} · {p.museum}", 10, 400, MUTED, max_lines=1),
        ], spacing=0, tight=True, expand=True),
        H(8), zoom_badge(30),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        radius=14, padding=ft.Padding.only(left=14, right=14, top=10, bottom=10),
        on_click=lambda e: open_viewer(app, p))


def _stage_chips(stage: int) -> ft.Row:
    chips = []
    for i, name in enumerate(STAGES):
        on = i <= stage
        chips.append(ft.Container(
            T(name, 10, 600, WHITE if on else PRIMARY, no_wrap=True, lh=1.2),
            padding=ft.Padding.symmetric(horizontal=8, vertical=7.5), border_radius=14,
            bgcolor=PRIMARY if on else GLASS, border=None if on else ft.Border.all(1, GLASS_EDGE),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)))
    return ft.Row(chips, spacing=4, wrap=True, run_spacing=4)


def _aura_header() -> ft.Control:
    return ft.Row([logo(21), H(12),
                   ft.Container(T("Cùng bạn nhìn tranh", 10, 400, MUTED, lh=1.0),
                                padding=ft.Padding.only(top=4))],
                  spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _user_bubble(text: str, max_w: float) -> ft.Control:
    """Bong bóng người dùng: nền đỏ rượu chuyển sắc, bên phải. Bề rộng ước theo độ dài chữ
    để câu ngắn ("Có") không bị kéo thành bong bóng to."""
    longest = max((len(x) for x in text.splitlines()), default=0)
    w = max(64.0, min(max_w, 34 + longest * 7.4))
    return ft.Row([
        ft.Container(
            T(text, 14, 400, WHITE), width=w,
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                       colors=[WINE_LIGHT, PRIMARY]),
            padding=ft.Padding.only(left=15, right=13, top=11, bottom=12),
            border_radius=ft.BorderRadius.only(top_left=18, top_right=18, bottom_left=18,
                                               bottom_right=4),
        )], alignment=ft.MainAxisAlignment.END)


def _choice(c: Choice, *, picked: bool, enabled: bool, on_click) -> ft.Control:
    return ft.Container(ft.Row([
        T(c.label, 12, 500, PRIMARY, expand=True, lh=1.3),
        H(12), icon("arrow-up-right", 16, PRIMARY),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=TINT if picked else GLASS, border=ft.Border.all(1, GLASS_LINE if picked else GLASS_EDGE),
        border_radius=23, padding=ft.Padding.only(left=14, right=16, top=9, bottom=9),
        on_click=on_click if enabled else None, ink=enabled,      # gợn sóng khi chạm
        opacity=1.0 if (enabled or picked) else 0.5,
        animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT))


def _info_card(info: Info) -> ft.Control:
    """Thẻ tư liệu AURA tra được trong kho tư liệu của tranh: nhãn, chủ đề (chữ có chân), nội dung."""
    return ft.Container(ft.Column([
        ft.Row([icon("message-circle" if info.general else "book-open", 13, PRIMARY), H(6),
                T("AI TRẢ LỜI · KIẾN THỨC CHUNG" if info.general else "TƯ LIỆU", 9, 600, PRIMARY, ls=1.1)],
               spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(6),
        T(info.topic, 16, 400, INK, serif=True),
        V(5),
        T(info.text, 13, 400, INK),
    ], spacing=0, tight=True), bgcolor=INFO_BG, border=ft.Border.all(1, GLASS_EDGE),
        border_radius=12, padding=ft.Padding.only(left=14, right=14, top=11, bottom=13))


def _detail_card(app, p: Painting, att) -> ft.Control:
    w = app.content_width - 18
    return glass(ft.Column([
        T(att.label.upper(), 9, 600, PRIMARY, ls=0.9),
        V(7),
        cropped_image(p.image, p.aspect, w - 2, 180, att.crop, radius=6,
                      overlays=[zoom_badge(28, right=8, top=8)],
                      on_click=lambda e: app.go(f"/detail/{p.id}/{att.detail_key}")),
        V(8),
        ft.Container(ft.Row([T("Xem toàn bộ chi tiết", 11, 600, PRIMARY), H(12),
                             icon("arrow-up-right", 16, PRIMARY)], spacing=0, tight=True),
                     bgcolor=TINT, height=30, border_radius=15,
                     padding=ft.Padding.only(left=12, right=12), alignment=ft.Alignment.CENTER_LEFT,
                     on_click=lambda e: app.go(f"/detail/{p.id}/{att.detail_key}")),
    ], spacing=0, tight=True), radius=14, padding=ft.Padding.only(left=8, right=8, top=10, bottom=10))


def _summary_card(app, p: Painting, s) -> ft.Control:
    return glass(ft.Column([
        T(s.title, 18, 400, INK, serif=True),
        V(7.5),
        T(s.text, 13, 400, INK),
        V(12),
        ft.Container(ft.Row([T(s.action, 13, 600, WHITE), ft.Container(expand=True),
                             icon("arrow-up-right", 18, WHITE)], spacing=0),
                     height=40, bgcolor=PRIMARY, border_radius=20,
                     padding=ft.Padding.only(left=16, right=19), alignment=ft.Alignment.CENTER_LEFT,
                     on_click=lambda e: app.go(f"/quiz/{p.id}")),
    ], spacing=0, tight=True), radius=14, padding=ft.Padding.only(left=14, right=14, top=12, bottom=14),
        shadow=True)


MIN_THINK = 0.6          # giây: "đang suy nghĩ" hiện đủ lâu để không chớp tắt
DOT = 6
# Hiệu ứng "đang gõ": mỗi lần hiện thêm chữ là một lần gửi cập nhật từ Python sang màn hình.
# Khi app chạy trên máy chủ (Render), gửi quá dày sẽ nghẽn mạng/CPU -> giới hạn ~14 lần mỗi đoạn.
TYPE_TICK = 0.09         # giây giữa hai lần hiện thêm chữ (mỗi lần là một lượt gửi xuống trình duyệt)
TYPE_PARA_MAX = 0.85     # một đoạn dài cỡ nào cũng gõ xong trong khoảng chừng này giây
WORD_RE = re.compile(r"\S+\s*")


# Trạng thái đang xử lý. Thanh chạy là hiệu ứng của Flutter (chạy trên máy người xem, không tốn
# máy chủ); dòng chữ chỉ đổi vài lần theo đúng các bước AURA đang làm.
THINK_LABELS = [(0, "ĐANG PHÂN TÍCH CÂU TRẢ LỜI CỦA BẠN"),
                (1.2, "ĐANG TRUY XUẤT TƯ LIỆU VỀ TÁC PHẨM"),
                (3.5, "ĐANG SOẠN CÂU HỎI TIẾP THEO"),
                (8, "SẮP XONG RỒI")]


def _thinking() -> tuple[ft.Control, ft.Text]:
    """Khung kính nhỏ: nhãn trạng thái + thanh tiến trình mảnh màu đỏ rượu."""
    label = T(THINK_LABELS[0][1], 9.5, 600, PRIMARY, ls=1.0, lh=1.2)
    bar = ft.Container(ft.ProgressBar(bar_height=2.5, color=PRIMARY, bgcolor=TINT, border_radius=2),
                       width=210)
    box = glass(ft.Column([ft.Row([logo(12), H(10), label], spacing=0,
                                  vertical_alignment=ft.CrossAxisAlignment.CENTER),
                           V(9), bar], spacing=0, tight=True),
                radius=14, padding=ft.Padding.only(left=14, right=16, top=11, bottom=12))
    return ft.Row([box], spacing=0), label


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
    think_row, think_label = _thinking()
    cw = app.content_width
    think_box = ft.Container(ft.Column([V(16), think_row], spacing=0, tight=True),
                             visible=st.thinking)
    # Mỗi tin nhắn là một khối riêng: tin mới chỉ THÊM khối mới, không vẽ lại cả cuộc trò chuyện.
    thread = ft.Column([think_box], spacing=0, tight=True,
                       horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    blocks: dict[int, ft.Container] = {}
    # Hiệu ứng gõ chữ: tin AURA mới hiện từng cụm từ; thẻ tư liệu hiện khi gõ tới chỗ của nó;
    # nút gợi ý/ảnh chi tiết hiện sau khi gõ xong.
    # i -> (các đoạn chữ, khối phần phụ, khối thẻ tư liệu)
    typing: dict[int, tuple[list[ft.Text], ft.Container, ft.Container | None]] = {}
    fade_in: set[int] = set()

    def last_aura() -> int:
        return max((i for i, m in enumerate(st.messages) if m.role == "aura"), default=-1)

    def block_controls(i: int) -> ft.Column:
        m = st.messages[i]
        prev = st.messages[i - 1].role if i else None
        if m.role == "user":
            items = [V(14 if prev == "aura" else 9), _user_bubble(m.text, cw * 0.82)]
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
        """Đổi dòng trạng thái theo thời gian chờ. Chỉ gửi cập nhật khi chữ đổi (vài lần mỗi lượt),
        thanh chạy thì Flutter tự vẽ."""
        t0, shown = time.monotonic(), THINK_LABELS[0][1]
        think_label.value = shown
        while st.thinking and think_box.visible:
            waited = time.monotonic() - t0
            label = [s for after, s in THINK_LABELS if waited >= after][-1]
            if label != shown:
                shown = think_label.value = label
                try:
                    think_label.update()
                except Exception:
                    return
            await asyncio.sleep(0.25)

    def set_thinking(on: bool) -> None:
        st.thinking = on
        think_box.visible = on

    def _aura_block(i: int, m: Message, interactive: bool, header: bool) -> list[ft.Control]:
        t: AuraTurn = m.turn
        typed = i in typing
        # Tên "AURA" chỉ giới thiệu một lần ở tin nhắn đầu, các lượt sau không lặp lại.
        out: list[ft.Control] = [_aura_header(), V(10.3)] if header else []
        inner: list[ft.Control] = []
        texts: list[ft.Text] = []
        info_box = None
        if t.infos:
            cards: list[ft.Control] = []
            for k, info in enumerate(t.infos):
                cards += [V(8) if k else V(0), _info_card(info)]
            info_box = ft.Container(ft.Column(cards, spacing=0, tight=True,
                                              horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                                    visible=not typed, opacity=0 if typed else 1,
                                    animate_opacity=ft.Animation(360, ft.AnimationCurve.EASE_OUT))
        last = len(t.paragraphs) - 1
        for k, para in enumerate(t.paragraphs):
            if t.infos and k == t.info_at:
                inner += [V(10) if inner else V(0), info_box, V(12)]
            elif k:
                inner.append(V(9))
            # Câu hỏi gợi mở (đoạn cuối, khi cuộc trò chuyện chưa kết thúc) nổi bật màu đỏ rượu.
            question = k == last and not t.done and para.rstrip().endswith("?")
            texts.append(T("" if typed else para, 14, 500 if question else 400,
                           PRIMARY if question else INK))
            inner.append(texts[-1])
        if t.infos and t.info_at >= len(t.paragraphs):
            inner += [V(10) if inner else V(0), info_box]
        bubble = glass(ft.Column(inner, spacing=0, tight=True,
                                 horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                       radius=18, padding=ft.Padding.only(left=15, right=15, top=13, bottom=14),
                       margin=ft.Margin.only(right=18))
        bubble.border_radius = ft.BorderRadius.only(top_left=4, top_right=18, bottom_left=18,
                                                    bottom_right=18)
        # Phần phụ (ảnh chi tiết, nút gợi ý, thẻ tổng kết, nguồn) gom vào một khối để hiện sau chữ.
        extras = _aura_extras(i, t, interactive)
        box = ft.Container(ft.Column(extras, spacing=0, tight=True,
                                     horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                           visible=not typed, opacity=0 if i in fade_in else 1,
                           animate_opacity=ft.Animation(320, ft.AnimationCurve.EASE_OUT))
        if typed:
            typing[i] = (texts, box, info_box)
        return out + [bubble, box]

    async def type_out(i: int) -> None:
        """Hiện chữ của tin AURA thứ i dần dần theo từng cụm từ, như đang gõ."""
        texts, box, info_box = typing[i]
        turn = st.messages[i].turn
        for k, (txt, para) in enumerate(zip(texts, turn.paragraphs)):
            if info_box is not None and k == turn.info_at:
                if not await show_info(info_box):
                    return
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
        if info_box is not None and turn.info_at >= len(turn.paragraphs):
            if not await show_info(info_box):
                return
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

    async def show_info(info_box: ft.Container) -> bool:
        """Thẻ tư liệu hiện ra mờ -> rõ (hiệu ứng chạy trên máy người xem)."""
        info_box.visible = True
        try:
            info_box.update()
            await asyncio.sleep(0.03)
            info_box.opacity = 1
            info_box.update()
        except Exception:
            return False
        await asyncio.sleep(0.35)
        return True

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
        if not text:
            return
        if st.thinking:
            if msg_index is not None:      # bấm nút gợi ý cũ lúc đang bận: bỏ qua
                return
            # Gõ tin khi AURA đang trả lời: xếp hàng, gửi ngay khi AURA xong (không làm mất tin).
            waited = 0.0
            while st.thinking and waited < 30:
                await asyncio.sleep(0.1)
                waited += 0.1
            if st.thinking:
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
        typing[i] = ([], ft.Container(), None)
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
    composer = glass(ft.Row([
        _painting_button(app, p), H(10),
        field, H(10),
        ft.Container(icon("arrow-up", 16, WHITE), width=32, height=32, border_radius=16,
                     gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                                colors=[WINE_LIGHT, PRIMARY]),
                     alignment=ft.Alignment.CENTER, on_click=submit),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        strong=True, shadow=True, radius=26,
        padding=ft.Padding.only(left=10, right=10, top=8, bottom=8), height=54)

    content = body([
        V(14),
        _context_card(app, p),
        V(18.2),
        T("TIẾN TRÌNH TRÒ CHUYỆN", 9, 600, PRIMARY, ls=1.0),
        V(8.2),
        stage_holder,
        thread,
    ], bottom=11.5, ref=scroller)          # tự cuộn bằng scroll_to (mượt) thay cho auto_scroll
    footer = ft.Container(composer, padding=ft.Padding.only(left=24, right=24, top=10, bottom=20.5))
    sync(animate=False)                    # tin nhắn cũ (khi quay lại màn chat) hiện ngay
    app.page.run_task(start)
    # Máy tính / màn hình rộng: tranh lớn treo bên trái (phóng to được), cuộc trò chuyện bên phải.
    aside = gallery_wall(app, p) if app.page_width >= WIDE_W else None
    return screen(f"/chat/{p.id}", content,
                  top=top_bar("Hỏi Aura", on_back=app.back_handler, trailing="info",
                              on_trailing=lambda e: bottom_sheet(app.page, "AURA hỏi, bạn nhìn", ABOUT)),
                  footer=footer, nav=bottom_nav(1, app.go), aside=aside)
