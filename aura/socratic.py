"""Bộ não hội thoại Socrates của AURA.

Giao diện chat chỉ làm việc với `SocraticEngine`. Muốn dùng phương pháp
Socrates riêng của nhóm (LLM, luật, cây hội thoại...), hãy viết một lớp mới
cài đặt hai hàm `start()` và `reply()` rồi truyền vào `AuraApp(engine=...)`.

Mỗi lượt của AURA (`AuraTurn`) gồm: các đoạn văn, gợi ý trả lời nhanh,
giai đoạn hiện tại (0..3 trong STAGES), và tuỳ chọn: ảnh chi tiết đính kèm,
thẻ tổng kết, trích nguồn.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from typing import Protocol

from .data import Painting

STAGES = ["Ấn tượng đầu", "Tách chi tiết", "Đối thoại", "Mở rộng"]


@dataclass
class Choice:
    label: str                       # chữ trên nút gợi ý
    message: str | None = None       # câu đầy đủ gửi đi (mặc định = label)

    @property
    def text(self) -> str:
        return self.message or self.label


@dataclass
class DetailAttachment:
    detail_key: str
    crop: tuple[float, float, float, float]
    label: str = "Chi tiết tác phẩm"


@dataclass
class Summary:
    title: str
    text: str
    action: str = "Làm quiz nhỏ"


@dataclass
class Info:
    """Thẻ tư liệu: thông tin AURA tra trong kho tư liệu của tranh (danh tính, bối cảnh...)."""
    topic: str
    text: str
    general: bool = False            # True: AI trả lời bằng kiến thức chung, không có trong tư liệu của tranh


@dataclass
class AuraTurn:
    paragraphs: list[str]
    choices: list[Choice] = field(default_factory=list)
    stage: int = 0
    attachment: DetailAttachment | None = None
    summary: Summary | None = None
    source: str | None = None        # dòng nguồn dưới tin nhắn cuối
    done: bool = False
    infos: list[Info] = field(default_factory=list)   # thẻ tư liệu, hiện trước đoạn thứ info_at
    info_at: int = 0


@dataclass
class Message:
    role: str                        # "aura" | "user"
    text: str
    turn: AuraTurn | None = None


# ---- Lưu / đọc lại cuộc trò chuyện (dạng JSON, cất trong bộ nhớ của trình duyệt) ----------------

def message_to_dict(m: Message) -> dict:
    return {"role": m.role, "text": m.text, "turn": asdict(m.turn) if m.turn is not None else None}


def message_from_dict(d: dict) -> Message:
    t = d.get("turn")
    turn = None
    if t:
        att = t.get("attachment")
        turn = AuraTurn(
            paragraphs=[str(x) for x in t.get("paragraphs") or []],
            choices=[Choice(c["label"], c.get("message")) for c in t.get("choices") or []],
            stage=int(t.get("stage") or 0),
            attachment=DetailAttachment(att["detail_key"], tuple(att["crop"]),
                                        att.get("label") or "Chi tiết tác phẩm") if att else None,
            summary=Summary(**t["summary"]) if t.get("summary") else None,
            source=t.get("source"),
            done=bool(t.get("done")),
            infos=[Info(i["topic"], i["text"], bool(i.get("general"))) for i in t.get("infos") or []],
            info_at=int(t.get("info_at") or 0),
        )
    return Message(str(d["role"]), str(d.get("text") or ""), turn)


class SocraticEngine(Protocol):
    async def start(self, painting: Painting) -> AuraTurn: ...

    async def reply(self, painting: Painting, history: list[Message], user_text: str) -> AuraTurn: ...


def _generic_script(p: Painting) -> list[AuraTurn]:
    """Kịch bản Socrates chung dựng từ các 'điểm nhìn' của tranh."""
    pts = p.look_points
    first_detail = next(iter(p.details.values()), None)
    turns = [
        AuraTurn([f"Chào bạn! Hãy dành vài giây nhìn toàn bộ bức “{p.title}”. Điều gì giữ ánh mắt "
                  f"bạn lâu nhất?"],
                 [Choice("Một khuôn mặt hay ánh mắt 👀"), Choice("Màu sắc và ánh sáng ✨"),
                  Choice("Một chi tiết nhỏ khó gọi tên 🤔")], stage=0),
    ]
    for i, lp in enumerate(pts[:2]):
        turns.append(AuraTurn(
            [f"Cảm ơn bạn. Giờ mình cùng thử: {lp.title.lower()}. {lp.text}"],
            [Choice("Mình thấy rõ chi tiết đó"), Choice("Cần nhìn kỹ hơn 🤔")],
            stage=1 + i,
            attachment=DetailAttachment(first_detail.key, first_detail.crop)
            if (i == 0 and first_detail) else None))
    turns.append(AuraTurn(
        [p.story, "Biết thêm điều này, cách bạn nhìn bức tranh có thay đổi không?"],
        [Choice("Có, mình thấy khác đi"), Choice("Vẫn giữ cảm nhận ban đầu")], stage=3))
    turns.append(AuraTurn(
        ["Bạn đã nhìn chậm, tách điều thấy khỏi điều đoán, rồi đối chiếu với thông tin. Hãy chia "
         "sẻ cảm nhận của mình nhé."], stage=3, done=True,
        summary=Summary("Bạn vừa khám phá", f"Bạn đã quan sát kỹ “{p.title}” của {p.artist} và "
                        "kiểm tra thông tin từ bảo tàng.", action="Chia sẻ cảm nhận"),
        source=f"Nguồn: {p.museum} · Xem nguồn ↗" if p.museum else None))
    return turns


class ScriptedSocraticEngine:
    """Engine dự phòng: kịch bản chung dựng từ dữ liệu tranh, dùng khi tranh chưa có
    kịch bản JSON trong Chatbot/scripts/."""

    def __init__(self, think_delay: float = 0.9):
        self.think_delay = think_delay

    def _script(self, p: Painting) -> list[AuraTurn]:
        return _generic_script(p)

    async def start(self, painting: Painting) -> AuraTurn:
        return self._script(painting)[0]

    async def reply(self, painting: Painting, history: list[Message], user_text: str) -> AuraTurn:
        if self.think_delay:
            await asyncio.sleep(self.think_delay)
        script = self._script(painting)
        step = sum(1 for m in history if m.role == "user")
        return script[min(step, len(script) - 1)]
