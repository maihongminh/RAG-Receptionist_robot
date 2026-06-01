# Productization audit, deployment and test plan

Tài liệu này gom ba phần cần làm trước khi hệ thống tiến gần production:

- audit/observability;
- test strategy;
- deployment/run environment.

## 1. Audit log DB

Hiện đã có audit DB nền tảng trong `robo_auth.audit_events`.

Schema hiện tại:

```text
robo_auth.audit_events
  id
  event_type
  account_id
  session_id
  user_id
  role
  clinic_id
  intent
  tool_name
  source
  allowed
  reason
  row_count
  request_id
  latency_ms
  metadata
  created_at
```

Đang ghi:

```text
login_success
login_failed
logout_success
policy_decision
tool_result
```

Mỗi HTTP request có:

- `X-Request-ID`: nhận từ client nếu có, nếu không backend tự sinh UUID;
- `X-Process-Time-Ms`: tổng thời gian xử lý request;
- `/ask` response trả thêm `request_id` và `latency_ms`;
- audit DB ghi cùng `request_id` và `latency_ms` để lần vết các event của một lượt gọi.

Các event cần mở rộng thêm:

- token invalid/expired;
- refresh token;
- RAG internal/private source access nếu có.

Không ghi:

- password plaintext;
- full token;
- full sensitive response nếu không cần.

## 2. Observability

Đã có:

- request_id;
- latency tổng;

Cần log kỹ thuật thêm:

- latency intent parser;
- latency SQL/RAG/LLM;
- parser source;
- answer source;
- tool source;
- top score RAG;
- error/fallback reason.

Trace UI:

- dev: có thể hiện data preview;
- production: tắt hoặc mask dữ liệu nhạy cảm;
- admin-only nếu cần debug.

## 3. Test strategy

### Unit tests

- intent parser;
- policy guard;
- auth token/password/session;
- response generator;
- SQL query builders/helpers;
- RAG config/document registry.

### Integration tests

Dùng Postgres test DB hoặc local seeded DB:

- login bằng email/password;
- patient hỏi lịch hẹn;
- doctor hỏi lịch bệnh nhân;
- receptionist/clinic_admin theo clinic;
- guest bị chặn private data;
- service price exact/generic;
- clinic public info;
- RAG check-in/result process.

### E2E smoke

Qua HTTP:

```text
POST /auth/login
GET /auth/me
POST /ask public
POST /ask private
POST /ask RAG
```

Frontend smoke:

- login form hiển thị riêng;
- login success vào chat;
- logout quay về login;
- long chat không phá layout;
- trace/data preview scroll ổn.

## 4. Deployment plan

Mục tiêu đầu:

```text
docker compose up
```

Services:

- `postgres`
- `qdrant`
- `backend`
- `frontend`
- `ollama` optional

Config:

- `.env.example` cho dev;
- `.env.production.example` nếu cần;
- secret không commit;
- volume cho Postgres/Qdrant/Ollama.

## 5. Healthcheck

Backend nên có:

```text
GET /health
GET /ready
```

`/health`:

- process sống.

`/ready`:

- DB connect được;
- Qdrant connect được nếu enabled;
- LLM/Ollama optional tùy config.

## 6. Release checklist

Trước mỗi commit/merge lớn:

- `python -m pytest`;
- MVP scenario script;
- node syntax check frontend;
- docs cập nhật nếu đổi flow;
- DB migration/seed idempotent;
- không commit `.env`;
- không commit cache.

Trước demo:

- rebuild app views;
- seed demo;
- rebuild Qdrant nếu đổi RAG docs;
- restart backend/frontend;
- test login 4 role demo;
- test public/private/RAG câu chính.
