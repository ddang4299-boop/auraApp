"""Màn Quiz & cảm nhận sau cuộc trò chuyện."""
from __future__ import annotations

import math

import flet as ft

from ..app import QuizState
from ..data import DEFAULT_ID, FEELINGS, PAINTINGS, Painting, QuizQuestion
from ..theme import (BEIGE, BORDER, GOLD, GREEN, GREEN_BG, GREEN_INK, INK, MUTED, PRIMARY, RADIUS,
                     RED, SURFACE, TINT, WHITE, WHY_BG, WHY_BORDER, WHY_INK)
from ..ui import (H, T, V, body, bottom_nav, cropped_image, divider, icon, kicker,
                  painting_strip, primary_button, screen, surface_field, text_link, top_bar)

# (x, y, rộng, cao, góc, màu) — mảnh giấy hoa trang trí khi làm đúng hết
CONFETTI = [
    (32, 8, 8, 7, 0.3, GOLD), (54, 15, 6, 6, 0.2, PRIMARY), (68, 21, 5, 5, 0, "#5B8DEF"),
    (77, 6, 9, 4, 0.6, GREEN), (104, 18, 7, 7, 0, "#5B8DEF"), (128, 3, 9, 4, -0.4, GOLD),
    (142, 22, 4, 4, 0, PRIMARY), (151, 13, 6, 6, 0.5, PRIMARY), (178, 5, 8, 8, -0.2, GREEN),
    (203, 16, 8, 5, 0.8, "#E07060"), (215, 25, 6, 6, 0, GOLD), (225, 7, 9, 4, 0.3, "#5B8DEF"),
    (250, 14, 7, 7, 0, GOLD), (273, 4, 7, 9, -0.2, PRIMARY), (286, 22, 5, 5, 0, GREEN),
    (293, 17, 9, 4, 0.5, GREEN), (318, 3, 8, 6, 0.3, "#E07060"), (339, 12, 8, 4, 0.2, "#5B8DEF"),
    (348, 6, 8, 6, 0.7, GREEN), (361, 17, 6, 6, 0.3, GOLD), (363, 25, 4, 4, 0, "#E07060"),
]


def confetti(width: float) -> ft.Control:
    scale = width / 402
    pieces = [ft.Container(left=(x - 24) * scale + 24 * scale, top=y, width=w, height=h,
                           bgcolor=c, border_radius=min(w, h) / 2 if w == h and w <= 6 else 1.5,
                           rotate=ft.Rotate(a))
              for x, y, w, h, a, c in CONFETTI]
    return ft.Stack(pieces, height=34)


def _radio(kind: str) -> ft.Control:
    """kind: none | correct | wrong."""
    if kind == "correct":
        return ft.Container(icon("check", 12, WHITE), width=18, height=18, border_radius=9,
                            bgcolor=GREEN, alignment=ft.Alignment.CENTER)
    if kind == "wrong":
        return ft.Container(icon("x", 11, WHITE), width=18, height=18, border_radius=9,
                            bgcolor=RED, alignment=ft.Alignment.CENTER)
    return ft.Container(width=18, height=18, border_radius=9, border=ft.Border.all(1.5, MUTED))


def _option(text: str, kind: str, on_click=None) -> ft.Control:
    colors = {"correct": (GREEN_BG, GREEN, GREEN_INK), "wrong": (TINT, RED, INK),
              "none": (None, BORDER, INK)}
    bg, border, fg = colors[kind]
    trailing: list[ft.Control] = []
    if kind == "correct":
        trailing = [H(12), ft.Container(T("Đúng", 9, 600, WHITE, lh=1.0), bgcolor=GREEN, height=15,
                                        padding=ft.Padding.symmetric(horizontal=8), border_radius=8,
                                        alignment=ft.Alignment.CENTER)]
    return ft.Container(ft.Row([
        _radio(kind), H(12),
        T(text, 13, 500 if kind == "correct" else 400, fg, expand=True),
        *trailing,
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=bg, border=ft.Border.all(1, border), border_radius=RADIUS,
        padding=ft.Padding.only(left=14, right=12, top=12.5, bottom=12.5), on_click=on_click)


def _why(app, p: Painting, qq: QuizQuestion, extra: list[str] = ()) -> ft.Control:
    w = app.content_width - 26
    items: list[ft.Control] = [ft.Row([T("🔍", 13, lh=1.2), H(7), T("Vì sao?", 13, 600, GREEN_INK)],
                                      spacing=0)]
    if qq.why_crop:
        items += [V(5.5), cropped_image(p.image, p.aspect, w, 180, qq.why_crop, radius=4)]
    for k, para in enumerate(list(qq.why) + list(extra)):
        items += [V(6.5 if k == 0 else 8), T(para, 12, 400, WHY_INK, lh=1.58)]
    items += [V(8), ft.Container(T(qq.source, 10, 400, MUTED, italic=True),
                                 on_click=lambda e: app.open_url(p.url))]
    return ft.Container(ft.Column(items, spacing=0, tight=True), bgcolor=WHY_BG,
                        border=ft.Border.all(1, WHY_BORDER), border_radius=RADIUS,
                        padding=ft.Padding.only(left=14, right=10, top=9, bottom=14.5))


def _bar(label: str, color: str, bar_color: str, fill: float) -> ft.Control:
    """Nhãn câu hỏi + thanh tiến độ mảnh."""
    done = max(0, min(1000, int(fill * 1000)))
    segs = []
    if done:
        segs.append(ft.Container(height=3, bgcolor=bar_color, expand=done, border_radius=2))
    if done < 1000:
        segs.append(ft.Container(height=3, bgcolor=BORDER, expand=1000 - done, border_radius=2))
    return ft.Container(ft.Row([
        T(label, 10, 600, color, no_wrap=True), H(10),
        ft.Row(segs, spacing=0, expand=True),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.only(left=10, right=20))


def feelings_row(selected: int | None, on_pick=None, two_line: bool = False) -> ft.Control:
    cols = []
    for i, (emoji, label) in enumerate(FEELINGS):
        on = i == selected
        cols.append(ft.Container(ft.Column([
            ft.Container(T(emoji, 26, lh=1.0), width=52, height=52, border_radius=26,
                         bgcolor=TINT if on else BEIGE,
                         border=ft.Border.all(2, PRIMARY) if on else None,
                         alignment=ft.Alignment.CENTER),
            V(5.5),
            T(label, 10, 600 if on else 400, PRIMARY if on else MUTED, lh=1.4,
              align=ft.TextAlign.CENTER),
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, on_click=(lambda e, i=i: on_pick(i)) if on_pick else None))
    return ft.Row(cols, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)


def _question_block(app, p: Painting, st: QuizState, i: int, qq: QuizQuestion, n: int,
                    pick) -> list[ft.Control]:
    cw = app.content_width
    ans = st.answers.get(i)
    graded = ans is not None
    retry = st.phase == "retry" and st.current == i
    if graded and ans == qq.correct:
        label, color, bar_c, fill = f"Câu {i + 1}/{n} · Trả lời đúng ✓", GREEN, GREEN, (i + 1) / n
    elif retry:
        label, color, bar_c, fill = f"Câu {i + 1}/{n} · Thử lại", RED, PRIMARY, (i + 0.8) / n
    elif graded:
        label, color, bar_c, fill = f"Câu {i + 1}/{n} · Chưa đúng", RED, RED, (i + 1) / n
    else:
        label, color, bar_c, fill = f"Câu {i + 1}/{n}", PRIMARY, PRIMARY, (i + 0.15) / n
    out: list[ft.Control] = [
        ft.Row([
            ft.Container(T(f"{i + 1:02d}", 19, 400, PRIMARY, serif=True, ls=0, lh=1.1),
                         padding=ft.Padding.only(top=1)),
            H(10),
            T(qq.text, 14, 600, INK, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        V(14),
        _bar(label, color, bar_c, fill),
        V(15),
    ]
    for k, opt in enumerate(qq.options):
        if k:
            out.append(V(9))
        if graded and k == qq.correct:
            kind = "correct"
        elif graded and k == ans:
            kind = "wrong"
        else:
            kind = "none"
        out.append(_option(opt, kind, on_click=None if graded else (lambda e, k=k: pick(i, k))))
    if retry:
        hint = "Chưa đúng lần này. Cùng nhìn kỹ chiếc gương nhé." if qq.why_crop else \
            "Chưa đúng lần này. Cùng đọc lại gợi ý nhé."
        out += [V(13.5), T(hint, 12, 400, PRIMARY)]
        out += [V(13.5), _why(app, p, qq)]
    elif graded:
        out += [V(13), _why(app, p, qq)]
    return out


def build(app, q, pid: str = DEFAULT_ID) -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS[DEFAULT_ID]
    demo = q.get("demo")
    if demo == "graded":
        app.state.quizzes[p.id] = QuizState(answers={0: 0, 1: 1}, current=1, phase="graded",
                                            feeling=3)
    elif demo == "retry":
        app.state.quizzes[p.id] = QuizState(answers={0: 1}, current=0, phase="retry")
    st = app.state.quiz(p.id)
    if not p.quiz:
        st.phase = "graded"
    n = len(p.quiz)
    holder = ft.Column(spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    note_field = ft.TextField(value=st.note, multiline=True, min_lines=3, max_lines=6,
                              hint_text="Một nếp vải, một cử chỉ, hay một điều bạn vừa nhận ra…",
                              text_style=ft.TextStyle(size=13, color=INK, font_family="Inter",
                                                      height=1.54, letter_spacing=0),
                              hint_style=ft.TextStyle(size=13, color=MUTED, font_family="Inter",
                                                      height=1.54, letter_spacing=0),
                              on_change=lambda e: setattr(st, "note", e.control.value or ""),
                              **surface_field())

    def pick(i: int, k: int):
        st.answers[i] = k
        if k == p.quiz[i].correct:
            if i + 1 < n:
                st.current, st.phase = i + 1, "answering"
            else:
                st.phase = "graded"
        else:
            st.current, st.phase = i, "retry"
        render()

    def retry(e=None):
        st.answers.pop(st.current, None)
        st.phase = "answering"
        render()

    def skip(e=None):
        if st.current + 1 < n:
            st.current, st.phase = st.current + 1, "answering"
        else:
            st.phase = "graded"
        render()

    def pick_feeling(i: int):
        st.feeling = i
        render()

    def finish(send_feeling: bool):
        if not send_feeling:
            st.note = ""
        app.go(f"/result/{p.id}")

    def render(update: bool = True):
        items: list[ft.Control] = []
        score = sum(1 for i, qq in enumerate(p.quiz) if st.answers.get(i) == qq.correct)
        if st.phase == "graded" and n:
            perfect = score == n
            items += [V(16), confetti(app.content_width) if perfect else V(34), V(24.5),
                      ft.Container(ft.Row([
                          ft.Container(icon("check", 16, WHITE), width=32, height=32,
                                       border_radius=16, bgcolor=GREEN, alignment=ft.Alignment.CENTER),
                          H(8),
                          ft.Column([
                              T(f"{'Xuất sắc! ' if perfect else ''}Bạn đúng {score}/{n} câu.", 17, 400,
                                GREEN_INK, serif=True, ls=0),
                              V(3),
                              T("Cả hai lựa chọn đều phản ánh đúng những gì nhà nghiên cứu từng ghi nhận."
                                if perfect else "Xem lại phần “Vì sao?” để hiểu thêm từng chi tiết.",
                                11, 400, GREEN_INK),
                          ], spacing=0, tight=True, expand=True),
                      ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                          bgcolor=GREEN_BG, border=ft.Border.all(1, GREEN), border_radius=RADIUS,
                          padding=ft.Padding.only(left=16, right=14, top=11, bottom=12))]
            items += [V(22)]
            sub = "Chọn 1 đáp án mỗi câu · Đã chấm điểm"
        else:
            items += [V(21.5)]
            sub = "Chọn 1 đáp án mỗi câu" + (" · Thử lại câu đầu" if st.phase == "retry" and st.current == 0
                                             else "")
        if n:
            graded_view = st.phase == "graded"
            items += [kicker("01 · Điều bạn vừa khám phá"), V(4.5 if graded_view else 11),
                      T(sub, 11, 400, MUTED), V(23.5 if graded_view else 16)]
            shown = range(n) if st.phase == "graded" else [st.current]
            for j, i in enumerate(shown):
                if j:
                    items.append(V(23.5))
                items += _question_block(app, p, st, i, p.quiz[i], n, pick)
        else:
            items += [kicker("01 · Điều bạn vừa khám phá"), V(8),
                      T("Quiz cho tác phẩm này đang được biên soạn. Bạn vẫn có thể chia sẻ cảm "
                        "nhận bên dưới.", 13, 400, MUTED)]
        if st.phase == "retry":
            nxt = f"Tiếp tục câu {st.current + 2}" if st.current + 1 < n else "Xem kết quả"
            items += [V(25), primary_button("Thử lại câu này", retry, pill=True), V(15.5),
                      text_link(nxt, skip)]
        elif st.phase == "graded":
            items += [V(23.5),
                      ft.Container(T(f"Dựa trên cuộc trò chuyện và {p.museum} ↗", 10, 400, MUTED),
                                   on_click=lambda e: app.open_url(p.url)),
                      V(26), divider(), V(21),
                      kicker("02 · Cảm nhận của riêng bạn"), V(6.5),
                      T("Sau cuộc trò chuyện, bạn cảm thấy thế nào?", 23, serif=True), V(11.5),
                      T("Cảm nhận không có đúng hay sai.", 13, 400, PRIMARY), V(20),
                      T("Mức độ kết nối với tác phẩm · Chọn 1 mức", 13, 400, MUTED), V(13),
                      feelings_row(st.feeling, pick_feeling), V(12),
                      T("Bạn tự chọn theo cảm nhận lúc này; phần này không tính vào kết quả quiz.",
                        11, 400, MUTED), V(19.5),
                      T("Chi tiết nào khiến bạn đổi góc nhìn?", 13, 500, INK), V(7),
                      T("Không bắt buộc", 10, 400, MUTED), V(8),
                      ft.Container(note_field, height=87, bgcolor=SURFACE, border=ft.Border.all(1, BORDER),
                                   border_radius=RADIUS, padding=ft.Padding.only(left=14, right=14, top=12,
                                                                                 bottom=8)),
                      V(20.5),
                      primary_button("Xem kết quả & gửi cảm nhận", lambda e: finish(True), pill=True,
                                     trailing_arrow=True, size=13, padding_h=18),
                      V(15.5),
                      text_link("Chỉ xem kết quả, bỏ qua cảm nhận", lambda e: finish(False))]
        holder.controls = items
        if update:
            app.page.update()

    render(update=False)
    content = body([
        V(23.5),
        kicker("Sau cuộc trò chuyện cùng AURA"),
        V(8),
        T("Nhìn lại, hiểu thêm.", 27, serif=True),
        V(14),
        T("Hai câu hỏi nhỏ để nhìn lại điều vừa khám phá, rồi dành một chút cho cảm nhận của bạn.",
          14, 400, MUTED),
        V(25.5),
        painting_strip(p, on_click=lambda e: app.go(f"/painting/{p.id}")),
        holder,
    ], bottom=35)
    return screen(f"/quiz/{p.id}", content, top=top_bar("Quiz & cảm nhận", on_back=app.back_handler),
                  nav=bottom_nav(1, app.go))
