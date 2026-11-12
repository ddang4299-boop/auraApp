# AURA — Cảm nhận tranh Phục Hưng qua đối thoại Socrates

Ứng dụng di động viết bằng **Python + [Flet](https://flet.dev)** (Flet dựng giao diện bằng Flutter,
nên cùng một mã nguồn chạy được trên Android, iOS, máy tính và web).
Giao diện dựng theo bản thiết kế của nhóm (khung iPhone 402pt).

## Chạy thử

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

flet run main.py                # cửa sổ kích thước điện thoại trên máy tính
flet run --android main.py      # chạy trên điện thoại Android qua app "Flet" (cùng mạng Wi-Fi)
flet run --ios main.py          # chạy trên iPhone qua app "Flet"
```

## Đóng gói app

```bash
flet build apk      # Android (.apk)
flet build aab      # Android cho Google Play
flet build ipa      # iOS (cần máy Mac + Xcode)
```

Cấu hình đóng gói nằm trong `pyproject.toml`.

## Đưa lên mạng cho người khác dùng thử (có AI)

Chạy app trên máy chủ Render (miễn phí), key AI giữ trên máy chủ: xem [DEPLOY.md](DEPLOY.md).

## Cấu trúc

```
main.py                 Điểm khởi chạy
aura/
  theme.py              Màu, font, kích thước (lấy từ bản thiết kế)
  ui.py                 Component dùng chung: chữ, nút, chip, thẻ, top bar, thanh điều hướng
  data.py               Nội dung: tranh, mốc thời gian, khái niệm, quiz
  socratic.py           Bộ não hội thoại Socrates (interface + kịch bản mẫu)
  auth.py               Đăng nhập Google / Facebook (OAuth 2.0 + PKCE)
  app.py                Điều hướng, trạng thái, phiên đăng nhập
  screens/
    auth.py             Chào mừng · Số điện thoại · OTP
    home.py             Khám phá
    gallery.py          Kho tranh · Đã lưu
    painting.py         Tổng quan tranh
    chat.py             Hỏi Aura (trò chuyện Socrates)
    detail.py           Chi tiết tranh (phóng to)
    quiz.py             Quiz & cảm nhận
    result.py           Kết quả & cảm nhận
    profile.py          Hồ sơ, tài khoản liên kết, thông tin app, đăng xuất
Chatbot/                Chatbot Socrates chạy theo kịch bản JSON
  aura_adapter.py       Cầu nối chatbot với màn chat (AuraChatbotEngine)
  engine.py, hub.py     Bộ máy chạy kịch bản, chọn tranh
  llm.py                Gọi LLM (tuỳ chọn) để hiểu câu gõ tự do
  scripts/              Kịch bản: mỗi tranh một file <Tên_tranh>.json
cli_demo.py             Chat thử chatbot ngay trong terminal
assets/                 Font, icon (Lucide), ảnh tranh
tests/                  Kiểm thử luồng đăng nhập OAuth
docs/BAO_CAO.md         Báo cáo quá trình xây dựng giao diện
```

## Các màn hình và đường dẫn

| Đường dẫn | Màn hình |
|---|---|
| `/` | Chào mừng / đăng nhập |
| `/login/phone`, `/login/otp` | Đăng nhập bằng số điện thoại |
| `/home` | Khám phá (avatar góc phải → Hồ sơ) |
| `/gallery`, `/saved` | Kho tranh, Đã lưu |
| `/painting/<id>` | Tổng quan tranh |
| `/chat/<id>` | Hỏi Aura |
| `/detail/<id>/<chi-tiết>` | Chi tiết tranh |
| `/quiz/<id>`, `/result/<id>` | Quiz & cảm nhận, Kết quả |
| `/profile` | Hồ sơ cá nhân |

## Chatbot theo kịch bản

`main.py` dùng `AuraChatbotEngine` (`Chatbot/aura_adapter.py`):

- Tranh có kịch bản trong `Chatbot/scripts/` chạy bằng chatbot của nhóm. Tên file khớp với `id`
  của tranh trong `aura/data.py`, không phân biệt hoa thường và dấu `-`/`_`
  (ví dụ `mona-lisa` ↔ `Mona_Lisa.json`).
- Tranh chưa có kịch bản dùng kịch bản mẫu trong `aura/socratic.py`.
- Muốn đính kèm ảnh chi tiết khi hội thoại vào một nhánh, khai báo `chat_branches` của tranh
  trong `aura/data.py` (ví dụ `"BRANCH_2A": "face"`).

```bash
python cli_demo.py                  # chat thử trong terminal
pip install -r requirements-dev.txt # thư viện LLM (tuỳ chọn), rồi điền key vào .env
python -m Chatbot.doctor            # kiểm tra key và model dùng được
```

Không có key, chatbot chạy chế độ từ khoá offline. **Không** nhúng key LLM vào app hay bản web:
bản đóng gói luôn chạy offline. Muốn dùng LLM cho người dùng thật cần một máy chủ trung gian giữ key.

## Gắn phương pháp Socrates của nhóm

Màn chat chỉ gọi tới interface `SocraticEngine` trong `aura/socratic.py`:

```python
class MyEngine:
    async def start(self, painting) -> AuraTurn: ...
    async def reply(self, painting, history, user_text) -> AuraTurn: ...

# main.py
AuraApp(page, engine=MyEngine())
```

`AuraTurn` gồm: các đoạn văn, gợi ý trả lời (`Choice`), chặng hiện tại (0–3:
Ấn tượng đầu → Tách chi tiết → Đối thoại → Mở rộng), ảnh chi tiết đính kèm, thẻ tổng kết, dòng nguồn.
`ScriptedSocraticEngine` là kịch bản **dự phòng** dựng từ dữ liệu tranh, dùng cho tranh chưa có
file JSON trong `Chatbot/scripts/`.

**Khi có JSON hội thoại + engine đọc JSON:** viết một lớp adapter nhỏ gọi engine đó trong
`start()`/`reply()` rồi chuyển kết quả sang `AuraTurn` (đoạn văn → `paragraphs`, lựa chọn → `choices`,
giai đoạn → `stage`...). Không cần sửa màn hình nào. `reply()` là `async` nên engine có thể gọi
mạng/LLM; trong lúc chờ, giao diện tự hiện "AURA đang suy nghĩ…".

## Đăng nhập Google / Facebook

1. Sao chép `.env.example` thành `.env`.
2. **Google**: Google Cloud Console → *APIs & Services* → *Credentials* → *Create OAuth client ID*
   → loại **Desktop app**. Điền `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
3. **Facebook**: developers.facebook.com → tạo app → thêm *Facebook Login* → mục
   *Valid OAuth Redirect URIs* thêm `http://localhost:8765/`. Điền `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`.

Khi bấm "Tiếp tục với Google/Facebook", app mở trình duyệt hệ thống; sau khi đồng ý, trình duyệt
chuyển về `http://127.0.0.1:8765/` (app tự lắng nghe), app lấy tên, email và ảnh đại diện, rồi lưu phiên
trên máy. Trong trang **Hồ sơ** có thể liên kết thêm tài khoản còn lại.

Nếu chưa có khoá, app hiện hộp thoại hướng dẫn kèm nút **Dùng thử** (hồ sơ mẫu) để vẫn trải nghiệm được.

> Lưu ý khi phát hành: luồng loopback phù hợp cho máy tính và bản thử trên điện thoại. Bản phát hành
> chính thức trên Android/iOS nên chuyển sang Google Sign-In / Facebook SDK gốc hoặc Firebase Auth
> (redirect bằng deep link) và **không** nhúng client secret vào app.

## Kiểm thử

```bash
python tests/test_auth_flow.py   # luồng OAuth Google với máy chủ giả lập, không cần mạng
```
