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

from .data import HANDS_CROP, Painting

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


# ---------------------------------------------------------------------------
# Kịch bản mẫu cho "Chân dung vợ chồng Arnolfini" (đúng như bản thiết kế)
# ---------------------------------------------------------------------------

_ARNOLFINI_SCRIPT: list[AuraTurn] = [
    AuraTurn(
        ["Chào bạn! Trước khi tìm hiểu xem hai người này là ai, chúng ta hãy thử nhìn vào cách "
         "họ đứng cạnh nhau nhé. Hãy nhìn vào bàn tay họ đang nắm ở chính giữa bức tranh và nét "
         "mặt của cả hai. Theo cảm nhận của bạn, bầu không khí giữa cặp đôi này đang như thế nào?"],
        [Choice("Rất trang trọng, hơi căng thẳng 😐"), Choice("Ấm áp, bình yên 🌿"),
         Choice("Kỳ lạ, không giống đang yêu nhau 🤔")],
        stage=0,
    ),
    AuraTurn(
        ["Bạn nhận xét rất tinh tế! Họ đứng thẳng lưng, ánh mắt trầm tĩnh như đang thực hiện một "
         "nghi lễ lớn chứ không phải buổi hẹn hò thường ngày. Giờ bạn hãy nhìn sang người phụ nữ "
         "mặc váy xanh lá nhé. Cách cô ấy đặt tay lên phần bụng nhô cao khiến bạn liên tưởng đến "
         "điều gì đầu tiên?"],
        [Choice("Chắc chắn là đang mang thai 🤰"), Choice("Do chiếc váy bị phồng lên 👗")],
        stage=1, attachment=DetailAttachment("hands", HANDS_CROP),
    ),
    AuraTurn(
        ["Mình thử tách điều nhìn thấy khỏi điều suy đoán nhé: bạn thấy bàn tay đặt trên bụng, "
         "hay thấy bàn tay đang gom những nếp vải?"],
        [Choice("Nhìn rõ bàn tay đang gom vải 👗"), Choice("Còn nghi ngờ, cần nhìn kỹ hơn 🤔")],
        stage=2,
    ),
    AuraTurn(
        ["Theo National Gallery, phần nhô lên là lớp váy rộng được người phụ nữ nâng trước người, "
         "một cách giữ váy thời đó. Vì vậy, chỉ chi tiết này chưa đủ để kết luận cô ấy mang thai. [1]",
         "Giờ bạn hãy nhìn lại cách họ đứng và trang phục: điều đó có thay đổi cách bạn hiểu sự "
         "trang trọng trong bức tranh không?"],
        [Choice("Có, trang phục và tư thế có thể là lý do chính"),
         Choice("Vẫn cảm thấy có gì đó trang trọng, nhưng không chắc là do mang thai")],
        stage=2,
    ),
    AuraTurn(
        ["Nếu nhìn lại từ đầu, bạn sẽ mô tả điều gì trước khi tìm một lời giải thích?"],
        [Choice("Tay, mặt, vải và tư thế nghiêm trang"),
         Choice("Nhìn chi tiết trước, sau đó kiểm tra nguồn")],
        stage=3,
    ),
    AuraTurn(
        ["Bạn đã tách được điều mình nhìn thấy với điều mình suy đoán. Bước tiếp theo là thử quiz "
         "và chia sẻ cảm nhận của mình."],
        stage=3, done=True,
        summary=Summary("Bạn vừa khám phá",
                        "Bạn đã tách chi tiết tay, mặt, vải và tư thế nghiêm trang trong Chân dung "
                        "vợ chồng Arnolfini, rồi kiểm tra nguồn để hiểu thêm về lớp váy rộng được "
                        "người phụ nữ nâng trước người."),
        source="Nguồn: National Gallery, London · Xem nguồn ↗",
    ),
]

# Câu trả lời mẫu dùng để phát lại toàn bộ hội thoại (bản demo trong thiết kế).
ARNOLFINI_DEMO_REPLIES: list[str | int] = [
    "Trông họ rất trang trọng, nghiêm túc quá mức chứ không thấy cười đùa tình cảm gì cả.",
    "Nhìn giống hệt như cô ấy đang mang thai vậy, nên chắc họ mới đứng nghiêm trang thế.",
    "Nhìn lại thì có vẻ cô ấy đang gom vải váy lên chứ không chắc là bụng phồng.",
    "Có, mình nghĩ sự trang trọng có thể đến từ cách họ đứng thẳng và trang phục phức tạp hơn "
    "là một sự kiện riêng tư.",
    1,   # chạm vào gợi ý thứ 2
]


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
        source="Nguồn: National Gallery, London · Xem nguồn ↗"))
    return turns


class ScriptedSocraticEngine:
    """Engine mẫu chạy theo kịch bản. Thay bằng engine thật của nhóm bạn."""

    def __init__(self, think_delay: float = 0.9):
        self.think_delay = think_delay

    def _script(self, p: Painting) -> list[AuraTurn]:
        return _ARNOLFINI_SCRIPT if p.id == "arnolfini" else _generic_script(p)

    async def start(self, painting: Painting) -> AuraTurn:
        return self._script(painting)[0]

    async def reply(self, painting: Painting, history: list[Message], user_text: str) -> AuraTurn:
        if self.think_delay:
            await asyncio.sleep(self.think_delay)
        script = self._script(painting)
        step = sum(1 for m in history if m.role == "user")
        return script[min(step, len(script) - 1)]
