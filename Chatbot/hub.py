"""
Hub: cửa vào duy nhất cho app. Tự quét folder scripts/, chọn tranh theo id/tên, giữ cache Engine.

    hub = Hub(llm=make_llm())
    hub.paintings()                      # [{"id","title","artist"}, ...]  (chỉ tranh hợp lệ)
    r = hub.start("mona_lisa")           # id, tên có/không dấu đều được
    r = hub.step(r["state"], "mình thấy nụ cười buồn")   # state tự nhớ đang ở tranh nào
"""
from __future__ import annotations

from typing import Optional, Union

from .engine import Engine
from .library import PaintingLibrary
from .llm import LLMFn


class Hub:
    def __init__(self, llm: Optional[LLMFn] = None, scripts_dir=None):
        self.llm = llm
        self.lib = PaintingLibrary(scripts_dir)
        self._cache: dict = {}

    def paintings(self) -> list:
        return [i.brief() for i in self.lib.scan() if i.ok]

    def problems(self) -> list:
        """Kịch bản bị loại (lỗi nặng) hoặc có cảnh báo, để team sửa json."""
        return [{"id": i.id, "ok": i.ok, "errors": i.errors, "warnings": i.warnings}
                for i in self.lib.scan() if i.errors or i.warnings]

    def engine(self, key: Union[str, None]) -> Engine:
        info = self.lib.resolve(key)
        hints = info.path.with_suffix(".hints.json")
        stamp = (info.path.stat().st_mtime, hints.stat().st_mtime if hints.exists() else 0)
        hit = self._cache.get(info.id)
        if hit and hit[0] == stamp:
            return hit[1]
        eng = Engine(info.path, llm=self.llm, library=self.lib)  # json sửa/thêm hints -> tự nạp lại
        self._cache[info.id] = (stamp, eng)
        return eng

    def start(self, key: str) -> dict:
        return self.engine(key).start()

    def step(self, state: dict, user_input) -> dict:
        return self.engine(state["painting_id"]).step(state, user_input)
