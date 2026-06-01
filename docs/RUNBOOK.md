# Hướng dẫn chạy project

Project hiện có 2 phần chạy riêng:

```text
backend  -> FastAPI API, port 8000
frontend -> Chatbot UI tĩnh, port 5173
```

Database local:

```text
Postgres database: robo_reception
Schema raw:        robo_raw
Schema app:        robo_app
```

## 1. Chạy backend

Mở terminal 1:

```bash
cd /home/minhmh/tool/robo/backend
source .venv/bin/activate
DATABASE_URL="postgresql:///robo_reception" uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Nếu chưa có `.venv` hoặc chưa cài dependency:

```bash
cd /home/minhmh/tool/robo/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Sau đó chạy lại lệnh backend ở trên.

Kiểm tra backend:

```bash
curl http://localhost:8000/health
```

Kết quả đúng:

```json
{"status":"ok"}
```

API docs:

```text
http://localhost:8000/docs
```

### Bật/tắt LLM

Mặc định backend chạy không cần LLM:

```text
LLM_PROVIDER=none
```

Khi để như trên, backend dùng rule parser local nên vẫn hỏi đáp được không cần API key.

Nếu muốn bật LLM OpenAI-compatible để parse intent/entities, sửa `backend/.env`:

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

Sau khi sửa `.env`, restart backend.

Nếu muốn dùng LLM local miễn phí qua Ollama, cài Ollama rồi sửa `backend/.env`:

```text
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b
LLM_BASE_URL=http://localhost:11434
LLM_TIMEOUT_SECONDS=60
LLM_INTENT_TIMEOUT_SECONDS=8
LLM_ANSWER_TIMEOUT_SECONDS=8
LLM_CONTEXT_CHAR_LIMIT=3500
```

Ý nghĩa các timeout:

- `LLM_INTENT_TIMEOUT_SECONDS`: thời gian chờ LLM phân loại intent. Nên thấp vì nếu chậm backend sẽ dùng rule parser.
- `LLM_ANSWER_TIMEOUT_SECONDS`: thời gian chờ LLM diễn đạt câu trả lời từ dữ liệu đã truy xuất. Với máy 16GB RAM nên để thấp, vì template fallback đã được chuẩn hóa.
- `LLM_CONTEXT_CHAR_LIMIT`: giới hạn số ký tự context đưa vào LLM formatter/grounded answer.

Model gợi ý:

```text
qwen2.5:3b      máy nhẹ hơn
qwen2.5:7b      chất lượng tốt hơn, cần RAM nhiều hơn
llama3.2:3b     máy nhẹ hơn
llama3.1:8b     chất lượng tốt hơn, cần RAM nhiều hơn
```

Lệnh cài/chạy cơ bản:

```bash
ollama pull qwen2.5:3b
ollama serve
```

Nếu `ollama serve` báo port đã chạy rồi thì bỏ qua, chỉ cần restart backend.

Lưu ý:

- LLM chỉ phân loại intent và trích xuất entity.
- LLM không tự trả lời dữ liệu nghiệp vụ.
- Dữ liệu vẫn đi qua `DecisionRouter`, `PolicyGuard`, SQL/RAG/Auth tool và `ResponseGenerator`.
- Nếu LLM lỗi hoặc thiếu key, backend tự fallback về rule parser.
- Trên UI, panel `Trace` sẽ hiện `Parser: LLM` nếu OpenAI/Ollama được dùng thật; nếu hiện `Rule fallback` thì LLM chưa chạy hoặc đã fallback.

### RAG vector bằng Qdrant local

RAG vector dùng:

```text
scripts/rag_documents.py -> Ollama embedding -> Qdrant local qdrant_data
```

Postgres vẫn là nguồn dữ liệu gốc. Qdrant chỉ là vector index, có thể xóa và build lại.

Flow hiện tại:

```text
robo_raw.admin_help_templates
  -> robo_app.knowledge_articles
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Qdrant collection clinic_knowledge
```

Khi thêm nguồn mới:

```text
nhiều nguồn text hợp lệ
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Qdrant
```

Model embedding:

```bash
ollama pull nomic-embed-text
```

Cấu hình trong `backend/.env`:

```text
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_TIMEOUT_SECONDS=10
RAG_VECTOR_ENABLED=true
RAG_TOP_K=5
RAG_MIN_SCORE=0.75
RAG_KEYWORD_SOURCE_LIMIT=500
RAG_KEYWORD_TOP_K=3
RAG_KEYWORD_MIN_SCORE=0.18
RAG_CONTEXT_MAX_ROWS=5
RAG_API_PREVIEW_MAX_ROWS=50
RAG_SQL_RESULT_LIMIT=1000
RAG_EMPTY_CONFIDENCE=0.0
QDRANT_MODE=local
QDRANT_PATH=/home/minhmh/tool/robo/qdrant_data
QDRANT_COLLECTION=clinic_knowledge
```

Các tham số RAG này được gom trong:

```text
backend/app/rag/rag_config.py
```

Ý nghĩa:

```text
RAG_TOP_K                  số chunk vector tối đa lấy từ Qdrant
RAG_MIN_SCORE              ngưỡng similarity tối thiểu của Qdrant
RAG_KEYWORD_SOURCE_LIMIT   số row tối đa đọc từ fallback SQL keyword
RAG_KEYWORD_TOP_K          số kết quả fallback keyword tối đa trả về
RAG_KEYWORD_MIN_SCORE      ngưỡng score tối thiểu của keyword/fuzzy fallback
RAG_CONTEXT_MAX_ROWS       số row tối đa đưa vào LLM context/template answer
RAG_API_PREVIEW_MAX_ROWS   số row tối đa trả về frontend trong data preview/trace
RAG_SQL_RESULT_LIMIT       số row tối đa lấy từ SQL trước khi rank/group
RAG_EMPTY_CONFIDENCE       confidence khi không có kết quả
```

Build hoặc rebuild index:

```bash
cd /home/minhmh/tool/robo
backend/.venv/bin/python scripts/build_qdrant_index.py
```

Nếu backend đang chạy và Qdrant local báo lock `qdrant_data`, dừng backend rồi chạy lại script build index.

## 2. Chạy frontend

Mở terminal 2:

```bash
cd /home/minhmh/tool/robo/frontend
python3 -m http.server 5173
```

Mở trình duyệt:

```text
http://localhost:5173
```

Frontend mặc định gọi backend tại:

```text
http://localhost:8000
```

Nếu backend đổi port/host, sửa dòng này trong `frontend/app.js`:

```js
const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";
```

## 3. Test API bằng curl

Chào hỏi/giới thiệu bot:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"xin chào"}'
```

Hỏi thông tin chung:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Địa chỉ phòng khám ở đâu?"}'
```

Hỏi giá dịch vụ:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"CT Brain without contrast giá bao nhiêu?"}'
```

Hỏi lịch bác sĩ:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hôm nay bác sĩ SUON SAVUTH có khám không?"}'
```

Hỏi hướng dẫn/quy trình bằng RAG vector:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quy trình check-in bệnh nhân như thế nào?"}'
```

Kết quả đúng sẽ có source dạng:

```json
{
  "sources": ["qdrant:clinic_knowledge"]
}
```

Yêu cầu đặt lịch:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"đặt lịch"}'
```

Hỏi dữ liệu cá nhân:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Tôi có lịch hẹn nào không?"}'
```

Câu dữ liệu cá nhân phải trả về `requires_auth: true`.

Đăng nhập email/password MVP:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient.demo@robo.local","password":"demo123"}'
```

Response trả `access_token`. Dùng token để gọi `/ask`:

```bash
TOKEN="paste_access_token_here"

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question":"Tôi có lịch hẹn nào không?","domain":"clinic"}'
```

Kiểm tra token hiện tại:

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

Tài khoản demo:

```text
patient.demo@robo.local   / demo123 -> patient
doctor@clinic.local       / demo123 -> doctor
receptionist@clinic.local / demo123 -> receptionist
admin@clinic.local        / demo123 -> clinic_admin
```

Khi test LLM, response JSON có thêm:

```json
{
  "parser_source": "llm",
  "answer_source": "llm_grounded"
}
```

Nếu là:

```json
{
  "parser_source": "rule",
  "answer_source": "template"
}
```

thì backend đang dùng rule/template fallback.

Ý nghĩa `answer_source`:

```text
template      -> backend format bằng code
llm_grounded  -> LLM trả lời từ RAG context cho knowledge_search
llm_formatted -> Ollama local format dữ liệu SQL/Auth đã truy xuất
```

## 4. Kiểm tra database

Vào Postgres:

```bash
psql -U minhmh -d robo_reception -h localhost
```

Kiểm tra raw tables:

```sql
\dt robo_raw.*
```

Kiểm tra app views:

```sql
\dv robo_app.*
```

Query mẫu:

```sql
SELECT count(*) FROM robo_app.services;
SELECT count(*) FROM robo_app.doctors;
SELECT count(*) FROM robo_app.doctor_schedules;
```

Thoát:

```sql
\q
```

## 5. Nếu cần chạy lại app views

```bash
cd /home/minhmh/tool/robo
scripts/apply_app_views.sh
```

Nếu cần tạo/cập nhật account schema demo:

```bash
cd /home/minhmh/tool/robo
scripts/apply_auth_schema.sh
```

## 6. Nếu port đang bị chiếm

Kiểm tra backend:

```bash
pgrep -af 'uvicorn app.main:app'
```

Dừng backend:

```bash
kill <PID>
```

Kiểm tra frontend:

```bash
pgrep -af 'http.server 5173'
```

Dừng frontend:

```bash
kill <PID>
```

## 7. Thứ tự chạy mỗi lần làm việc

1. Đảm bảo Postgres đang chạy:

```bash
pg_isready
```

2. Chạy backend ở terminal 1.
3. Chạy frontend ở terminal 2.
4. Mở `http://localhost:5173`.

Nếu vừa sửa dữ liệu trong app views hoặc thêm nguồn vào `scripts/rag_documents.py`, rebuild Qdrant trước khi test câu hỏi RAG:

```bash
cd /home/minhmh/tool/robo
backend/.venv/bin/python scripts/build_qdrant_index.py
```

RAG đang loại các topic không phù hợp để trả lời bệnh nhân:

```text
RAG_EXCLUDED_TOPICS=overview,roles
```

Nếu thấy LLM kéo nhầm nội dung platform/system overview như `SmartClinic`, kiểm tra topic của article và thêm vào `RAG_EXCLUDED_TOPICS`, sau đó rebuild index.

### Test kịch bản MVP chatbot

Chạy bộ kịch bản MVP qua endpoint `/ask` bằng FastAPI TestClient:

```bash
cd /home/minhmh/tool/robo
./backend/.venv/bin/python scripts/test_mvp_chatbot.py --llm-provider none
```

Mặc định script tắt vector RAG để chạy ổn định bằng keyword fallback. Nếu muốn test Qdrant/Ollama vector thật:

```bash
./backend/.venv/bin/python scripts/test_mvp_chatbot.py --llm-provider ollama --rag-vector --verbose
```

## 8. Ghi chú kiến trúc

Backend hiện đã scaffold theo hướng:

```text
API /ask
  -> AI Agent Orchestrator
  -> LLM client hoặc rule fallback
  -> Decision Router
  -> Tool Registry
  -> Domain Adapter
  -> SQL/RAG/Auth tools
  -> Response Generator
```

Hiện tại:

- Domain đang chạy: `clinic`
- LLM provider OpenAI-compatible/Ollama: đã có code, local đang dùng `qwen2.5:3b`
- RAG vector: Qdrant local mode, dữ liệu trong `qdrant_data/`, collection `clinic_knowledge`
- Grounded answer: đã bật cho `knowledge_search`, context đưa vào LLM đã được rút gọn chỉ còn title/nội dung chính; fallback template vẫn format markdown thành câu trả lời dễ đọc nếu LLM lỗi/tắt.
- Local LLM formatter: đã bật có chọn lọc cho SQL/Auth answers khi `LLM_PROVIDER=ollama`; không chạy với provider cloud. Các intent list tốt bằng template như nhóm dịch vụ hoặc service_price nhiều dòng sẽ ưu tiên template để tránh timeout và tránh LLM chọn thiếu dữ liệu.
- Service catalog flow: `service_catalog_summary` trả tổng quan nhóm dịch vụ, `service_category_detail` trả danh sách dịch vụ trong một nhóm cụ thể như CT Scan/MRI/Laboratories.
- Auth password/token MVP: `/auth/login` phát access token + refresh token từ email/password trong `robo_auth.accounts`; login tạo `robo_auth.sessions`; `/ask` ưu tiên `Authorization: Bearer <token>` và kiểm tra session còn active.
- Auth refresh: `/auth/refresh` rotate refresh token và phát access token mới.
- Auth change password: `/auth/change-password` yêu cầu bearer token, current password và new password; đổi xong revoke các session khác.
- Auth password reset foundation: `/auth/password-reset/request` tạo token reset có TTL trong `robo_auth.password_reset_tokens`; `/auth/password-reset/complete` đổi password bằng reset token, clear lock/counter và revoke toàn bộ session. Mặc định API không trả token; bật `AUTH_PASSWORD_RESET_EXPOSE_TOKEN=true` chỉ khi test local/dev.
- Auth logout server-side: `/auth/logout` revoke session hiện tại bằng `sessions.revoked_at`.
- Audit DB nền tảng: login/logout, policy decision và tool result được ghi vào `robo_auth.audit_events`.
- Request observability: backend nhận/tạo `X-Request-ID`, trả `X-Request-ID`, `X-Process-Time-Ms`; `/ask` response và audit DB đều có `request_id`, `latency_ms`.
- Auth mock trong request là dev-only path và mặc định tắt.
- Auth chưa gắn email/SMS/OTP delivery thật; access token hiện ký bằng HMAC local qua `AUTH_TOKEN_SECRET`, refresh token lưu hash trong `robo_auth.sessions`, reset token lưu hash trong `robo_auth.password_reset_tokens`.

Cấu hình auth legacy/debug:

```text
AUTH_ALLOW_REQUEST_CONTEXT=false
AUTH_ALLOW_LEGACY_ROLE_LOGIN=false
AUTH_REFRESH_TOKEN_TTL_SECONDS=2592000
AUTH_MAX_FAILED_LOGIN_ATTEMPTS=5
AUTH_LOCK_SECONDS=900
AUTH_MIN_PASSWORD_LENGTH=8
AUTH_LOGIN_RATE_LIMIT_ATTEMPTS=10
AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
AUTH_PASSWORD_RESET_TOKEN_TTL_SECONDS=900
AUTH_PASSWORD_RESET_EXPOSE_TOKEN=false
```

Chỉ bật hai biến này khi cần debug đường cũ `payload.auth` hoặc login bằng `role + UUID`.

Nếu user nhập sai mật khẩu quá `AUTH_MAX_FAILED_LOGIN_ATTEMPTS`, account sẽ bị khóa tạm thời trong `AUTH_LOCK_SECONDS` giây.
Nếu login quá nhiều lần trong một cửa sổ ngắn, backend trả HTTP 429 trước khi chạm DB login.

Ví dụ request reset password local/dev:

```bash
curl -X POST http://localhost:8000/auth/password-reset/request \
  -H 'Content-Type: application/json' \
  -d '{"email":"patient.demo@robo.local"}'
```

Nếu cần thấy token trên UI/API để test thủ công, đặt `AUTH_PASSWORD_RESET_EXPOSE_TOKEN=true` rồi restart backend. Không bật biến này cho môi trường thật.

Bước tiếp theo:

1. Thêm OTP/reset password qua email/SMS nếu cần nâng tiếp phần auth.
2. Mở rộng dữ liệu riêng tư ngoài lịch hẹn, ví dụ kết quả, hồ sơ tóm tắt.
3. Mở rộng grounded answer sang intent khác nếu cần.

## 9. Chạy test backend

```bash
cd /home/minhmh/tool/robo/backend
source .venv/bin/activate
pytest
```

## 10. Theo dõi tiến độ

Đọc và cập nhật:

```text
docs/PROGRESS.md
docs/DOCS_INDEX.md
```

Tiến độ hiện tại được ghi trong:

```text
docs/PROGRESS.md
```

Sau mỗi lần hoàn thành một phần, cập nhật file này để lần sau dễ tiếp tục.

Mục lục tài liệu nằm ở:

```text
docs/DOCS_INDEX.md
```

## 11. Đọc hiểu backend flow

Tài liệu giải thích chi tiết flow backend và cây thư mục project:

```text
docs/BACKEND_FLOW.md
```

## 12. Xác thực và phân quyền

Kế hoạch auth/RBAC nằm ở:

```text
docs/AUTHORIZATION_PLAN.md
```
