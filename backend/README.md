# Backend API

Backend này được scaffold theo hướng **core + domain adapter** để sau này thêm LLM, RAG và các domain khác mà không phải viết lại core.

## Kiến trúc

```text
POST /ask
  -> core/orchestrator.py
  -> llm/llm_client.py hoặc rule fallback để parse intent/entities
  -> core/decision_router.py
  -> auth/policy_guard.py
  -> core/tool_registry.py
  -> domains/clinic/adapter.py
  -> domains/clinic/sql_tools.py
  -> rag/embedding_client.py + rag/qdrant_store.py nếu là knowledge_search
  -> rag/grounded_response_generator.py cho grounded/LLM-formatted answers nếu có context
  -> core/response_generator.py template fallback
```

Hiện MVP hỗ trợ domain đầu tiên:

```text
clinic
```

Các intent đã có:

- `general_info`
- `greeting`
- `service_price`
- `service_category_list`
- `service_catalog_summary`
- `service_category_detail`
- `doctor_schedule`
- `knowledge_search`
- `appointment_booking`
- `personal_data`
- `out_of_scope`

LLM chưa bắt buộc. Nếu chưa có API key, backend dùng rule-based router để chạy local.
Nếu bật `LLM_PROVIDER=openai`, `llm/llm_client.py` sẽ gọi OpenAI-compatible Chat Completions để parse intent/entities rồi vẫn đi qua `PolicyGuard` và tool như bình thường.

Quy ước LLM:

- LLM đầu flow: parse intent/entities.
- Backend quyết định route SQL/RAG/Auth và kiểm tra policy.
- LLM cuối flow:
  - `knowledge_search`: grounded answer từ RAG context.
  - Các câu SQL/Auth khác: local formatter chỉ chạy khi `LLM_PROVIDER=ollama`, để không gửi dữ liệu bệnh nhân lên cloud.
- SQL/RAG/API là nguồn sự thật; model không được tự bịa giá, lịch, địa chỉ hoặc dữ liệu cá nhân.

Auth/RBAC hiện có:

- `POST /auth/login` phát bearer token từ email/password trong `robo_auth.accounts` và tạo `robo_auth.sessions`
- `GET /auth/me` đọc bearer token, kiểm tra session còn active và trả auth context
- `POST /auth/logout` revoke session hiện tại
- `POST /auth/refresh` rotate refresh token
- `POST /auth/change-password` đổi password cho user đã đăng nhập và revoke các session khác
- `POST /auth/password-reset/request` + `/auth/password-reset/complete` tạo flow reset password bằng token có TTL
- `GET /auth/admin/accounts`, `GET /auth/admin/accounts/{account_id}`, `POST /auth/admin/accounts/{account_id}/unlock`, `POST /auth/admin/accounts/{account_id}/revoke-sessions` cho account admin vận hành
- `/ask` ưu tiên `Authorization: Bearer <token>`; payload `auth` là dev-only path và mặc định tắt
- request không có token sẽ được xem là `guest`
- dữ liệu cá nhân bị chặn bởi `PolicyGuard`
- request có `auth.role=patient` và `patient_id` được tra lịch hẹn của chính patient đó
- request có `auth.role=doctor` và `doctor_id` được tra lịch hẹn của bác sĩ đó
- request có `auth.role=receptionist` hoặc `clinic_admin` và `clinic_id` được tra lịch hẹn trong clinic đó
- audit ghi application logger và `robo_auth.audit_events`
- request observability có `X-Request-ID`, `X-Process-Time-Ms`, `/ask.request_id`, `/ask.latency_ms`
- account admin API chỉ cho `clinic_admin` trong clinic scope hoặc `system_admin` toàn hệ thống
- chưa gắn provider email/SMS/OTP thật; reset token foundation đã có và mặc định không expose token ra API

Tài khoản demo:

```text
patient.demo@robo.local   / demo123 -> patient
doctor@clinic.local       / demo123 -> doctor
receptionist@clinic.local / demo123 -> receptionist
admin@clinic.local        / demo123 -> clinic_admin
```

## Cài dependency

```bash
cd /home/minhmh/tool/robo/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Cấu hình

Tạo `.env` trong thư mục `backend/`:

```bash
cp .env.example .env
```

Sửa `DATABASE_URL` theo password local của bạn:

```text
DATABASE_URL=postgresql://minhmh:YOUR_PASSWORD@localhost:5432/robo_reception
```

Nếu chạy trên cùng WSL user `minhmh`, có thể dùng local socket và không cần ghi password:

```text
DATABASE_URL=postgresql:///robo_reception
```

Mặc định có thể giữ:

```text
LLM_PROVIDER=none
```

Nếu muốn bật LLM:

```text
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT_SECONDS=20
LLM_INTENT_TIMEOUT_SECONDS=8
LLM_ANSWER_TIMEOUT_SECONDS=8
LLM_CONTEXT_CHAR_LIMIT=3500
OPENAI_API_KEY=your_api_key_here
```

Sau khi sửa `.env`, restart backend. Nếu LLM lỗi hoặc thiếu key, backend tự fallback về rule parser.

Auth password/token MVP dùng HMAC secret local:

```text
AUTH_TOKEN_SECRET=change-this-local-secret
AUTH_TOKEN_TTL_SECONDS=86400
AUTH_REFRESH_TOKEN_TTL_SECONDS=2592000
AUTH_ALLOW_REQUEST_CONTEXT=false
AUTH_ALLOW_LEGACY_ROLE_LOGIN=false
AUTH_MAX_FAILED_LOGIN_ATTEMPTS=5
AUTH_LOCK_SECONDS=900
AUTH_MIN_PASSWORD_LENGTH=8
AUTH_LOGIN_RATE_LIMIT_ATTEMPTS=10
AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
```

`AUTH_ALLOW_REQUEST_CONTEXT` và `AUTH_ALLOW_LEGACY_ROLE_LOGIN` chỉ nên bật khi debug đường auth cũ. Productization flow dùng email/password, nhận access token + refresh token, rồi gửi `Authorization: Bearer <token>` vào `/ask`.

`AUTH_MAX_FAILED_LOGIN_ATTEMPTS` và `AUTH_LOCK_SECONDS` điều khiển khóa account tạm thời khi nhập sai mật khẩu nhiều lần.
`AUTH_LOGIN_RATE_LIMIT_ATTEMPTS` và `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS` giới hạn số lần gọi login theo IP/email trong một cửa sổ thời gian. `AUTH_MIN_PASSWORD_LENGTH` áp dụng cho `/auth/change-password`.

Nếu muốn dùng Ollama local:

```text
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b
LLM_BASE_URL=http://localhost:11434
LLM_TIMEOUT_SECONDS=60
LLM_INTENT_TIMEOUT_SECONDS=8
LLM_ANSWER_TIMEOUT_SECONDS=8
LLM_CONTEXT_CHAR_LIMIT=3500
```

Sau đó chạy:

```bash
ollama pull qwen2.5:3b
ollama serve
```

Backend vẫn dùng cùng flow `LLM -> Intent -> PolicyGuard -> ToolRegistry`.

### RAG vector

RAG vector hiện dùng Qdrant local mode:

```text
scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Ollama nomic-embed-text
  -> qdrant_data / clinic_knowledge
  -> robo_rag.index_manifest
```

Hiện flow nguồn là:

```text
robo_raw.admin_help_templates
  -> robo_app.knowledge_articles
  -> scripts/rag_documents.py
```

Build index:

```bash
cd /home/minhmh/tool/robo
scripts/apply_rag_schema.sh
backend/.venv/bin/python scripts/check_rag_registry.py
backend/.venv/bin/python scripts/build_qdrant_index.py --mode full
```

`robo_rag.index_manifest` lưu các point đã index theo collection/source/document/chunk/hash để chuẩn bị incremental sync. Qdrant vẫn là vector store chính; manifest chỉ là tracking trong Postgres.

Sau khi đã có collection và manifest, có thể sync phần thay đổi:

```bash
backend/.venv/bin/python scripts/build_qdrant_index.py --mode incremental
```

Khi `knowledge_search`, backend sẽ query Qdrant trước. Nếu Qdrant chưa có index, không có kết quả đạt `RAG_MIN_SCORE`, hoặc lỗi, backend fallback về keyword/fuzzy search từ cùng registry `scripts/rag_documents.py`.

RAG retrieval loại các topic không phù hợp để trả lời bệnh nhân theo `RAG_EXCLUDED_TOPICS`, mặc định:

```text
overview,roles
```

Mục tiêu là không đưa tài liệu platform/system overview hoặc phân quyền vào context trả lời các câu hỏi quy trình của bệnh nhân. Sau khi đổi danh sách này hoặc sửa dữ liệu knowledge, cần rebuild Qdrant index.

Ở giai đoạn hiện tại, `knowledge_search` đã dùng grounded response generation để LLM viết câu trả lời tự nhiên hơn từ `ToolResult.rows`, RAG chunks và `sources`. Context đưa vào LLM chỉ giữ title và nội dung chính của tài liệu; nếu LLM timeout hoặc tắt, template fallback vẫn format markdown thành danh sách dễ đọc thay vì trả content thô.

Với các kết quả SQL/Auth như thông tin phòng khám, giá dịch vụ chính xác, lịch hẹn cá nhân và kết quả xét nghiệm, backend có thể dùng Ollama local để format câu trả lời từ `ToolResult.rows`. Formatter này chỉ chạy với `LLM_PROVIDER=ollama`; nếu provider là cloud hoặc LLM lỗi/tắt, `ResponseGenerator` template vẫn là fallback. Các câu dạng danh sách đã có template tốt, ví dụ nhóm dịch vụ, tổng quan danh mục dịch vụ, chi tiết dịch vụ trong một nhóm hoặc service_price nhiều dòng, sẽ không ép qua LLM để tránh timeout và tránh LLM chọn thiếu dữ liệu.

## File chính

```text
app/config.py                 đọc env DB, LLM, embedding, Qdrant
app/db.py                     helper Postgres
app/api/ask.py                endpoint POST /ask
app/core/orchestrator.py      điều phối toàn bộ flow
app/core/response_generator.py template answer hiện tại
app/llm/llm_client.py         LLM intent parser và formatter local
app/rag/grounded_response_generator.py LLM answer từ context
app/rag/embedding_client.py   Ollama embedding client
app/rag/qdrant_store.py       Qdrant local/server vector store
app/rag/rag_config.py         RAG top-k, min score, fallback limit/confidence
app/auth/policy_guard.py      kiểm tra quyền trước khi gọi tool
app/auth/auth_context.py      resolve auth context
app/auth/permissions.py       permission matrix
app/domains/clinic/sql_tools.py SQL tools + Qdrant knowledge_search
```

## Chạy server

```bash
cd /home/minhmh/tool/robo/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

UI chatbot chạy tách ở thư mục `frontend/`.

## Test API

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"CT Brain without contrast giá bao nhiêu?"}'
```

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hôm nay bác sĩ SUON SAVUTH có khám không?"}'
```

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Địa chỉ phòng khám ở đâu?"}'
```

## Lộ trình tiếp theo

Sau khi API text, UI, LLM parser, Qdrant RAG và grounded answer chạy ổn:

1. Thêm auth tool cho dữ liệu cá nhân.
2. Mở rộng grounded answer sang intent phù hợp khác nếu cần.
3. Thêm domain adapter mới như `hotel`, `restaurant`, `school`.
