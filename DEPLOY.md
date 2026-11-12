# Đưa AURA lên mạng (Render) để người khác dùng thử, có AI

Sau khi làm xong, bạn có một đường link dạng `https://aura-xxxx.onrender.com`. Ai mở link
(máy tính hay điện thoại) cũng dùng được app, kể cả chat AI. Phần Python và **key AI nằm trên
máy chủ Render**, người dùng không bao giờ thấy key.

Các file đã chuẩn bị sẵn trong dự án:

| File | Dùng để |
|---|---|
| `render.yaml` | Bảng cấu hình: Render đọc file này để biết cài gì, chạy lệnh gì |
| `requirements-server.txt` | Danh sách thư viện cho máy chủ (app web + AI) |
| `main.py` | Khi có biến `PORT` (Render tự đặt) thì chạy ở chế độ máy chủ web |

## Bước 1. Đưa code mới nhất lên GitHub

Render lấy code từ GitHub, nên mọi thay đổi phải được đẩy lên trước:

```
git add -A
git commit -m "Chuẩn bị triển khai lên Render"
git push
```

File `.env` (chứa key) nằm trong `.gitignore` nên **không** bị đẩy lên. Đúng như vậy là tốt.

## Bước 2. Tạo tài khoản Render

1. Vào https://render.com, chọn **Get Started**.
2. Đăng nhập bằng **GitHub** (tiện nhất, Render sẽ thấy được repo của bạn).
3. Cho phép Render truy cập repo `auraApp`.

## Bước 3. Tạo dịch vụ từ file render.yaml

1. Trong trang quản lý (Dashboard), bấm **New +** → **Blueprint**.
2. Chọn repo `auraApp`. Render tự tìm thấy `render.yaml` và hiện dịch vụ tên `aura`.
3. Render hỏi giá trị cho hai key bí mật. Dán key thật (giống trong file `.env` trên máy bạn):
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY`
4. Bấm **Apply** / **Deploy Blueprint**.

Render bắt đầu cài thư viện và chạy app, mất khoảng 3–5 phút. Theo dõi ở tab **Logs**. Khi
thấy dịch vụ ở trạng thái **Live** là xong.

## Bước 4. Mở link và gửi cho người khác

Đường link nằm ở đầu trang dịch vụ (dạng `https://aura-xxxx.onrender.com`). Mở thử trên máy
bạn, rồi gửi cho bạn bè. Trên iPhone có thể bấm **Chia sẻ → Thêm vào MH chính** để có biểu
tượng như app thật.

## Cập nhật app về sau

Mỗi lần `git push` code mới, Render **tự** cài lại và chạy bản mới (mất vài phút).

Đổi key: vào dịch vụ `aura` → **Environment** → sửa giá trị → **Save**. Render tự khởi động lại.

## Những điều cần biết

- **Vì sao bản trên mạng chậm hơn trên máy?** Giao diện chạy trên điện thoại người dùng nhưng
  Python chạy trên máy chủ: mỗi lần bấm phải đi qua mạng tới máy chủ rồi về. Vì vậy máy chủ nên
  đặt ở **Singapore** (`region: singapore` trong `render.yaml`, gần Việt Nam nhất). Vùng máy chủ
  **không đổi được** sau khi tạo: muốn đổi phải xoá dịch vụ cũ rồi tạo Blueprint mới.
- Gói miễn phí chỉ có khoảng 0,1 CPU nên vẫn chậm hơn chạy trên máy. Code đã được tối ưu để mỗi
  lần bấm tốn ít CPU nhất có thể (chuyển màn một lượt đi-về, Trang chủ được giữ sẵn, bỏ log thừa
  của Flet), nhưng mở Kho tranh / trang tranh vẫn mất khoảng nửa giây đến một giây trên gói miễn
  phí. Muốn mượt hẳn cần gói trả phí (Starter, 0,5 CPU) — chỉ nên nâng khi thật sự cho nhiều người dùng.

- **Gói miễn phí sẽ "ngủ"** khi 15 phút không có ai dùng. Người mở link đầu tiên sau đó phải
  chờ khoảng 1 phút để máy chủ thức dậy; các lần sau thì nhanh.
- **Hạn mức AI dùng chung.** Mọi người dùng chung key của bạn: Gemini miễn phí ~20 lượt/ngày,
  hết thì tự sang Groq (`LLM_FALLBACK=groq,groq:openai/gpt-oss-20b`: hai model Groq, mỗi model
  8.000 token/phút riêng), cả hai cùng hết thì AURA trả lời bằng phản hồi viết sẵn (vẫn dùng được).
  Bấm nút gợi ý không tốn lượt AI; chỉ câu tự gõ mới gọi AI. Nếu Render không tự lấy giá trị
  `LLM_FALLBACK` mới từ `render.yaml`, vào **Environment** sửa tay thành giá trị trên.
- **Đăng nhập Google**: bấm "Tiếp tục với Google" thì cả tab chuyển sang trang Google, đăng nhập
  xong quay về app. Cần:
  1. Google Cloud → Google Auth Platform → **Clients** → client loại **Web application**, mục
     *Authorized redirect URIs* có `https://<link-render>/oauth_callback`.
  2. `GOOGLE_CLIENT_ID` (đã ghi trong `render.yaml`) và `GOOGLE_CLIENT_SECRET` (nhập ở
     **Environment** trên Render, không ghi vào file).
  3. Google Auth Platform → **Audience**: khi còn "Testing" chỉ các email trong *Test users* đăng
     nhập được; bấm **Publish app** để ai cũng đăng nhập được.
  Chưa có secret thì nút Google hiện hộp thoại với lựa chọn **Dùng thử**; luôn có thể **Bỏ qua**.
- **Dữ liệu không được lưu lâu dài**: lịch sử chat, tranh đã lưu sẽ mất khi máy chủ khởi động
  lại. Với bản dùng thử như vậy là đủ.
- **Không bao giờ** dán key vào `render.yaml`, `README.md` hay bất kỳ file nào đưa lên GitHub.
