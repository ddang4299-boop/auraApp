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

Chạy app trên máy chủ Render (miễn phí), key AI giữ trên máy chủ: xem [docs/DEPLOY.md](docs/DEPLOY.md).

## Cấu trúc

```
main.py                 Điểm khởi chạy
aura/
  theme.py              Màu, font, kích thước (lấy từ bản thiết kế)
  ui.py                 Component dùng chung: chữ, nút, chip, thẻ, top bar, thanh điều hướng nổi
  data.py               Nội dung 5 bức tranh: thông tin, chi tiết, quiz, câu hỏi nhanh dưới ô chat
  topics.py             Nội dung trang Khám phá: thời kỳ, mốc thời gian, khái niệm
  socratic.py           Interface hội thoại (AuraTurn...) + kịch bản mẫu dự phòng + lưu/đọc lịch sử chat
  auth.py               Đăng nhập Google (OAuth 2.0 + PKCE)
  vision.py             Scan: nhận diện tranh trong ảnh chụp bằng điểm đặc trưng (OpenCV SIFT + RANSAC)
  app.py                Điều hướng, trạng thái, phiên đăng nhập, lưu cuộc trò chuyện vào trình duyệt
  screens/
    auth.py             Chào mừng (đăng nhập Google hoặc bỏ qua)
    home.py             Khám phá
    topics.py           Mốc thời gian, khái niệm, bài đọc chủ đề
    gallery.py          Kho tranh kiểu phòng trưng bày (khung tranh, biển tên, bộ lọc) · Đã lưu
    onboarding.py       Hướng dẫn 4 bước cho người mở app lần đầu
    painting.py         Tổng quan tranh
    viewer.py           Xem tranh phóng to
    chat.py             Trò chuyện về tranh (Socrates quanh một bức, câu hỏi nhanh, bắt đầu lại)
    ask.py              Hỏi Aura: hỏi đáp mở về Phục Hưng, tả tranh để AURA đoán tên và mở đúng bức
    scan.py             Scan tác phẩm: mẹo chụp, chụp/chọn ảnh, kết quả nhận diện
    sources.py          Tư liệu: các thẻ tư liệu chatbot dựa vào khi trả lời
    settings.py         Cài đặt, Giới thiệu, Chính sách quyền riêng tư
    detail.py           Chi tiết tranh (phóng to)
    quiz.py             Quiz & cảm nhận
    result.py           Kết quả & cảm nhận
    profile.py          Thông tin tài khoản: hồ sơ cá nhân, tài khoản liên kết
Chatbot/                Chatbot Socrates chạy theo kịch bản JSON
  aura_adapter.py       Cầu nối chatbot với màn chat (AuraChatbotEngine)
  engine.py, hub.py     Bộ máy chạy kịch bản, chọn tranh
  generic.py            Hội thoại Socrates có AI cho tranh chưa có kịch bản JSON (lộ trình dựng từ data.py)
  general.py            Hỏi Aura: hỏi đáp mở + nhận diện tranh từ mô tả (kiểm lại với Kho tranh)
  qa.py                 Trả lời câu hỏi gõ tay dựa trên tư liệu của tranh (RAG) rồi bắc cầu về câu đang hỏi
  llm.py                Gọi LLM (tuỳ chọn), nhiều key / nhiều nhà cung cấp dự phòng
  library.py            Đọc và kiểm tra các file kịch bản
  cli_demo.py           Chat thử chatbot ngay trong terminal
  doctor.py             Kiểm tra key và model dùng được
  build_hints.py        Sinh sẵn gợi ý cho từng câu hỏi trong kịch bản
  scripts/              Kịch bản: mỗi tranh một file <Tên_tranh>.json
assets/                 Font, icon (Lucide), ảnh tranh, trang khung bản web (index.html)
  fonts/web/            Font rút gọn (Latin + tiếng Việt) app thực sự dùng; font gốc ở fonts/
  images/home/thumb/    Ảnh minh hoạ thu nhỏ cho các thẻ nhỏ; ảnh gốc ở images/home/
tools/
  optimize_assets.py    Tạo lại ảnh thu nhỏ, logo màn chờ, font rút gọn (chạy khi thay ảnh/font)
tests/                  Kiểm thử luồng đăng nhập OAuth
docs/
  DEPLOY.md             Hướng dẫn đưa app lên Render
  BAO_CAO.md            Báo cáo quá trình xây dựng giao diện
render.yaml             Cấu hình máy chủ Render
requirements*.txt       Thư viện: app (requirements.txt), máy chủ (-server), phát triển (-dev)
```

## Các màn hình và đường dẫn

| Đường dẫn | Màn hình |
|---|---|
| `/` | Chào mừng / đăng nhập |
| `/home` | Khám phá (avatar góc phải → Cài đặt) |
| `/timeline`, `/concepts`, `/topic/<id>` | Mốc thời gian, Khái niệm, bài đọc chủ đề |
| `/gallery`, `/saved` | Kho tranh: Bộ sưu tập · Đã lưu (công tắc ở đầu trang; `/saved` mở thẳng Đã lưu) |
| `/painting/<id>` | Tổng quan tranh |
| `/chat/<id>` | Trò chuyện về một bức tranh (Socrates) |
| `/ask` | Hỏi Aura: hỏi đáp mở, nhận diện tranh từ mô tả |
| `/scan` | Scan tác phẩm: chụp ảnh để nhận ra bức tranh |
| `/sources/<id>` | Tư liệu chatbot dùng để trả lời |
| `/detail/<id>/<chi-tiết>` | Chi tiết tranh |
| `/quiz/<id>`, `/result/<id>` | Quiz & cảm nhận, Kết quả |
| `/settings`, `/profile` | Cài đặt, Thông tin tài khoản |
| `/about`, `/privacy` | Giới thiệu, Chính sách quyền riêng tư |

Thanh điều hướng nổi (dạng viên thuốc): **Khám phá** · **Kho tranh** · **Scan** · **Hỏi Aura** · **Cài đặt**.
- Kho tranh gồm Bộ sưu tập và Đã lưu (tranh đã bấm dấu trang, lưu trong trình duyệt).
- Nút tròn ở giữa là **Scan ảnh tác phẩm**: chụp cả bức hay chỉ một phần, AURA nhận ra bức tranh và mở đúng
  trang (chụp sát một chi tiết thì gợi ý mở chi tiết đó). Chưa chắc thì hỏi "Có phải bức này không?",
  không nhận ra thì gợi ý chụp lại. Cách làm: `aura/vision.py` "nhớ" sẵn khoảng 1.500 điểm đặc trưng của mỗi
  bức (SIFT, ở 3 mức nét), ghép với điểm trong ảnh chụp rồi kiểm tra hình học bằng RANSAC. Không cần huấn
  luyện model, thêm tranh vào `data.py` là Scan nhận được. Ảnh gửi lên máy chủ, nhận diện xong xoá ngay.
- Hỏi Aura: hỏi về thời Phục Hưng hay bất kỳ bức tranh nào; tả một bức tranh thì AURA đoán tên, bức nào có
  trong Kho tranh thì hiện thẻ có nút mở thẳng bức đó.
- Trang của mỗi bức tranh có nút trò chuyện về bức đó và liên kết tới phần Tư liệu.
Điện thoại: thanh nổi ở cạnh dưới. Máy tính: thanh nằm ở góc trên bên phải.
Cuộc trò chuyện được cất trong bộ nhớ của trình duyệt nên tải lại trang (F5) vẫn nói tiếp đúng chỗ;
nút **Bắt đầu lại** trong màn chat xoá để trò chuyện từ đầu, đăng xuất cũng xoá.
Lần đầu mở app có hướng dẫn 4 bước (Tiếp theo / Quay lại / Bỏ qua); đã xem thì không hiện lại
(ghi nhớ trong trình duyệt, khoá `aura.onboarded`).

## Chatbot theo kịch bản

`main.py` dùng `AuraChatbotEngine` (`Chatbot/aura_adapter.py`):

- Tranh có kịch bản trong `Chatbot/scripts/` chạy bằng chatbot của nhóm. Tên file khớp với `id`
  của tranh trong `aura/data.py`, không phân biệt hoa thường và dấu `-`/`_`
  (ví dụ `mona-lisa` ↔ `Mona_Lisa.json`).
- Tranh chưa có kịch bản (hiện là 4 tranh của National Gallery) dùng `Chatbot/generic.py`: lộ trình
  ấn tượng đầu → từng điểm nhìn → chuyện phía sau → suy ngẫm, dựng từ dữ liệu tranh. Câu gõ tự do được
  trả lời theo 3 bước: bàn thẳng vào ý người xem, thêm một thông tin thật từ tư liệu, rồi một câu hỏi
  gợi mở mới dẫn về lộ trình. Thông tin ngoài tư liệu được gắn nhãn "Kiến thức chung"; con số không
  có trong tư liệu (kích thước, tuổi...) thì không đoán. Không có AI vẫn chạy bằng lời viết sẵn.
- Muốn đính kèm ảnh chi tiết khi hội thoại vào một nhánh, khai báo `chat_branches` của tranh
  trong `aura/data.py` (ví dụ `"BRANCH_2A": "face"`).

```bash
python -m Chatbot.cli_demo          # chat thử trong terminal
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

## Đăng nhập Google

1. Sao chép `.env.example` thành `.env`.
2. **Google**: Google Cloud Console → *APIs & Services* → *Credentials* → *Create OAuth client ID*
   → loại **Desktop app**. Điền `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.

Khi bấm "Tiếp tục với Google", app mở trình duyệt hệ thống; sau khi đồng ý, trình duyệt
chuyển về `http://127.0.0.1:8765/` (app tự lắng nghe), app lấy tên, email và ảnh đại diện, rồi lưu phiên
trên máy. Người dùng cũng có thể bấm **Bỏ qua** để dùng như khách, rồi liên kết Google sau trong **Hồ sơ**.

Nếu chưa có khoá, app hiện hộp thoại hướng dẫn kèm nút **Dùng thử** (hồ sơ mẫu) để vẫn trải nghiệm được.

> Lưu ý khi phát hành: luồng loopback phù hợp cho máy tính và bản thử trên điện thoại. Bản phát hành
> chính thức trên Android/iOS nên chuyển sang Google Sign-In gốc hoặc Firebase Auth
> (redirect bằng deep link) và **không** nhúng client secret vào app.

## Bản web nhẹ và nhanh

- Ảnh minh hoạ ở thẻ nhỏ, logo màn chờ và font đều dùng bản rút gọn (trang chủ tải ảnh ít hơn ~43%,
  font ít hơn ~59%). Thay ảnh trong `assets/images/` hoặc font trong `assets/fonts/` thì chạy
  `python tools/optimize_assets.py` để tạo lại.
- Lúc mới mở, bản web đôi khi báo bề rộng tạm (~164px): app chờ bề rộng thật (tối đa 1,5 giây) rồi mới
  dựng màn, nên mỗi lần mở chỉ dựng một lần (máy chủ miễn phí 0,1 CPU, dựng hai lần mất thêm ~1 giây).
- Máy chủ Render nén sẵn các file lớn của Flutter (Brotli), không cần nén thêm trong app.
- RAM máy chủ (gói miễn phí 512 MB):
  - Phần nặng của chatbot (kịch bản, chỉ mục hỏi đáp, chuỗi LLM, Hỏi Aura) dùng CHUNG cho mọi người dùng
    thay vì mỗi tab trình duyệt một bản (đo được: 5 phiên từ +69 MB còn +6 MB).
  - Thư viện AI (`openai`, `google-genai`, mỗi cái ~20 MB) chỉ nạp khi gọi AI lần đầu; Gemini là dự phòng
    nên thường không bao giờ nạp. OpenCV (Scan) chỉ nạp khi có người dùng Scan.
  - Người dùng đóng tab: phiên được xoá sau 15 phút (mặc định của Flet là 1 giờ). Trên Linux, bộ cấp phát
    bộ nhớ được giới hạn 2 arena và trả RAM thừa về hệ điều hành 5 phút một lần (`main.py`).
- Scan: điểm đặc trưng của tranh gốc được tính sẵn trong `aura/scan_refs.npz` (~0,5 MB), máy chủ khỏi phải
  tính lúc chạy. **Thêm hoặc đổi ảnh tranh thì chạy `python -m aura.vision` để tạo lại** (quên cũng không
  sao: app tự nhận ra ảnh đã đổi và tính lại bức đó, chỉ chậm hơn lần đầu).
- Nút chụp ở Scan dùng `action=ft.PickFiles(...)`: trình duyệt mở hộp chọn ảnh ngay trong cú chạm. Safari
  trên iPhone chặn hộp chọn tệp nếu lệnh mở phải đi vòng qua máy chủ Python (cách `pick_files()`).

## Kiểm thử

```bash
python tests/test_auth_flow.py   # luồng OAuth Google với máy chủ giả lập, không cần mạng
```
