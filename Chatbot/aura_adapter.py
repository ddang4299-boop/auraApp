"""
Adapter nối Engine với giao diện AURA (AuraTurn / Choice). Không cần sửa màn hình nào.

    adapter = AuraAdapter(hub, turn_cls=AuraTurn, choice_cls=Choice)   # truyền class của app
    turn = adapter.start("mona_lisa")        # -> AuraTurn
    turn = await adapter.reply("...")        # async; chạy engine trong thread để UI không đứng

reply() nhận: chuỗi gõ tay, hoặc chữ của 1 câu hỏi gợi ý (bấm chip) -> tự nhận ra là chip, hoặc đối tượng Choice.
Không truyền class (turn_cls=None) thì trả TurnView/ChoiceView đơn giản bên dưới, dùng để test.

Adapter điền AuraTurn bằng cách dò tên field (paragraphs/choices/stage/image/summary/source...), nên nếu app
đặt tên khác, sửa ALIASES bên dưới là xong.
"""
from __future__ import annotations

import asyncio
import dataclasses
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

ALIASES = {
    "paragraphs": ["paragraphs", "texts", "body", "lines"],
    "choices": ["choices", "suggestions", "options", "chips"],
    "stage": ["stage", "step", "phase", "stage_index"],
    "image": ["image", "detail_image", "image_path", "attachment", "media"],
    "summary": ["summary", "summary_card", "recap", "card"],
    "source": ["source", "source_line", "sources", "citation"],
    "ended": ["ended", "done", "finished", "is_final"],
}
CHOICE_ALIASES = {"text": ["text", "label", "title", "content"], "id": ["id", "key", "value", "choice_id"],
                  "kind": ["kind", "type"]}


@dataclass
class ChoiceView:
    text: str
    id: str = ""
    kind: str = "hint"


@dataclass
class TurnView:
    paragraphs: list = field(default_factory=list)
    choices: list = field(default_factory=list)
    stage: int = 0                  # 0 Ấn tượng đầu | 1 Tách chi tiết | 2 Đối thoại | 3 Mở rộng
    image: Any = None
    summary: Any = None
    source: Optional[str] = None
    ended: bool = False


def _field_names(cls) -> list:
    if dataclasses.is_dataclass(cls):
        return [f.name for f in dataclasses.fields(cls)]
    try:
        return [p for p in inspect.signature(cls).parameters if p != "self"]
    except (TypeError, ValueError):
        return []


def _build(cls, values: dict, aliases: dict):
    names = set(_field_names(cls))
    kwargs = {}
    for canon, val in values.items():
        for a in aliases.get(canon, [canon]):
            if a in names:
                kwargs[a] = val
                break
    return cls(**kwargs)


def default_summary(a: dict) -> dict:
    """Thẻ tổng kết: chỉ dùng lời của user, không kết luận thay họ."""
    rows = [
        ("Ấn tượng ban đầu", a.get("initial_impression")),
        ("Chi tiết bạn đã chú ý", ", ".join(a.get("explored_details") or [])),
        ("Thay đổi so với ban đầu", a.get("impression_change")),
        ("Một câu về bức tranh lúc này", a.get("one_sentence_now")),
        ("Điều bạn muốn người khác để ý", a.get("for_a_newcomer")),
    ]
    return {"title": a.get("painting", ""), "rows": [(k, v) for k, v in rows if v],
            "closing_note": a.get("closing_note")}


class AuraAdapter:
    def __init__(self, hub, turn_cls: Optional[type] = None, choice_cls: Optional[type] = None,
                 image_resolver: Optional[Callable] = None, summary_formatter: Callable = default_summary):
        """image_resolver(painting_id, branch_id, details) -> ảnh chi tiết (đường dẫn/bytes) hoặc None."""
        self.hub = hub
        self.turn_cls, self.choice_cls = turn_cls, choice_cls
        self.image_resolver, self.summary_formatter = image_resolver, summary_formatter
        self.state: Optional[dict] = None
        self._chips: list = []

    # ---------------- public ----------------
    def start(self, painting: str):
        r = self.hub.start(painting)
        return self._to_turn(r)

    async def reply(self, user_input):
        r = await asyncio.to_thread(self.hub.step, self.state, self._as_input(user_input))
        return self._to_turn(r)

    # ---------------- internals ----------------
    def _as_input(self, x):
        if isinstance(x, str):
            text = x
        else:  # đối tượng Choice của app
            text = next((str(getattr(x, a)) for a in CHOICE_ALIASES["text"] if hasattr(x, a)), str(x))
        for c in self._chips:                       # bấm chip -> gửi id, không gõ lại chữ
            if c["text"].strip() == str(text).strip():
                return {"suggestion_id": c["id"]}
        return text

    def _to_turn(self, r: dict):
        self.state = r["state"]
        paragraphs = []
        if r["ack"] and not r["ended"]:
            paragraphs.append(r["ack"])
        paragraphs += [c["content"] for c in r["contexts"]]
        q = r["question"]
        self._chips = q["suggestions"] if q else []
        if q:
            paragraphs.append(q["text"])          # đẩy thẳng câu hỏi, không nhắc lại lựa chọn của user
        elif r["ack"]:
            paragraphs.append(r["ack"])           # lời kết

        choices = [self._choice(c) for c in self._chips]
        d = r.get("detail") or {}
        image = self.image_resolver(self.state["painting_id"], d.get("branch"), d.get("details")) \
            if (self.image_resolver and d) else None
        values = {
            "paragraphs": paragraphs, "choices": choices, "stage": r["stage"], "image": image,
            "summary": self.summary_formatter(r["assessment"]) if r["assessment"] else None,
            "source": ("Thông tin: " + ", ".join(r["sources"])) if r["sources"] else None,
            "ended": r["ended"],
        }
        return _build(self.turn_cls, values, ALIASES) if self.turn_cls else TurnView(**values)

    def _choice(self, chip: dict):
        if not self.choice_cls:
            return ChoiceView(text=chip["text"], id=chip["id"], kind=chip["kind"])
        return _build(self.choice_cls, {"text": chip["text"], "id": chip["id"], "kind": chip["kind"]}, CHOICE_ALIASES)
