# Frontend

UI chatbot web chạy tách khỏi backend.

Backend API mặc định:

```text
http://localhost:8000
```

Chạy frontend:

```bash
cd /home/minhmh/tool/robo/frontend
python3 -m http.server 5173
```

Mở:

```text
http://localhost:5173
```

Nếu backend chạy host/port khác, chỉnh `API_BASE_URL` trong `app.js`.

## Auth MVP

Frontend có màn hình đăng nhập riêng trước khi vào chatbot. Khi nhập email/password hợp lệ, UI gọi `/auth/login`, lưu access token + refresh token vào `localStorage`, sau đó gửi:

```text
Authorization: Bearer <token>
```

cho các request `/ask`.

Khi bấm đăng xuất, UI gọi `/auth/logout` để revoke session server-side rồi mới xóa token local.

Tài khoản demo hiện dùng chung mật khẩu `demo123`:

```text
patient.demo@robo.local   -> patient
doctor@clinic.local       -> doctor
receptionist@clinic.local -> receptionist
admin@clinic.local        -> clinic_admin
system.admin@robo.local   -> system_admin
```

Guest có thể vào chatbot mà không cần token, nhưng dữ liệu cá nhân vẫn bị policy guard chặn. Token hiện là MVP HMAC local có `session_id`; account/password/session dùng schema `robo_auth`.

Nếu access token hết hạn, UI gọi `/auth/refresh` để rotate refresh token và lấy access token mới. Nếu refresh cũng lỗi, UI xóa session local và quay về màn login.

UI có form đổi mật khẩu trong phần tài khoản sau khi đăng nhập. Form này gọi `/auth/change-password`; đổi xong backend revoke các session khác của cùng account.

Màn login có phần quên mật khẩu. Flow này gọi:

```text
POST /auth/password-reset/request
POST /auth/password-reset/complete
```

Mặc định backend không trả reset token về UI. Khi test local/dev có thể bật `AUTH_PASSWORD_RESET_EXPOSE_TOKEN=true` để UI nhận token và điền vào form reset. Môi trường thật cần gắn provider gửi email/SMS/OTP riêng.

Nếu đăng nhập bằng `clinic_admin` hoặc `system_admin`, sidebar có nút `Quản trị tài khoản`. Panel này gọi các API `/auth/admin/...` để:

- xem danh sách account trong phạm vi quyền;
- xem role, identity mapping và session;
- mở khóa account bị lock;
- thu hồi session của account.

UI này là công cụ vận hành cơ bản, chưa phải màn tạo/sửa role phức tạp.

Trace header trong màn chat hiển thị thêm request id rút gọn và latency của `/ask` để debug nhanh một lượt gọi.
