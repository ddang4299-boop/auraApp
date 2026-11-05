# Báo cáo xây dựng giao diện ứng dụng AURA

*Ngày 04/11/2026 · Phạm vi: toàn bộ giao diện theo bản thiết kế `sample.pdf`, cộng thêm phần đăng nhập Google/Facebook và trang Hồ sơ theo yêu cầu bổ sung.*

---

## 1. Tóm tắt

- Đã dựng **13 màn hình**: 11 màn theo bản thiết kế, cộng **Đã lưu** và **Hồ sơ** (hai màn này không có trong bản mẫu nên được thiết kế cùng phong cách).
- Ngôn ngữ: **Python**. Framework: **Flet 1.0.5**. Flet dựng giao diện bằng Flutter, nên cùng một mã nguồn chạy được trên Android, iOS, máy tính và web, và đóng gói được thành `.apk` / `.ipa`.
- Giao diện được **tự chụp và so với bản mẫu qua 8 vòng**. Sau vòng cuối, phần lớn màn hình lệch dưới ~5pt so với thiết kế (bảng ở mục 5).
- **Kiểm thử tự động end-to-end: 14/14 đạt.** Bài kiểm thử bấm thật trên giao diện qua các luồng đăng nhập, hồ sơ, kho tranh, chat, quiz và đăng xuất.
- Phần **nội dung hội thoại** hiện là dữ liệu mẫu chép từ bản thiết kế. Giao diện đã tách riêng một "điểm cắm" (`SocraticEngine`) để gắn JSON hội thoại và engine đọc JSON của thành viên khác **mà không phải sửa màn hình nào**.

---

## 2. Luồng làm việc

```
 sample.pdf ──► (1) Phân tích ──► (2) Design tokens ──► (3) Component ──► (4) Màn hình
                                                                              │
              (7) Báo cáo ◄── (6) Kiểm thử E2E ◄── (5) Vòng chụp & so sánh ◄──┘
                                                       ▲            │
                                                       └── sửa ◄────┘  (lặp 8 vòng)
```

**(1) Phân tích bản thiết kế.** Dùng PyMuPDF đọc PDF và trích:
- kích thước khung (402pt, iPhone 16 Pro), vị trí và cỡ chữ của **từng dòng chữ**,
- 4 ảnh tranh gốc, và toạ độ vùng cắt (crop) của ảnh trên từng màn,
- màu sắc, bằng cách lấy mẫu điểm ảnh trên bản render 2×.

**(2) Design tokens.** Gom toàn bộ màu, font, khoảng cách dòng và bo góc vào `aura/theme.py`. Font được xác định bằng cách **đo độ rộng chữ** và so với PDF:
- Inter cho thân bài: khớp gần như tuyệt đối,
- Lora cho tiêu đề, kèm letter-spacing −2%,
- Montserrat cho logo.

**(3) Component dùng chung** (`aura/ui.py`): chữ, nút, chip, thẻ, ảnh có vùng cắt, top bar, thanh điều hướng, avatar, khung màn hình (SafeArea).

**(4) Màn hình.** Mỗi màn là một file trong `aura/screens/`. Khoảng cách giữa các khối được tính từ toạ độ chữ trích ở bước 1.

**(5) Vòng chụp & so sánh.**
- App chạy ở chế độ web với khung iPhone giả lập.
- Playwright mở Chrome và chụp từng màn **đúng chiều cao trang PDF tương ứng**.
- Script ghép ảnh *bản mẫu | app | chồng lớp* và tính điểm lệch trung bình.
- Đọc ảnh ghép, sửa code, rồi chụp lại. Lặp 8 vòng.

**(6) Kiểm thử end-to-end.** Điều khiển app trong trình duyệt bằng cây accessibility của Flutter: bấm nút, cuộn, kiểm tra nội dung xuất hiện.

---

## 3. Công nghệ và công cụ

| Nhóm | Công nghệ / công cụ | Vai trò |
|---|---|---|
| Ứng dụng | **Python 3.10**, **Flet 1.0.5** (Flutter) | Viết UI bằng Python, build Android/iOS |
| Đăng nhập | **OAuth 2.0 + PKCE**, `httpx` | Google / Facebook, mở trình duyệt hệ thống và nhận kết quả qua loopback |
| Lưu trữ | `ft.SharedPreferences` | Nhớ phiên đăng nhập và hồ sơ trên máy |
| Font | Inter, Lora, Montserrat (SIL OFL) + `fontTools` | Tạo bản font tĩnh theo từng độ đậm từ font biến thiên |
| Icon | Lucide (ISC) | Icon nét mảnh giống bản thiết kế |
| Phân tích PDF | **PyMuPDF** | Trích chữ, toạ độ, ảnh; render trang |
| Xử lý ảnh | **Pillow**, NumPy | Lấy mẫu màu, ghép ảnh so sánh, tính độ lệch |
| Chụp & kiểm thử | **Playwright** + Google Chrome (headless) | Chụp màn hình, kiểm thử E2E |
| Môi trường | `venv`, Windows 11 | — |

---

## 4. Kiến trúc mã nguồn

```
main.py               khởi chạy
aura/theme.py         design tokens
aura/ui.py            component dùng chung
aura/data.py          nội dung tranh, mốc thời gian, quiz
aura/socratic.py      interface SocraticEngine + kịch bản mẫu
aura/auth.py          đăng nhập Google/Facebook
aura/app.py           điều hướng (stack màn hình, nút Back Android), trạng thái, phiên đăng nhập
aura/screens/*.py     13 màn hình
tests/                test_auth_flow.py
```

**Điểm cắm cho chatbot.** Màn chat chỉ gọi hai hàm `start()` và `reply()` của `SocraticEngine`. Khi có JSON hội thoại và engine đọc JSON, chỉ cần một adapter nhỏ chuyển kết quả của engine sang `AuraTurn`, gồm:
- đoạn văn,
- gợi ý trả lời,
- giai đoạn (Ấn tượng đầu → Tách chi tiết → Đối thoại → Mở rộng),
- ảnh chi tiết, thẻ tổng kết, nguồn.

---

## 5. Kết quả đo

Điểm lệch là độ chênh trung bình của điểm ảnh giữa bản mẫu và ảnh chụp app (thang 0–255, càng thấp càng giống).

| Màn | Vòng đầu | Vòng cuối | Ghi chú |
|---|---|---|---|
| Chào mừng | 7.6 | 8.0 | Ảnh bản mẫu bị kéo giãn dọc; app giữ đúng tỉ lệ tranh |
| Số điện thoại | 23.0 | 4.7 | Vòng đầu bị lỗi ô nhập (API Flet 1.0), đã sửa |
| OTP | — | 4.2 | |
| Khám phá | — | 10.0 | Thêm avatar góc phải theo yêu cầu |
| Kho tranh | 37.1 | 12.8 | Đã sửa khung ảnh thẻ nổi bật và thứ tự lưới |
| Tổng quan tranh | — | 8.0 | |
| Hỏi Aura (chat) | 24.5 | 16.4 | Bản mẫu cố định dòng "AURA đang suy nghĩ…"; app chỉ hiện khi đang chờ |
| Quiz (đã chấm) | — | 16.6 | |
| Kết quả | — | 9.5 | |
| Chi tiết tranh | — | 4.8 | |
| Quiz (thử lại) | 23.4 | 17.8 | |

**Kiểm thử E2E 14/14 đạt:**
- hộp thoại cấu hình Google → dùng thử → vào Khám phá,
- avatar → Hồ sơ (đúng tên, đúng trạng thái liên kết),
- lọc kho tranh,
- chat: chọn gợi ý → "đang suy nghĩ" → AURA trả lời kèm ảnh chi tiết,
- quiz: chọn sai → thử lại → đúng → câu 2 → "Xuất sắc 2/2",
- đăng xuất: xác nhận → về màn chào.

**Luồng OAuth:** kiểm thử với máy chủ Google giả lập đạt (PKCE S256, callback loopback 200, lấy được tên/email).

---

## 6. Sự cố gặp phải và cách xử lý

| Sự cố | Nguyên nhân | Cách xử lý |
|---|---|---|
| Chữ rộng hơn bản mẫu khoảng 5% | Theme Material 3 mặc định cộng letter-spacing 0.25 | Luôn đặt letter-spacing rõ ràng |
| Font đậm không ăn | Flutter không tự chọn độ đậm của font biến thiên | Tạo font tĩnh theo từng độ đậm |
| Server web không phản hồi | Flet 1.0 chạy chế độ socket thay vì web | Dùng `FLET_FORCE_WEB_SERVER` |
| Chụp màn hình treo ngẫu nhiên | GPU ảo của Chrome headless | Thêm `--disable-gpu`, chụp qua CDP, tự thử lại; chạy thử 5/5 lần thành công |
| Nút Google không phản hồi | Sai chữ hoa/thường của khoá nhà cung cấp | Sửa khoá thành chữ thường (lỗi thật do kiểm thử E2E phát hiện) |
| Callback OAuth sẵn có của Flet không dùng được | Chỉ chạy ở chế độ web | Tự viết luồng OAuth loopback chuẩn cho app cài đặt (RFC 8252) |

---

## 7. Hạn chế và việc cần làm tiếp

1. **Khoá đăng nhập thật.** Cần tạo OAuth client trên Google Cloud và Facebook Developers rồi điền vào `.env` (hướng dẫn trong README). Chưa thử với tài khoản thật. Khi chưa có khoá, app hiện nút **Dùng thử**.
2. **Phát hành trên điện thoại.** Luồng loopback phù hợp cho máy tính và bản thử. Bản phát hành chính thức trên Android/iOS nên chuyển sang Google Sign-In / Facebook SDK gốc hoặc Firebase Auth, và **không nhúng client secret**.
3. **Đăng nhập số điện thoại.** Giao diện và kiểm tra định dạng đã có, nhưng chưa gửi SMS OTP thật (cần dịch vụ như Firebase Phone Auth).
4. **Nội dung hội thoại.** Đang là kịch bản mẫu; chờ JSON và engine của thành viên khác.
5. **Nội dung 3 tranh còn lại** (Người đàn ông đội khăn đỏ, Đức Mẹ hoa cẩm chướng, Léal Souvenir) do mình soạn ngắn gọn, có dè dặt ở các điểm chưa chắc chắn. Nhóm nên **rà lại tính chính xác**. Quiz hiện chỉ có cho bức Arnolfini.
6. **Lệch dọc nhỏ.** Chữ của app nằm cao hơn bản mẫu khoảng 2–4pt do cách Flutter phân bổ khoảng cách dòng; mắt thường khó nhận ra.
7. **Chưa build thử** `.apk` / `.ipa`. Cấu hình build đã có trong `pyproject.toml`.

---

## 8. Cách chạy

```bash
.venv\Scripts\activate
flet run main.py                 # cửa sổ cỡ điện thoại trên máy tính
flet run --android main.py       # điện thoại Android cài app "Flet", cùng mạng Wi-Fi
python tests/test_auth_flow.py   # kiểm thử luồng OAuth
```

*Ghi chú: các script chụp/so sánh và kiểm thử E2E ở mục 2 và 5 đã được gỡ khỏi repo sau khi hoàn tất.*
