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

Frontend có màn hình đăng nhập riêng trước khi vào chatbot. Khi nhập email/password hợp lệ, UI gọi `/auth/login`, lưu token vào `localStorage`, sau đó gửi:

```text
Authorization: Bearer <token>
```

cho các request `/ask`.

Tài khoản demo hiện dùng chung mật khẩu `demo123`:

```text
patient.demo@robo.local   -> patient
doctor@clinic.local       -> doctor
receptionist@clinic.local -> receptionist
admin@clinic.local        -> clinic_admin
```

Guest có thể vào chatbot mà không cần token, nhưng dữ liệu cá nhân vẫn bị policy guard chặn. Token hiện là MVP HMAC local; account/password dùng schema `robo_auth`.
