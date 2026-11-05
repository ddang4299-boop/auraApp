"""Màn Kết quả & cảm nhận."""
from __future__ import annotations

import flet as ft

from ..app import QuizState
from ..data import FEELINGS, NEXT_STORY, PAINTINGS
from ..theme import (BEIGE, BORDER, GOLD, GREEN, GREEN_BG, GREEN_INK, INK, MUTED, PRIMARY, RADIUS,
                     WHITE)
from ..ui import (H, T, V, body, bottom_nav, card, divider, icon, kicker, painting_strip,
                  primary_button, screen, top_bar)
from .quiz import feelings_row

TAKEAWAYS = {
    "arnolfini": [
        "Gương phản chiếu hai người ở phía cửa; một người có thể là van Eyck. Đó là giả thuyết, "
        "không phải bằng chứng xác định danh tính.",
        "Cách diễn giải về “hợp đồng hôn nhân” từng được đề xuất, nhưng không xác nhận đây là "
        "cảnh lễ cưới hay giấy tờ pháp lý.",
    ],
}


def build(app, q, pid: str = "arnolfini") -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS["arnolfini"]
    if q.get("demo") == "1":
        app.state.quizzes[p.id] = QuizState(answers={0: 0, 1: 1}, current=1, phase="graded",
                                            feeling=3)
    st = app.state.quiz(p.id)
    n = len(p.quiz)
    score = sum(1 for i, qq in enumerate(p.quiz) if st.answers.get(i) == qq.correct)
    nxt = PAINTINGS[NEXT_STORY.get(p.id, "madonna-pinks")]
    cw = app.content_width

    badge = "Thám tử thị giác" if n and score == n else "Người quan sát chậm"
    takeaways = TAKEAWAYS.get(p.id) or [p.story]
    paras: list[ft.Control] = []
    for k, t in enumerate(takeaways):
        paras += [V(8 if k == 0 else 10), T(t, 13, 400, INK)]

    score_box = ft.Container(ft.Row([
        T(f"{score}/{n}" if n else "—", 32, 400, GREEN_INK, serif=True, ls=-0.3, lh=1.1),
        H(14),
        ft.Column([
            T("Hai câu trả lời đúng" if (n == 2 and score == 2) else f"{score} câu trả lời đúng",
              13, 600, GREEN_INK),
            V(2.5),
            T("Kết quả phần kiến thức về tác phẩm.", 11, 400, GREEN_INK),
        ], spacing=0, tight=True, expand=True),
    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        height=64, bgcolor=GREEN_BG, border=ft.Border.all(1, GREEN), border_radius=RADIUS,
        padding=ft.Padding.only(left=12, right=12))

    result_card = card(ft.Column([
        ft.Row([
            ft.Container(icon("award", 24, INK), width=52, height=52, border_radius=26, bgcolor=GOLD,
                         alignment=ft.Alignment.CENTER),
            H(12),
            ft.Column([T(badge, 21, serif=True, ls=-0.3), V(4),
                       T("Bạn đã hoàn thành hai câu hỏi" if n == 2 else "Bạn đã hoàn thành phần quiz",
                         11, 400, MUTED)], spacing=0, tight=True, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(17),
        score_box,
        V(13),
        T("Điều bạn vừa nhận ra", 13, 600, INK),
        *paras,
        V(10.5),
        T("Nhìn chi tiết trước, rồi đối chiếu nguồn: điều thấy và điều suy đoán không phải lúc nào "
          "cũng giống nhau.", 11, 400, MUTED),
    ], spacing=0, tight=True), padding=ft.Padding.only(left=16, right=16, top=14, bottom=15))

    feeling = st.feeling
    feeling_title = f"Bạn chọn: {FEELINGS[feeling][1]}" if feeling is not None else "Bạn chưa chọn mức kết nối"
    note_block: list[ft.Control] = []
    if st.note.strip():
        note_block = [V(14), ft.Container(T(f"“{st.note.strip()}”", 13, 400, INK, italic=True),
                                          bgcolor=BEIGE, border_radius=RADIUS, padding=14)]

    img_w = 190
    next_card = card(ft.Column([
        ft.Container(ft.Image(src=nxt.image, width=img_w, height=img_w / nxt.aspect, fit=ft.BoxFit.COVER),
                     bgcolor=BEIGE, alignment=ft.Alignment.CENTER,
                     padding=ft.Padding.symmetric(vertical=17)),
        ft.Container(ft.Column([
            T(nxt.title, 21, serif=True, ls=-0.3), V(8),
            T(f"{nxt.artist} · {nxt.year}", 11, 400, MUTED), V(6),
            T(nxt.teaser, 11, 400, MUTED),
        ], spacing=0, tight=True), padding=ft.Padding.only(left=12, right=12, top=9, bottom=12.5)),
    ], spacing=0, tight=True), on_click=lambda e: app.go(f"/painting/{nxt.id}"))

    content = body([
        V(23.5),
        kicker("Sau cuộc trò chuyện cùng AURA"),
        V(8),
        T("Nhìn kỹ hơn, hiểu thêm một chút.", 27, serif=True),
        V(14),
        T("Cảm ơn bạn đã dành thời gian nhìn chậm và đặt câu hỏi cùng AURA.", 14, 400, MUTED),
        V(25.5),
        painting_strip(p, on_click=lambda e: app.go(f"/painting/{p.id}")),
        V(24.5),
        result_card,
        V(22.5),
        kicker("Cảm nhận của riêng bạn"),
        V(7.5),
        T(feeling_title, 23, serif=True),
        V(13),
        feelings_row(feeling),
        *note_block,
        V(12),
        T("Bạn tự chọn theo cảm nhận lúc này; phần này không tính vào kết quả quiz. Cảm nhận không "
          "có đúng hay sai.", 11, 400, MUTED),
        V(25),
        divider(),
        V(20),
        T("Một câu chuyện tiếp theo", 23, serif=True),
        V(15.5),
        next_card,
        V(12.5),
        primary_button("Khám phá bức tiếp theo", lambda e: app.go(f"/painting/{nxt.id}"), pill=True),
        V(11),
        ft.Container(T(f"Thông tin & ảnh: {nxt.museum} ↗", 11, 400, MUTED),
                     on_click=lambda e: app.open_url(nxt.url)),
    ], bottom=25)
    return screen(f"/result/{p.id}", content,
                  top=top_bar("Kết quả & cảm nhận", on_back=app.back_handler),
                  nav=bottom_nav(1, app.go))
