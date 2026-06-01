# MVP snapshot

Thư mục này mô tả trạng thái MVP đã hoàn thành và được lưu tại branch:

```text
mvp-v1
```

Commit MVP:

```text
e8477eb Add email password auth login
```

Mục đích của `docs/mvp/`:

- giữ lại phạm vi MVP để sau này xem lại đường đi của project;
- tránh nhầm với phase productization đang phát triển trên `main`;
- ghi rõ những gì MVP đã có, chưa có, và cách chạy/test lại MVP.

## MVP đã có gì?

- Backend FastAPI với API chính `POST /ask`.
- Frontend chatbot web.
- Login email/password MVP.
- Bearer token cho `/ask`.
- RBAC/policy guard theo role.
- SQL tools cho dữ liệu phòng khám:
  - thông tin clinic;
  - dịch vụ/giá;
  - lịch bác sĩ;
  - lịch hẹn;
  - kết quả cận lâm sàng.
- RAG bằng Qdrant cho knowledge/procedure.
- Local Ollama LLM parser/formatter có fallback rule/template.
- Short session context cho follow-up:
  - `xem tiếp`;
  - `các nhóm còn lại`;
  - `xem chi tiết nhóm 35`.
- Trace panel để debug parser/source/data.

## MVP chưa phải production

- MVP ban đầu dùng account demo; productization đã bắt đầu tách account sang `robo_auth`.
- Chưa có refresh token/logout server-side.
- Chưa có OTP/reset password.
- Audit log chưa ghi DB.
- RAG build thủ công, chưa tự sync khi DB thay đổi.
- Chưa mở rộng hết 56 bảng.
- Chưa có Docker/deployment production.

## Tài liệu trong thư mục

```text
docs/mvp/
├── README.md
├── SCOPE.md
├── TEST_ACCOUNTS.md
└── TEST_PLAN.md
```

Đọc tiếp:

1. `SCOPE.md`: phạm vi MVP và các luồng chính.
2. `TEST_ACCOUNTS.md`: account demo.
3. `TEST_PLAN.md`: câu hỏi/test smoke cho MVP.
