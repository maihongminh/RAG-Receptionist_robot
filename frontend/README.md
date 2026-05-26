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

Panel bên trái có thể gửi auth context mock cùng request `/ask`:

```text
guest          -> không gửi auth, dữ liệu cá nhân bị chặn
patient        -> cần patient_id
doctor         -> cần doctor_id
receptionist   -> cần clinic_id
clinic_admin   -> cần clinic_id
```

Panel này chỉ phục vụ demo/MVP. Login/OTP/JWT thật sẽ làm ở backend sau.
