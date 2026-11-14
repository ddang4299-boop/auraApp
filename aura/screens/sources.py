"""Màn Tư liệu: kho tư liệu AURA dựa vào khi trả lời về một bức tranh.

Chatbot trả lời theo kiểu RAG: tìm trong các thẻ tư liệu của kịch bản (Chatbot/scripts/*.json) rồi mới
trả lời. Màn này cho người xem thấy chính các thẻ đó, để biết câu trả lời của AURA dựa trên đâu."""
from __future__ import annotations

import flet as ft

from ..data import DEFAULT_ID, PAINTINGS
from ..socratic import Info
from ..theme import INK, MUTED, PRIMARY, TINT
from ..ui import (H, NAV_PAINTING, T, V, body, glass, icon, kicker, nav_bar, primary_button, screen,
                  source_line, top_bar)


def _card(n: int, info: Info) -> ft.Control:
    """Một thẻ tư liệu: số thứ tự, chủ đề (chữ có chân), nội dung."""
    return glass(ft.Column([
        ft.Row([
            ft.Container(T(f"{n:02d}", 10, 600, PRIMARY, lh=1.0), width=28, height=22, border_radius=11,
                         bgcolor=TINT, alignment=ft.Alignment.CENTER),
            H(10),
            T(info.topic, 17, 400, INK, serif=True, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        V(8),
        T(info.text, 13, 400, INK),
    ], spacing=0, tight=True), radius=14, padding=ft.Padding.only(left=14, right=14, top=12, bottom=14))


def build(app, q, pid: str = DEFAULT_ID) -> ft.View:
    p = PAINTINGS.get(pid) or PAINTINGS[DEFAULT_ID]
    get = getattr(app.engine, "knowledge", None)
    try:
        infos = list(get(p)) if get else []
    except Exception as e:                 # kịch bản lỗi: vẫn mở được màn, dùng phần giới thiệu của tranh
        print(f"[sources] Không đọc được tư liệu: {e}")
        infos = []
    if not infos:
        infos = [Info("Chuyện phía sau", p.story)]
    cards: list[ft.Control] = []
    for k, info in enumerate(infos):
        cards += [V(10) if k else V(0), _card(k + 1, info)]
    content = body([
        V(20),
        kicker("Kho tư liệu của AURA", ls=1.0),
        V(6),
        T(p.title, 29, serif=True),
        V(8),
        T(f"{len(infos)} thẻ tư liệu AURA tra cứu trước khi trả lời bạn về bức tranh này.", 14, 400, MUTED),
        V(16),
        glass(ft.Row([
            icon("info", 18, PRIMARY), H(10),
            T("Câu nào AURA phải trả lời ngoài các thẻ này, khung trả lời sẽ ghi rõ "
              "“AI trả lời · Kiến thức chung” để bạn biết nguồn.", 12, 400, INK, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            radius=12, padding=ft.Padding.only(left=14, right=14, top=12, bottom=12)),
        V(20),
        *cards,
        V(18),
        source_line(f"Thông tin & ảnh: {p.museum} ↗", lambda e: app.open_url(p.url)),
        V(16),
        primary_button("Hỏi AURA về bức tranh này", lambda e: app.go(f"/chat/{p.id}"),
                       leading="message-circle"),
    ], bottom=24)
    return screen(f"/sources/{p.id}", content, top=top_bar("Tư liệu", on_back=app.back_handler),
                  nav=nav_bar(app, NAV_PAINTING))
