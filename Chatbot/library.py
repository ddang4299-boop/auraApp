"""
Thư viện tranh: quét folder scripts/, mỗi tranh = 1 file .json. Không hard-code tên tranh.

Tìm folder theo thứ tự: tham số truyền vào -> biến môi trường CHATBOT_SCRIPTS_DIR ->
Chatbot/scripts | Chatbot/Scripts -> ./scripts | ./Scripts -> ./Chatbot/scripts.
Thêm tranh mới = bỏ thêm 1 file json vào folder, không cần sửa code.
Tranh nào lỗi cấu trúc sẽ bị báo lý do chứ không làm sập app.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

DYNAMIC_RULES = {
    "return_current_branch", "open_unexplored_branch_list", "cross_branch_questions",
    "pending_stage3_branch", "q1_1_by_emotion", "branch_by_detail_in_free_input",
    "revisit_branch_of_selected_detail",
}
REQUIRED_TOP = ("meta", "ai_behavior", "context_database", "stages")
EXIT_Q = "Q2.F"  # câu hỏi chuyển Stage 2 -> 3, mọi kịch bản phải có


def norm(s: str) -> str:
    """'Đêm đầy sao' -> 'demdaysao'; 'Mona_Lisa' -> 'monalisa' (để khớp tên không phân biệt dấu/hoa thường)."""
    s = unicodedata.normalize("NFKD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


@dataclass
class PaintingInfo:
    id: str                      # tên file (không đuôi)
    path: Path
    title: str = ""
    artist: str = ""
    ok: bool = False
    errors: list = field(default_factory=list)    # lỗi nặng: không chạy được
    warnings: list = field(default_factory=list)  # nghi ngờ: nên rà lại

    def brief(self) -> dict:
        return {"id": self.id, "title": self.title, "artist": self.artist}


def _all_nodes(data: dict) -> tuple[dict, dict]:
    qs, bs = {}, {}
    for sid, st in data.get("stages", {}).items():
        for qid, q in st.get("questions", {}).items():
            qs[qid] = q
        for qid, q in st.get("exit_revisit", {}).get("questions", {}).items():
            qs[qid] = q
        for bid, b in st.get("branches", {}).items():
            bs[bid] = b
            for qid, q in b.get("questions", {}).items():
                qs[qid] = q
    return qs, bs


def validate_script(data: dict) -> tuple[list, list]:
    errors, warns = [], []
    for k in REQUIRED_TOP:
        if k not in data:
            errors.append(f"Thiếu khóa gốc '{k}'")
    if errors:
        return errors, warns
    stages = data["stages"]
    for sid in ("STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4"):
        if sid not in stages:
            errors.append(f"Thiếu {sid}")
    if errors:
        return errors, warns
    qs, bs = _all_nodes(data)
    ctx = set(data["context_database"].get("items", {}))
    entry = data["meta"].get("entry_point", {}).get("id")
    if entry not in qs:
        errors.append(f"meta.entry_point trỏ tới câu không tồn tại: {entry}")
    if EXIT_Q not in qs:
        errors.append(f"Thiếu câu {EXIT_Q}")
    if "cross_branch_questions" not in stages["STAGE_2"]:
        errors.append("STAGE_2 thiếu cross_branch_questions")
    if not data["ai_behavior"].get("free_input_keyword_routing"):
        warns.append("Thiếu ai_behavior.free_input_keyword_routing (nhập tự do khó định tuyến)")
    for bid, b in bs.items():
        if b.get("entry_question") not in qs:
            errors.append(f"{bid}.entry_question không tồn tại: {b.get('entry_question')}")

    def check(nav, where):
        if not isinstance(nav, dict):
            return
        t, i = nav.get("type"), nav.get("id")
        if t == "question" and i not in qs:
            warns.append(f"{where}: next -> câu không tồn tại '{i}'")
        elif t == "branch" and i not in bs:
            warns.append(f"{where}: next -> nhánh không tồn tại '{i}'")
        elif t == "stage" and i not in stages:
            warns.append(f"{where}: next -> stage không tồn tại '{i}'")
        elif t == "dynamic" and nav.get("rule") not in DYNAMIC_RULES:
            warns.append(f"{where}: dynamic rule lạ '{nav.get('rule')}'")

    for qid, q in qs.items():
        check(q.get("default_next"), qid)
        check(q.get("alternative_next"), qid)
        for c in q.get("conditional_next", []) or []:
            check(c.get("next"), qid)
        for r in q.get("routing_rules", []) or []:
            check(r.get("next"), qid)
        for o in q.get("options", []) or []:
            check(o.get("next"), f"{qid}.{o.get('id')}")
            for c in o.get("context", []) or []:
                if c not in ctx:
                    warns.append(f"{qid}.{o.get('id')}: mã context '{c}' không có trong context_database")
        for c in (q.get("context_trigger") or {}).get("context", []):
            if c not in ctx:
                warns.append(f"{qid}: context_trigger '{c}' không có trong context_database")
    return errors, warns


class PaintingLibrary:
    ENV = "CHATBOT_SCRIPTS_DIR"

    def __init__(self, scripts_dir: Union[str, Path, None] = None):
        self.dir = self.find_dir(scripts_dir)

    @classmethod
    def find_dir(cls, explicit=None) -> Path:
        here = Path(__file__).parent
        cwd = Path.cwd()
        cands = [explicit, os.getenv(cls.ENV)]
        for base in (here, cwd, cwd / "Chatbot", here.parent):
            cands += [Path(base) / "scripts", Path(base) / "Scripts"]
        tried = []
        for c in cands:
            if not c:
                continue
            p = Path(c)
            tried.append(str(p))
            if p.is_dir() and any(p.glob("*.json")):
                return p
        raise FileNotFoundError("Không thấy folder scripts có file .json. Đã thử:\n  " + "\n  ".join(tried))

    def scan(self) -> list[PaintingInfo]:
        """Quét lại mỗi lần gọi (rẻ) nên thêm file json lúc app đang chạy vẫn nhận ra."""
        out = []
        for p in sorted(self.dir.glob("*.json")):
            if p.name.lower().endswith(".hints.json"):
                continue
            info = PaintingInfo(id=p.stem, path=p, title=p.stem)
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                meta = data.get("meta", {}) if isinstance(data, dict) else {}
                info.title = meta.get("target_artwork") or p.stem
                info.artist = meta.get("artist", "")
                info.errors, info.warnings = validate_script(data)
            except (OSError, json.JSONDecodeError) as e:
                info.errors = [f"Không đọc được file: {e}"]
            info.ok = not info.errors
            out.append(info)
        return out

    def resolve(self, key: Union[str, Path]) -> PaintingInfo:
        """key: id (tên file), tên tranh ('Mona Lisa', 'mona lisa'), hoặc đường dẫn file json."""
        if isinstance(key, Path) or str(key).lower().endswith(".json"):
            p = Path(key)
            for i in self.scan():
                if i.path.resolve() == p.resolve():
                    return i
            raise FileNotFoundError(f"Không thấy file {p}")
        k = norm(str(key))
        infos = self.scan()
        for i in infos:
            if norm(i.id) == k or norm(i.title) == k:
                return i
        for i in infos:  # khớp một phần
            if k and (k in norm(i.id) or k in norm(i.title)):
                return i
        raise KeyError(f"Không có tranh '{key}'. Hiện có: {[i.id for i in infos]}")

    def load(self, key) -> tuple[dict, PaintingInfo]:
        info = self.resolve(key)
        if not info.ok:
            raise ValueError(f"Kịch bản '{info.id}' lỗi: " + "; ".join(info.errors))
        return json.loads(info.path.read_text(encoding="utf-8")), info
