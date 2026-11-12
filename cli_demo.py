"""python cli_demo.py -> tự quét folder scripts/, chọn tranh, chat thử trong terminal.
Có key trong .env thì dùng LLM, không thì chạy keyword offline.
Gõ SỐ để bấm chip gợi ý (chip thay cho tin nhắn của bạn), hoặc gõ chữ tự do. 'q' để kết thúc."""
import json
from Chatbot import Hub, make_llm

hub = Hub(llm=make_llm())
for p in hub.problems():
    print(f"[!] {p['id']}: {'BỊ LOẠI - ' if p['errors'] else ''}{(p['errors'] + p['warnings'])[:3]}")
paintings = hub.paintings()
if not paintings:
    raise SystemExit("Không có kịch bản hợp lệ trong folder scripts/")
if len(paintings) == 1:
    pick = paintings[0]
else:
    for i, p in enumerate(paintings, 1):
        print(f"  {i}. {p['title']} - {p['artist']}  ({p['id']})")
    pick = paintings[int(input("Chọn tranh (số): ")) - 1]
print(f"\n--- {pick['title']} ({pick['artist']}) ---")
r = hub.start(pick["id"])


def show(r):
    if r["ack"] and not r["ended"]:
        print("\nBot:", r["ack"])
    for c in r["contexts"]:
        print(f"\n  [{c['topic']}] {c['content']}")
    q = r["question"]
    if q:
        print(f"\nBot: {q['text']}")
        for i, c in enumerate(q["suggestions"], 1):
            print(f"   [{i}] {c['text']}")


show(r)
while not r["ended"]:
    x = input("\nBạn: ").strip()
    if x == "q":
        x = "mình muốn kết thúc"
    chips = r["question"]["suggestions"]
    if x.isdigit() and 0 < int(x) <= len(chips):
        chip = chips[int(x) - 1]
        print("Bạn:", chip["text"])          # chip thay cho tin nhắn của user
        x = {"suggestion_id": chip["id"]}
    r = hub.step(r["state"], x)
    show(r)
print("\n" + r["ack"])
print("\n=== ASSESSMENT ===")
print(json.dumps(r["assessment"], ensure_ascii=False, indent=1))