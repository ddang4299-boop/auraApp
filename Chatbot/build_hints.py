"""
Sinh sẵn CHIP GỢI Ý (câu user có thể hỏi bot) cho mọi câu trong kịch bản, lưu ở scripts/<tranh>.hints.json.
Chạy 1 lần (cần key LLM), sau đó app dùng offline/không tốn token. File này đọc được, sửa tay được.

    python -m Chatbot.build_hints              # mọi tranh trong scripts/ (chỉ câu còn thiếu)
    python -m Chatbot.build_hints mona_lisa    # một tranh
    python -m Chatbot.build_hints --force      # sinh lại tất cả
"""
from __future__ import annotations

import json
import re
import sys
import time

from .library import EXIT_Q, PaintingLibrary, _all_nodes
from .llm import make_llm

SYSTEM = """Bạn soạn CHIP GỢI Ý cho app khám phá tranh. Chip là câu NGƯỜI DÙNG có thể bấm để hỏi chatbot khi chưa biết hỏi gì
(bấm chip = chip thay cho tin nhắn của họ). Ví dụ chip: "Bức tranh này là gì?", "Nụ cười này có gì lạ?".

Với mỗi node (chatbot đang hỏi người dùng "question"), viết 3 chip, viết ở GÓC NGƯỜI DÙNG đang tò mò:
- Câu hỏi ngắn (tối đa 12 từ), kết thúc "?", xưng "mình" hoặc không xưng hô. TUYỆT ĐỐI không mở đầu bằng "Bạn".
- Hỏi về thứ nhìn thấy trong tranh (chi tiết, vị trí, ánh sáng, biểu cảm...) hoặc về các chủ đề trong context_topics
  (để chatbot có cái đáp lại). Không hỏi thứ ngoài các chủ đề đó (giá tiền, so sánh tranh khác...).
- Liên quan tới chủ đề của node hiện tại, 3 chip khác hướng nhau.
- Không chứa sẵn đáp án, không gán sẵn cảm xúc/ý nghĩa, không nêu sự thật hay kiến thức.
- Không phải câu trả lời cho "question", không lặp lại "question".
"answer_themes" chỉ để bạn hiểu node nói về gì, đừng biến chúng thành chip.
Trả về MỘT JSON: {"<id node>": ["chip 1","chip 2","chip 3"], ...}. Không markdown."""


def _ok(h: str, main: str) -> bool:
    h = h.strip() if isinstance(h, str) else ""
    return (h.endswith("?") and h.count("?") == 1 and len(h) <= 90 and not h.lower().startswith("bạn")
            and h.lower() != main.strip().lower())


def build(painting: str, llm, force: bool = False, pause: float = 4.0, chunk: int = 10) -> dict:
    lib = PaintingLibrary()
    data, info = lib.load(painting)
    out_path = info.path.with_suffix(".hints.json")
    hints = {}
    if out_path.exists() and not force:
        old = json.loads(out_path.read_text(encoding="utf-8"))
        hints = old.get("hints", {}) if old.get("version", 1) >= 2 else {}   # v1 là kiểu cũ -> sinh lại
    qs, bs = _all_nodes(data)
    branch_of = {qid: b.get("title", "") for b in bs.values() for qid in b["questions"]}
    todo = [qid for qid, q in qs.items() if qid != EXIT_Q and qid not in hints and not q.get("suggested_questions")]
    print(f"[{info.id}] {len(todo)} câu cần sinh gợi ý")
    failed_in_a_row = 0
    for i in range(0, len(todo), chunk):
        batch = todo[i:i + chunk]
        topics = [v["topic"] for v in data["context_database"]["items"].values()]
        payload = {"painting": info.title, "context_topics": topics, "nodes": [
            {"id": qid, "question": qs[qid]["text"], "branch": branch_of.get(qid, ""),
             "answer_themes": [o["label"] for o in qs[qid].get("options", [])]} for qid in batch]}
        ok = False
        for attempt in range(3):
            try:
                raw = llm(SYSTEM, json.dumps(payload, ensure_ascii=False), 1500)
                got = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
                for qid in batch:
                    good = [h.strip() for h in got.get(qid, []) if _ok(h, qs[qid]["text"])][:3]
                    if good:
                        hints[qid] = good
                ok = True
                break
            except Exception as e:
                print(f"  lỗi lô {i // chunk + 1} (lần {attempt + 1}): {e}")
                if any(c in str(e) for c in ("404", "401", "403", "API key")):  # lỗi cấu hình: thử lại vô ích
                    break
                time.sleep(pause * (attempt + 1))
        failed_in_a_row = 0 if ok else failed_in_a_row + 1
        if failed_in_a_row >= 2:
            print("\nDừng: 2 lô liên tiếp thất bại. Chạy  python -m Chatbot.doctor  để xem provider nào lỗi và model nào dùng được.")
            break
        out_path.write_text(json.dumps({"version": 2, "painting": info.id, "hints": hints},
                                       ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {'đã xong' if ok else 'THẤT BẠI'} {min(i + chunk, len(todo))}/{len(todo)}")
        time.sleep(pause)
    missing = [q for q in todo if q not in hints]
    print(f"[{info.id}] xong. Còn thiếu {len(missing)} câu (sẽ dùng gợi ý chung): {missing[:8]}")
    return hints


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    llm = make_llm()
    if not llm:
        sys.exit("Chưa có key LLM trong .env (GEMINI_API_KEY...). Xem .env.example")
    keys = args or [i.id for i in PaintingLibrary().scan() if i.ok]
    for k in keys:
        build(k, llm, force="--force" in sys.argv)