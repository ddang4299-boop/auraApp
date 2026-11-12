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
from dataclasses import dataclass, field
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
class AuraTurn:
    paragraphs: list[str]
    choices: list[Choice] = field(default_factory=list)
    stage: int = 0
    attachment: DetailAttachment | None = None
    summary: Summary | None = None
    source: str | None = None        # dòng nguồn dưới tin nhắn cuối
    done: bool = False


@dataclass
class Message:
    role: str                        # "aura" | "user"
    text: str
    turn: AuraTurn | None = None


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
