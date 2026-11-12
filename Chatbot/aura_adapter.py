"""
Cầu nối Engine kịch bản (Chatbot/) với màn chat của AURA.

App chỉ làm việc với interface `SocraticEngine` trong aura/socratic.py:

    async start(painting)                        -> AuraTurn
    async reply(painting, history, user_text)    -> AuraTurn

Lớp `AuraChatbotEngine` dưới đây cài đặt đúng hai hàm đó:
  - Tranh có kịch bản trong Chatbot/scripts/ (khớp theo id, vd "mona-lisa" <-> Mona_Lisa.json)
    thì chạy bằng Engine của nhóm.
  - Tranh chưa có kịch bản thì dùng engine dự phòng (kịch bản mẫu ScriptedSocraticEngine),
    nên các tranh khác vẫn chat được như cũ.

Gắn vào app (main.py):
    from Chatbot.aura_adapter import AuraChatbotEngine
    AuraApp(page, engine=AuraChatbotEngine())
"""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from typing import Optional

from aura.data import Painting

from .library import EXIT_Q
from aura.socratic import (AuraTurn, Choice, DetailAttachment, Message, ScriptedSocraticEngine,
                           SocraticEngine, Summary)

# Câu đệm DỰ PHÒNG trước câu hỏi kế tiếp, chỉ dùng khi engine không có lời phản hồi riêng
# (result["feedback"]: lời viết sẵn cho từng lựa chọn trong kịch bản, hoặc lời AI viết).
ANSWER_ACKS = [
    "Cảm ơn bạn đã chia sẻ.",
    "Mình hiểu rồi.",
    "Mình ghi nhận cảm nhận đó của bạn.",
    "Cảm ơn bạn, mình cùng nhìn tiếp nhé.",
    "Mình hiểu cảm nhận của bạn.",
    "Cảm ơn bạn đã dành thời gian quan sát.",
]
FIRST_ACK = "Cảm ơn bạn. Mình cùng bắt đầu nhé."
NAV_ACKS = ["Được, mình cùng đi theo hướng đó nhé.", "Mình cùng chuyển sang hướng đó nhé."]
CONTEXT_ACK = "Mình chia sẻ thêm một chút thông tin để bạn tham khảo nhé."

CLOSING_FALLBACK = ("Cảm ơn bạn đã cùng khám phá bức tranh. Những điều bạn tự nhận ra là của riêng "
                    "bạn, và bức tranh luôn ở đây nếu bạn muốn quay lại nhìn thêm.")


@dataclass
class _Session:
    """Trạng thái hội thoại của một bức tranh (Engine của nhóm là stateless, app giữ state)."""
    script_id: str
    state: dict
    chips: list = field(default_factory=list)       # chip gợi ý của lượt gần nhất
    last_branch: Optional[str] = None               # nhánh đã đính kèm ảnh gần nhất
    replies: int = 0                                # số lượt người dùng đã gửi
    ack_i: int = 0                                  # xoay vòng câu đệm để không lặp


def summary_text(a: dict) -> str:
    """Thẻ tổng kết: chỉ dùng lời của người dùng, không kết luận thay họ."""
    # Engine ghi cả chữ trên chip (câu hỏi, có dấu "?") vào explored_details: chỉ giữ chi tiết thật.
    details = [d for d in (a.get("explored_details") or []) if d and not d.rstrip().endswith("?")]
    rows = [
        ("Ấn tượng ban đầu", a.get("initial_impression")),
        ("Chi tiết bạn đã chú ý", ", ".join(details)),
        ("Thay đổi so với ban đầu", a.get("impression_change")),
        ("Một câu về bức tranh lúc này", a.get("one_sentence_now")),
        ("Điều bạn muốn người khác để ý", a.get("for_a_newcomer")),
    ]
    lines = [f"{k}: {v}" for k, v in rows if v]
    if not lines:
        return (f"Bạn đã dành thời gian nhìn chậm “{a.get('painting', 'bức tranh')}”. "
                "Những điều bạn nhận ra là của riêng bạn.")
    return "\n".join(lines)


def _make_llm():
    """LLM nếu .env có key, ngược lại None (Engine chạy chế độ từ khoá offline)."""
    try:
        from .llm import make_llm
        return make_llm()
    except Exception as e:                     # thiếu thư viện / cấu hình sai: vẫn chạy offline
        print(f"[chatbot] Không bật được LLM, chạy offline: {e}")
        return None


class AuraChatbotEngine:
    def __init__(self, hub=None, fallback: Optional[SocraticEngine] = None):
        """hub: Chatbot.Hub đã tạo sẵn (để test). Mặc định tự tạo khi cần, kèm LLM nếu có key."""
        self._hub = hub
        self._hub_failed = False
        self.fallback = fallback or ScriptedSocraticEngine()
        self._sessions: dict[str, _Session] = {}      # painting.id -> phiên chat

    # ------------------------------------------------------------------ SocraticEngine
    async def start(self, painting: Painting) -> AuraTurn:
        script_id = self._script_for(painting)
        if not script_id:
            self._sessions.pop(painting.id, None)
            return await self.fallback.start(painting)
        r = await self._run(self.hub.start, script_id)
        session = _Session(script_id, r["state"])
        self._sessions[painting.id] = session
        return self._to_turn(painting, session, r)

    async def reply(self, painting: Painting, history: list[Message], user_text: str) -> AuraTurn:
        session = self._sessions.get(painting.id)
        if session is None:
            if not self._script_for(painting):
                return await self.fallback.reply(painting, history, user_text)
            await self.start(painting)                # phiên bị mất (vd app khởi động lại)
            session = self._sessions[painting.id]
        user_input = self._as_input(session, user_text)
        # Đang ở menu chọn hướng (Q2.F, danh sách chi tiết...) thì câu trả lời là chọn hướng, không phải cảm nhận
        at_menu = (session.state.get("node") or {}).get("id") in (EXIT_Q, "BRANCH_LIST", "BRIDGE")
        nav = at_menu or any(c.get("kind") == "nav" and c["text"].strip() == (user_text or "").strip()
                             for c in session.chips)
        r = await self._run(self.hub.step, session.state, user_input)
        session.replies += 1
        return self._to_turn(painting, session, r, ack=self._ack(session, r, nav))

    # ------------------------------------------------------------------ internals
    @property
    def hub(self):
        if self._hub is None:
            from .hub import Hub
            self._hub = Hub(llm=_make_llm())
        return self._hub

    def _script_for(self, painting: Painting) -> Optional[str]:
        """id kịch bản của tranh, hoặc None nếu chưa có / kịch bản lỗi."""
        if self._hub_failed:
            return None
        try:
            info = self.hub.lib.resolve(painting.id)
        except FileNotFoundError as e:               # không có folder scripts
            print(f"[chatbot] {e}")
            self._hub_failed = True
            return None
        except KeyError:                             # tranh này chưa có kịch bản
            return None
        if not info.ok:
            print(f"[chatbot] Kịch bản {info.id} lỗi, dùng kịch bản mẫu: {info.errors}")
            return None
        return info.id

    @staticmethod
    async def _run(fn, *args):
        # Engine/LLM chạy đồng bộ: đưa sang thread để giao diện không đứng.
        # Bản web (Pyodide) không có thread nên gọi thẳng.
        if sys.platform == "emscripten":
            return fn(*args)
        return await asyncio.to_thread(fn, *args)

    @staticmethod
    def _as_input(session: _Session, user_text: str):
        text = (user_text or "").strip()
        for c in session.chips:
            if c["text"].strip() == text:
                if c.get("option_id"):               # bấm 1 câu trả lời có sẵn trong kịch bản
                    return {"option_id": c["option_id"]}
                return {"suggestion_id": c["id"]}    # bấm 1 chip gợi ý của engine
        return text

    def _chips(self, session: _Session, r: dict) -> list:
        """Chip hiển thị: ưu tiên các câu TRẢ LỜI nhóm đã viết trong kịch bản (options).

        Engine mặc định hiện chip là câu HỎI của người dùng (từ *.hints.json). Ở chế độ offline
        bot không trả lời được các câu hỏi đó nên hội thoại thành "hỏi - hỏi", rất cụt.
        Dùng options thì bấm chip = trả lời đúng câu đang hỏi, đi đúng nhánh kịch bản.
        Menu điều hướng (Q2.F, chọn nhánh, quay lại) và câu không có options giữ chip của engine.
        """
        q = r["question"]
        engine_chips = q["suggestions"] if q else []
        node = r["state"].get("node") or {}
        if node.get("id") == "CROSS":
            # câu so sánh hai chi tiết: mời người dùng tự gõ; chip câu hỏi chung chung chỉ dẫn tới
            # "chưa có thông tin đáng tin cậy" nên không hiện
            return []
        if not q or node.get("type") != "question" or node.get("id") == EXIT_Q:
            return engine_chips
        node_def = self.hub.engine(session.script_id).q.get(node["id"], ({},))[0]
        options = [o for o in node_def.get("options", []) if "free input" not in o["label"].lower()]
        if not options:
            return engine_chips
        return [{"id": o["id"], "text": o["label"], "kind": "option", "option_id": o["id"]}
                for o in options]

    @staticmethod
    def _ack(session: _Session, r: dict, nav: bool) -> str:
        """Câu đệm cho lượt vừa rồi. Rỗng khi engine đã có lời đệm riêng hoặc hội thoại kết thúc."""
        if r["ended"] or r["ack"]:
            return ""
        if r["contexts"]:
            return CONTEXT_ACK
        if session.replies == 1:
            return FIRST_ACK
        pool = NAV_ACKS if nav else ANSWER_ACKS
        text = pool[session.ack_i % len(pool)]
        session.ack_i += 1
        return text

    def _to_turn(self, painting: Painting, session: _Session, r: dict, ack: str = "") -> AuraTurn:
        session.state = r["state"]
        q = r["question"]
        session.chips = self._chips(session, r)

        # Phản hồi đúng câu trả lời vừa rồi (kịch bản viết sẵn hoặc AI viết). Có nó thì bỏ câu đệm chung chung.
        feedback = (r.get("feedback") or "").strip()
        if feedback:
            ack = ""
        paragraphs: list[str] = []
        if r["ended"]:
            if feedback:
                paragraphs.append(feedback)
            paragraphs.append(r["ack"] or CLOSING_FALLBACK)
        else:
            if r["ack"]:
                paragraphs.append(r["ack"])
            elif feedback:
                paragraphs.append(feedback)
            elif ack and (r["contexts"] or not q):
                paragraphs.append(ack)
            paragraphs += [c["content"] for c in r["contexts"]]
            if q:
                # câu đệm đứng liền trước câu hỏi trong cùng một đoạn cho tự nhiên
                lead = ack if (ack and not r["ack"] and not r["contexts"]) else ""
                paragraphs.append(f"{lead} {q['text']}".strip())
        if not paragraphs:
            paragraphs.append(CLOSING_FALLBACK if r["ended"] else "Bạn muốn nhìn tiếp điều gì?")

        summary = None
        if r["assessment"]:
            summary = Summary("Bạn vừa khám phá", summary_text(r["assessment"]),
                              action="Làm quiz nhỏ" if painting.quiz else "Chia sẻ cảm nhận")

        source = None
        if r["sources"]:
            source = "Thông tin: " + " · ".join(r["sources"])
        elif r["ended"]:
            source = f"Nguồn: {painting.museum} · Xem nguồn ↗"

        return AuraTurn(
            paragraphs=paragraphs,
            choices=[Choice(c["text"]) for c in session.chips],
            stage=max(0, min(3, int(r["stage"]))),
            attachment=self._attachment(painting, session, r),
            summary=summary,
            source=source,
            done=bool(r["ended"]),
        )

    @staticmethod
    def _attachment(painting: Painting, session: _Session, r: dict) -> Optional[DetailAttachment]:
        """Đính kèm ảnh chi tiết khi hội thoại vừa chuyển sang một nhánh có ảnh tương ứng."""
        branch = (r.get("detail") or {}).get("branch")
        if not branch or branch == session.last_branch:
            return None
        session.last_branch = branch
        key = painting.chat_branches.get(branch)
        d = painting.details.get(key) if key else None
        if not d:
            return None
        return DetailAttachment(d.key, d.chat_crop or d.crop, label=d.title)
