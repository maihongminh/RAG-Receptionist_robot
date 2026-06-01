# Tiến độ project

File này dùng để cập nhật trạng thái sau mỗi lần làm việc.

## Trạng thái hiện tại

Cập nhật gần nhất: 2026-06-01

Project đã hoàn thành **MVP hỏi đáp có SQL/RAG/LLM local, auth password/token MVP và context hội thoại ngắn**.

Branch lưu MVP:

```text
mvp-v1
```

Project hiện chuyển sang **phase productization planning** trên `main`.

Luồng hiện tại:

```text
Postgres
  -> robo_raw
  -> robo_app
  -> backend /ask
  -> SQL/RAG/Auth tools
  -> response formatter / local LLM formatter
  -> frontend chatbot
```

## Đã hoàn thành

- Tạo roadmap tổng thể cho robot lễ tân.
- Import toàn bộ Excel vào Postgres.
- Tạo database `robo_reception`.
- Tạo schema `robo_raw` chứa đủ 56 bảng từ Excel.
- Tạo schema view `robo_app` cho dữ liệu sạch.
- Tạo tài liệu DB trong `db/README.md`.
- Tạo tài liệu hệ thống trong `docs/doc_system.md`.
- Tạo tài liệu backend flow trong `docs/BACKEND_FLOW.md`.
- Tạo kế hoạch xác thực/phân quyền trong `docs/AUTHORIZATION_PLAN.md`.
- Tạo mục lục tài liệu trong `docs/DOCS_INDEX.md`.
- Tạo hướng dẫn chạy chung trong `docs/RUNBOOK.md`.
- Scaffold backend FastAPI.
- Thiết kế backend theo hướng scale:
  - `core/orchestrator.py`
  - `core/decision_router.py`
  - `core/tool_registry.py`
  - `core/response_generator.py`
  - `llm/llm_client.py`
  - `rag/grounded_response_generator.py`
  - `auth/policy_guard.py`
  - `domains/clinic/adapter.py`
  - `domains/clinic/sql_tools.py`
- Tạo API `POST /ask`.
- Tạo frontend chatbot web tách riêng khỏi backend.
- Backend chạy tại `http://localhost:8000`.
- Frontend chạy tại `http://localhost:5173`.
- Thêm intent chào hỏi/giới thiệu bot.
- Thêm nhánh yêu cầu xác thực cho dữ liệu cá nhân.
- Thêm skeleton auth/RBAC vào backend:
  - `auth/auth_context.py`
  - `auth/permissions.py`
  - `auth/policy_guard.py`
  - `auth/audit_logger.py`
- Gắn `PolicyGuard` vào flow trước khi gọi tool.
- Thêm test tự động bước đầu cho:
  - rule intent parser
  - policy guard
  - orchestrator
- Đã chạy `pytest`: 20 test pass.
- Thêm RAG basic dạng keyword/fuzzy search trên `robo_app.knowledge_articles`.
- Thêm intent `appointment_booking` để xử lý câu như `đặt lịch`, `book lịch`, `đăng ký khám`.
- Thêm LLM provider OpenAI-compatible cho bước parse intent/entities.
- Thêm LLM provider Ollama local cho qwen/llama.
- Đã gỡ cấu hình/xử lý Gemini tạm thời để tập trung dùng Ollama qwen/llama local.
- LLM mặc định tắt bằng `LLM_PROVIDER=none`; nếu bật mà lỗi hoặc thiếu key thì fallback về rule parser.
- Thêm `parser_source` vào API/UI trace để biết câu hỏi được parse bằng LLM hay rule fallback.
- Thêm test cho LLM client.
- Đã chạy `pytest`: 24 test pass.
- Đã cài/chạy Ollama local trên WSL với model `qwen2.5:3b`.
- Đã xác nhận backend `/ask` trả `parser_source: "llm"` khi dùng Ollama.
- Thêm RAG vector bằng Qdrant local mode:
  - `qdrant_data/`
  - collection `clinic_knowledge`
  - embedding model `nomic-embed-text`
  - script `scripts/build_qdrant_index.py`
- `knowledge_search` hiện query Qdrant trước và fallback keyword/fuzzy search nếu Qdrant lỗi hoặc chưa có index.
- Thêm grounded LLM response generator cho `knowledge_search`.
- Thêm Ollama local formatter cho kết quả SQL/Auth, gồm lịch hẹn cá nhân sau khi đã qua `PolicyGuard`.
- Gom tài liệu cấp project vào `docs/` để root thư mục gọn hơn.
- Thêm short conversation context in-memory theo `session_id`:
  - frontend tạo/gửi `session_id`;
  - backend nhớ context ngắn cho follow-up;
  - hỗ trợ `xem tiếp`, `24 nhóm khác là nhóm nào`, `xem chi tiết nhóm 35`.
- Tách `context_max_rows`, `api_preview_max_rows`, `sql_result_limit` trong RAG config để kiểm soát số dòng trả lời/trace/query.
- Cải thiện service catalog:
  - `service_catalog_summary`;
  - `service_category_list`;
  - `service_category_detail`;
  - paging/follow-up theo nhóm dịch vụ.
- Cải thiện routing/normalization để LLM local không kéo sai intent public info sang service list.
- Cải thiện medical advice:
  - nhận diện câu triệu chứng linh hoạt;
  - bám cụm triệu chứng user nói;
  - không chẩn đoán hoặc khuyến nghị dịch vụ thay bác sĩ;
  - có cảnh báo dấu hiệu cần đi cơ sở y tế/cấp cứu.
- Test backend hiện tại: `112 passed`.
- MVP scenario hiện tại: `17/17 passed`.
- Manual role test đã ổn cho `guest`, `patient`, `doctor`, `receptionist`, `clinic_admin`.
- Thêm auth password/token MVP:
  - `POST /auth/login`;
  - `GET /auth/me`;
  - `/ask` đọc `Authorization: Bearer <token>`;
  - `robo_app.auth_accounts` lưu account demo bằng password hash PBKDF2-SHA256;
  - frontend có màn hình đăng nhập email/password riêng, đăng xuất và lưu token localStorage.
- Tạo branch `mvp-v1` để lưu snapshot MVP.
- Push `mvp-v1` lên GitHub.
- Tạo `docs/mvp/` để lưu phạm vi, account test và test plan của MVP:
  - `docs/mvp/README.md`;
  - `docs/mvp/SCOPE.md`;
  - `docs/mvp/TEST_ACCOUNTS.md`;
  - `docs/mvp/TEST_PLAN.md`.
- Bắt đầu phase productization bằng bộ tài liệu:
  - `docs/productization/PLAN.md`;
  - `docs/productization/ROADMAP.md`;
  - `docs/productization/AUTH_PLAN.md`;
  - `docs/productization/DATA_PLAN.md`;
  - `docs/productization/RAG_PLAN.md`;
  - `docs/productization/AUDIT_DEPLOYMENT_TEST_PLAN.md`.

### 2026-05-26

- Push repo lần đầu lên GitHub: `maihongminh/RAG-Receptionist_robot`.
- Gom tài liệu root vào `docs/`.
- Thêm conversation context MVP bằng `backend/app/core/conversation_context.py`.
- Frontend gửi `session_id` trong request `/ask`.
- Backend trả `session_id` trong response `/ask`.
- Sửa các lỗi follow-up service category:
  - `24 nhóm khác là nhóm nào`;
  - `xem tiếp`;
  - `xem chi tiết nhóm 24/35`;
  - match exact category như `check for insects in the blood`.
- Sửa false-positive service type, không để `ct` trong `insects` bị hiểu là CT/imaging.
- Sửa public info: `Phòng khám mở cửa lúc mấy giờ` không bị route nhầm sang danh sách dịch vụ.
- Sửa medical advice để câu như `tôi đau ngực, nên khám gì`, `tôi đau đầu đau mắt thì sao` trả lời linh hoạt hơn.
- Sửa catalog follow-up để `các nhóm còn lại` và `xem thêm` sau `các dịch vụ hiện có` trả tiếp đúng nhóm 11-20 theo thứ tự tổng quan.
- Manual test role: guest, patient, doctor, receptionist, clinic_admin đều ổn ở phạm vi MVP.
- Chạy test backend: `107 passed`.
- Chạy scenario MVP: `17/17 passed`.

Task tiếp theo đề xuất:

```text
Hoàn thiện OTP/refresh token hoặc account production dựa trên auth password/token MVP.
```
- Thêm config RAG riêng trong `backend/app/rag/rag_config.py`.
- Thêm `RAG_EXCLUDED_TOPICS=overview,roles` để loại tài liệu platform/permission khỏi RAG retrieval.
- Thêm auth MVP ban đầu bằng `auth` mock trong request:
  - guest bị chặn khi hỏi dữ liệu cá nhân
  - patient tra lịch hẹn theo `patient_id`
  - doctor tra lịch hẹn theo `doctor_id`
  - receptionist/clinic_admin tra lịch hẹn theo `clinic_id`
- Sau đó đã nâng lên màn đăng nhập email/password ở frontend.
- Đã chạy `pytest`: 36 test pass.
- Tách module backend để giảm tải `core`:
  - `backend/app/auth`: auth context, permissions, policy guard, audit logger
  - `backend/app/llm`: LLM client
  - `backend/app/rag`: embedding, Qdrant, RAG config, grounded response generator
- Đã chạy `pytest`: 43 test pass.

## Chức năng đang hỗ trợ

Bot hiện xử lý được các nhóm câu hỏi cơ bản:

- Chào hỏi/giới thiệu:
  - `xin chào`
  - `bạn là ai`
  - `bạn làm được gì`
- Thông tin chung:
  - địa chỉ phòng khám
  - số điện thoại
  - email
  - giờ làm việc
- Giá/dịch vụ:
  - hỏi giá dịch vụ
  - tìm dịch vụ theo tên gần đúng
- Lịch bác sĩ:
  - hỏi bác sĩ có khám hôm nay không
  - tra lịch theo tên bác sĩ
- Dữ liệu cá nhân:
  - guest bị yêu cầu xác thực
  - patient/doctor/receptionist/clinic_admin đăng nhập email/password và tra được dữ liệu trong phạm vi được phép

## Chưa hoàn thành

- Chưa có account/session production chính thức.
- Chưa có refresh token/logout server-side.
- Chưa có OTP/reset password.
- Chưa có audit log ghi xuống database, hiện mới log skeleton.
- Chưa có tạo lịch hẹn.
- Chưa có STT/TTS.
- Chưa có memory hội thoại dài hạn.
- Chưa có domain adapter thật cho:
  - khách sạn
  - nhà hàng
  - trường học
- Chưa có admin UI.
- Chưa có integration test với Postgres thật.

## Việc nên làm tiếp theo

Ưu tiên đề xuất:

1. P1 auth/account production foundation theo `docs/productization/AUTH_PLAN.md`.
2. P2 data/application layer hardening theo `docs/productization/DATA_PLAN.md`.
3. P3 private data expansion + audit theo `docs/productization/AUDIT_DEPLOYMENT_TEST_PLAN.md`.
4. P4 RAG production sync theo `docs/productization/RAG_PLAN.md`.
5. P5 deployment/test hardening.

## Cách chạy nhanh

Backend:

```bash
cd /home/minhmh/tool/robo/backend
source .venv/bin/activate
DATABASE_URL="postgresql:///robo_reception" uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd /home/minhmh/tool/robo/frontend
python3 -m http.server 5173
```

Mở:

```text
http://localhost:5173
```

## Ghi chú tiến độ

### 2026-05-18

- Cài Ollama trong WSL thành công.
- Pull và chạy model `qwen2.5:3b` thành công.
- Kiểm tra Ollama API `http://localhost:11434/api/tags` thấy model `qwen2.5:3b`.
- Backend `.env` đang dùng:
  - `LLM_PROVIDER=ollama`
  - `LLM_MODEL=qwen2.5:3b`
  - `LLM_BASE_URL=http://localhost:11434`
- Khởi động backend tại `http://localhost:8000`.
- Test `POST /ask` với câu `đặt lịch khám ngày mai` trả `parser_source: "llm"`.
- Sửa backend để chuẩn hóa `data_source/requires_auth` sau khi LLM parse, tránh local LLM trả đúng intent nhưng không gọi SQL/RAG tool.
- Test lại `Địa chỉ phòng khám ở đâu?` và `CT Brain without contrast giá bao nhiêu?` đều trả dữ liệu từ `robo_app`.
- Sửa UI chatbot để khung chính giữ chiều cao theo viewport; vùng hội thoại và `dataPreview` tự cuộn khi nội dung dài.
- Cập nhật tài liệu kiến trúc để tách rõ 2 vai trò LLM:
  - LLM đầu flow: parse intent/entities.
  - LLM cuối flow sau SQL/RAG retrieval: diễn đạt câu trả lời có căn cứ từ context.
- Cài dependency `qdrant-client`.
- Pull model embedding `nomic-embed-text` bằng Ollama.
- Thêm Qdrant local vector store tại `qdrant_data/`, đã thêm vào `.gitignore`.
- Thêm script `scripts/build_qdrant_index.py` để vector hóa source registry trong `scripts/rag_documents.py`.
- Build index thành công sau khi lọc: `4 chunks` từ `4 rows` vào collection `clinic_knowledge`.
- Sửa backend `knowledge_search` để ưu tiên Qdrant vector search, fallback keyword/fuzzy search.
- Test `Quy trình check-in bệnh nhân như thế nào?` trả source `qdrant:clinic_knowledge`.
- Cập nhật tài liệu flow RAG:
  - hiện tại build vector từ `scripts/rag_documents.py`.
  - `scripts/rag_documents.py` hiện gom `robo_app.knowledge_articles`; sau này thêm nguồn text hợp lệ vào file này.
- Đồng bộ tài liệu với source hiện tại:
  - bổ sung `embedding_client.py`, `qdrant_store.py`, `build_qdrant_index.py`, `qdrant_data/`.
  - bổ sung `test_clinic_sql_tools.py`.
  - cập nhật `docs/BACKEND_FLOW.md`, `backend/README.md`, `docs/doc_system.md`, `docs/RUNBOOK.md`, `docs/DOCS_INDEX.md`.
- Thêm `backend/app/rag/rag_config.py` để gom cấu hình RAG:
  - `RAG_TOP_K`
  - `RAG_MIN_SCORE`
  - `RAG_KEYWORD_SOURCE_LIMIT`
  - `RAG_KEYWORD_TOP_K`
  - `RAG_KEYWORD_MIN_SCORE`
  - `RAG_EMPTY_CONFIDENCE`
- Qdrant vector search hiện dùng `RAG_TOP_K` và `RAG_MIN_SCORE`; keyword fallback dùng limit/top-k/min-score riêng.
- Đổi default vector retrieval thành `RAG_TOP_K=5`, `RAG_MIN_SCORE=0.75` trong `rag_config.py`, `.env.example`, `backend/.env.example`, và `backend/.env`.
- Thêm grounded answer cho `knowledge_search`:
  - `rag/grounded_response_generator.py`
  - `LLMClient.generate_grounded_answer(...)`
  - API response có thêm `answer_source`.
  - UI Trace hiển thị `Answer: LLM grounded` hoặc `Template`.
  - Nếu LLM tắt/lỗi/rỗng thì fallback template.
- Chạy test backend: `31 passed`.
- Khởi động frontend tại `http://localhost:5173`.
- Task tiếp theo: thêm grounded LLM response generator sau SQL/RAG retrieval.

### 2026-05-15

- Chuẩn bị bắt đầu task LLM provider thật.
- Quy ước: trước khi làm task lớn mới, cập nhật `PROGRESS.md` và tài liệu liên quan.
- Thêm `DOCS_INDEX.md` để giải thích chức năng từng file tài liệu.
- Task tiếp theo: implement LLM client để parse intent/entities, rule parser vẫn giữ làm fallback.
- Hoàn thành LLM provider OpenAI-compatible trong `backend/app/llm/llm_client.py`.
- Hoàn thành LLM provider Ollama local trong `backend/app/llm/llm_client.py`.
- Gỡ nhánh Gemini tạm thời theo quyết định chuyển sang qwen/llama local.
- Cấu hình hiện tại quay về `LLM_PROVIDER=ollama`, `LLM_MODEL=qwen2.5:3b`.
- Thêm trace `parser_source` để kiểm tra LLM có chạy thật trên UI/API.
- Thêm prompt intent parser cho domain clinic trong `backend/app/domains/clinic/prompts.py`.
- Cập nhật `.env.example`, `RUNBOOK.md`, `BACKEND_FLOW.md`, `backend/README.md`, `doc_system.md`, `DOCS_INDEX.md`.
- Chạy test backend: `25 passed`.
- Task tiếp theo: nâng RAG basic lên vector embedding store.

### 2026-05-14

- Hoàn thành DB raw/app views.
- Hoàn thành backend API MVP.
- Hoàn thành frontend chatbot MVP.
- Bot hiện chỉ là hỏi đáp cơ bản bằng rule-based router, chưa có LLM/RAG thật.
- Viết tài liệu `BACKEND_FLOW.md` giải thích flow backend và cây thư mục project.
- Thêm skeleton auth/RBAC vào source để không phải bẻ lại flow sau này.
- Thêm test backend bước đầu, `20 passed`.
- Thêm RAG basic cho câu hỏi quy trình/hướng dẫn/FAQ.
- Thêm intent `appointment_booking`, câu `đặt lịch` không còn rơi vào knowledge overview.

### Ghi chú mới

Thêm ghi chú mới bên dưới dòng này.
