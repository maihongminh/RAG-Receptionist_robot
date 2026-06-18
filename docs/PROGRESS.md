# Tiến độ project

File này dùng để cập nhật trạng thái sau mỗi lần làm việc.

## Trạng thái hiện tại

Cập nhật gần nhất: 2026-06-17

Project đã hoàn thành **MVP hỏi đáp có SQL/RAG/LLM local, auth productization foundation và context hội thoại ngắn**.

Branch lưu MVP:

```text
mvp-v1
```

Project hiện đang ở **phase productization implementation** trên `main`.

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
- Mở rộng private SQL/auth use case đầu tiên sau productization foundation:
  - thêm intent `patient_profile_summary`;
  - thêm tool `clinic.lookup_patient_profile`;
  - patient xem hồ sơ của chính mình theo `patient_id`;
  - receptionist/clinic_admin xem trong phạm vi `clinic_id` và có thể lọc theo tên/mã/SĐT/email;
  - doctor chưa được mở quyền xem hồ sơ bệnh nhân tổng quát cho tới khi có care-scope rõ.
- Thêm seed productization riêng:
  - `db/app/seed_productization_demo.sql`;
  - `scripts/apply_productization_seed.sh`;
  - MVP seed vẫn giữ ở `db/app/seed_mvp_demo.sql`.
- Mở rộng private timeline:
  - thêm intent `patient_timeline_summary`;
  - thêm tool `clinic.lookup_patient_timeline`;
  - timeline hiện gom `robo_app.appointments` và `robo_app.paraclinical_results`;
  - patient xem timeline của chính mình;
  - receptionist/clinic_admin/system_admin phải nêu bệnh nhân cụ thể trước khi trả timeline;
  - doctor chưa mở quyền timeline tổng hợp cho tới khi có care-scope rõ.
- Mở rộng visit/medical summary:
  - thêm view `robo_app.patient_visit_summaries`;
  - view gom `medical_records`, `visits`, latest `vital_signs`, patient và doctor names;
  - thêm intent `visit_summary_lookup`;
  - thêm tool `clinic.lookup_visit_summary`;
  - patient xem lượt khám của chính mình;
  - doctor/receptionist/clinic_admin/system_admin phải nêu bệnh nhân cụ thể;
  - seed productization thêm 5 visits, 5 medical_records, 5 vital_signs cho patient demo.
- Mở rộng billing/payment summary:
  - thêm view `robo_app.billing_records`;
  - view đọc từ `diagnostic_walk_in_patients`;
  - thêm intent `billing_summary_lookup`;
  - thêm tool `clinic.lookup_billing_summary`;
  - patient xem hóa đơn/thanh toán của chính mình;
  - receptionist/clinic_admin/system_admin phải nêu bệnh nhân cụ thể;
  - doctor không có quyền billing;
  - seed productization thêm 5 billing records cho patient demo.
- Mở rộng partner lab request/onsite collection:
  - thêm view `robo_app.partner_lab_requests`;
  - thêm view `robo_app.partner_onsite_collections`;
  - thêm intent `partner_lab_request_lookup`;
  - thêm tool `clinic.lookup_partner_lab_requests`;
  - patient xem yêu cầu xét nghiệm/lấy mẫu của chính mình;
  - receptionist/clinic_admin/system_admin xem trong phạm vi được phép và phải lọc theo bệnh nhân/yêu cầu;
  - seed productization thêm 5 partner lab requests và 2 onsite collections cho patient demo.
- Mở rộng ICD10 reference lookup:
  - thêm view `robo_app.icd10_codes`;
  - thêm intent `icd10_lookup`;
  - thêm tool public SQL `clinic.lookup_icd10_codes`;
  - dùng để tra mã/tên ICD10 tham khảo;
  - formatter luôn nhắc đây là bảng mã tham khảo, không phải chẩn đoán y khoa.
- Mở rộng security/platform check summary:
  - thêm view `robo_app.security_check_results`;
  - thêm intent `security_check_summary`;
  - thêm tool `clinic.lookup_security_checks`;
  - chỉ `system_admin` được xem;
  - thêm account demo `system.admin@robo.local` với password `demo123`.
- Test backend hiện tại: `220 passed`.
- MVP/productization scenario hiện tại: `26/26 passed` với `--llm-provider none`.
- Manual role test đã ổn cho `guest`, `patient`, `doctor`, `receptionist`, `clinic_admin`.
- Thêm auth password/token MVP:
  - `POST /auth/login`;
  - `GET /auth/me`;
  - `/ask` đọc `Authorization: Bearer <token>`;
  - `robo_auth.accounts/account_roles/account_identities` lưu account demo bằng password hash PBKDF2-SHA256;
  - frontend có màn hình đăng nhập email/password riêng, đăng xuất và lưu token localStorage.
- Productization auth foundation:
  - `payload.auth` request-body mock mặc định bị bỏ qua;
  - login legacy bằng `role + UUID` mặc định tắt;
  - script scenario MVP login qua `/auth/login` rồi test private flow bằng Bearer token.
- Thêm session DB nền tảng:
  - `/auth/login` tạo row trong `robo_auth.sessions`;
  - token có `session_id`;
  - `/auth/me` và `/ask` kiểm tra session còn active;
  - `/auth/refresh` rotate refresh token và phát access token mới;
  - `/auth/logout` revoke session bằng `revoked_at`;
  - frontend tự refresh access token khi gặp 401, logout gọi `/auth/logout`.
- Thêm bảo vệ sai mật khẩu:
  - sai mật khẩu tăng `failed_login_count`;
  - vượt `AUTH_MAX_FAILED_LOGIN_ATTEMPTS` thì set `locked_until`;
  - login đúng reset counter và `last_login_at`.
- Thêm đổi mật khẩu:
  - `POST /auth/change-password`;
  - yêu cầu bearer token + mật khẩu hiện tại;
  - kiểm tra độ dài tối thiểu bằng `AUTH_MIN_PASSWORD_LENGTH`;
  - cập nhật password hash và revoke các session khác;
  - frontend có form đổi mật khẩu trong phần tài khoản sau khi đăng nhập.
- Thêm reset password token foundation:
  - `POST /auth/password-reset/request`;
  - `POST /auth/password-reset/complete`;
  - tạo bảng `robo_auth.password_reset_tokens`;
  - token chỉ lưu dạng SHA-256 hash, có TTL bằng `AUTH_PASSWORD_RESET_TOKEN_TTL_SECONDS`;
  - reset thành công cập nhật password hash, clear lock/counter và revoke toàn bộ session;
  - mặc định API không trả token để tránh lộ thông tin; local/dev có thể bật `AUTH_PASSWORD_RESET_EXPOSE_TOKEN=true` khi cần test thủ công;
  - frontend có form quên mật khẩu/reset token; kênh gửi email/SMS/OTP thật là integration boundary của bước sau.
- Thêm Account admin UI/API cơ bản:
  - `GET /auth/admin/accounts`;
  - `GET /auth/admin/accounts/{account_id}`;
  - `POST /auth/admin/accounts/{account_id}/unlock`;
  - `POST /auth/admin/accounts/{account_id}/revoke-sessions`;
  - frontend có panel `Quản trị tài khoản` cho `clinic_admin`/`system_admin`;
  - `clinic_admin` chỉ thấy account trong cùng clinic scope.
- Thêm rate limit login in-memory:
  - `AUTH_LOGIN_RATE_LIMIT_ATTEMPTS`;
  - `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS`;
  - bị giới hạn trả HTTP 429 và ghi audit `login_failed/rate_limited`.
- Thêm audit DB nền tảng:
  - tạo `robo_auth.audit_events`;
  - ghi `login_success`, `login_failed`, `logout_success`;
  - ghi `policy_decision` và `tool_result`;
  - audit DB lỗi thì fallback application logger, không làm hỏng request chính.
- Thêm request observability nền tảng:
  - middleware nhận/tạo `X-Request-ID`;
  - trả `X-Request-ID` và `X-Process-Time-Ms`;
  - `/ask` response có `request_id`, `latency_ms`;
  - audit DB ghi `request_id`, `latency_ms`.
- Bắt đầu P2 data/application layer hardening:
  - thêm `db/app/raw_table_inventory.json` để inventory đủ 56 bảng `robo_raw`;
  - thêm `docs/productization/RAW_TABLE_INVENTORY.md` để đọc nhanh nhóm bảng, access level, batch mở rộng;
  - thêm `scripts/check_raw_table_inventory.py` để đảm bảo inventory khớp `db/raw/schema.sql`;
  - thêm `db/app/contract.json` làm contract máy đọc được cho 24 view `robo_app`;
  - thêm `scripts/check_app_contract.py` để kiểm tra live DB có đủ view/cột/type theo contract;
  - thêm `backend/tests/test_app_data_contract.py` để bắt domain SQL tools query trực tiếp `robo_raw`;
  - contract check hiện tại pass: `robo_app has 24 contracted views`;
  - thêm `db/app/tool_map.json` để map intent/tool -> app view -> source table -> policy/test;
  - thêm `scripts/check_tool_map.py`, hiện pass `20 mapped tools`;
  - productization smoke hiện chạy cả raw table inventory check.
- Bắt đầu P4 RAG production sync:
  - chuẩn hóa `scripts/rag_documents.py` thành registry có `source_name`, `source_view`, `source_tables`, `domain`, `access_level`, `language`;
  - mỗi RAG document có `content_hash` để chuẩn bị incremental sync sau này;
  - Qdrant payload hiện có metadata production: `source`, `source_table`, `source_view`, `source_tables`, `source_id`, `chunk_index`, `domain`, `clinic_id`, `access_level`, `visibility`, `language`, `updated_at`, `content_hash`;
  - vector search đã filter tối thiểu theo `domain=clinic` và `access_level=public`;
  - thêm `scripts/check_rag_registry.py`;
  - contract/test backend đã kiểm tra registry RAG.
- Mở rộng P4 RAG manifest foundation:
  - thêm schema `db/rag/schema.sql`;
  - thêm script `scripts/apply_rag_schema.sh`;
  - thêm bảng `robo_rag.index_manifest` để track Qdrant point theo `qdrant_collection`, `source`, `source_id`, `chunk_index`, `point_id`, `content_hash`;
  - `scripts/build_qdrant_index.py` hiện ghi manifest sau full rebuild;
  - thêm helper `scripts/rag_index_manifest.py`;
  - đã chạy rebuild Qdrant local thành công: `4 chunks` từ `4 rows`, manifest `4 rows`;
- Thêm incremental RAG sync:
  - `scripts/build_qdrant_index.py --mode full` giữ hành vi recreate toàn bộ collection;
  - `scripts/build_qdrant_index.py --mode incremental` đọc `robo_rag.index_manifest`, bỏ qua document chưa đổi hash, re-index document mới/đổi hash, xóa point stale;
  - nếu thiếu collection hoặc manifest, incremental tự fallback sang full rebuild;
  - đã chạy incremental sync thật thành công: `4 unchanged`, `0 changed/new`, `0 stale`, `0 upserted chunks`.
- Mở rộng RAG source thứ hai:
  - thêm `robo_app.patient_question_templates` vào `scripts/rag_documents.py`;
  - source này lấy từ `robo_raw.patient_question_templates`;
  - `document_type=patient_question_template`, nội dung được đóng khung là mẫu câu hỏi gợi ý bệnh nhân hỏi bác sĩ;
  - registry checker pass tại thời điểm chỉ có hai source RAG;
  - đã chạy incremental sync thật: `4 unchanged`, `11 changed/new docs`, `0 stale`, `11 upserted chunks`;
  - manifest hiện có `4` chunks từ `knowledge_articles` và `11` chunks từ `patient_question_templates`.
  - thêm routing cho câu hỏi dạng `mẫu câu hỏi`, `nên hỏi bác sĩ câu gì` vào `knowledge_search`;
  - formatter fallback hiện trả `patient_question_template` dưới dạng danh sách câu hỏi gợi ý, có lọc topic như `medication`, `test_results`, `lifestyle`;
  - test thực tế `Tôi nên hỏi bác sĩ câu gì về thuốc?` trả 2 câu hỏi liên quan thuốc.
- Mở rộng RAG source thứ ba:
  - thêm view `robo_app.service_rag_guides` từ `robo_app.services`;
  - source lấy từ `robo_raw.service_catalog` và `robo_raw.service_categories`;
  - view này chỉ tạo nội dung giải thích nhóm dịch vụ/ví dụ dịch vụ, không chứa giá;
  - giá, lịch, dữ liệu cá nhân vẫn phải đi qua SQL/Auth tool;
  - registry checker hiện pass `3 source(s)`;
  - incremental sync đã upsert `41` chunks mới;
  - manifest hiện có `56` chunks: `4 knowledge_articles`, `11 patient_question_templates`, `41 service_rag_guides`.
- Bắt đầu P5 deployment/test hardening:
  - thêm endpoint `GET /ready`;
  - `/health` giữ vai trò liveness check đơn giản;
  - `/ready` kiểm tra Postgres, schema tối thiểu `robo_app/robo_auth/robo_rag`, RAG manifest và Qdrant collection;
  - thêm `scripts/check_productization_smoke.sh` để chạy app contract, tool map, RAG registry, MVP scenario và backend pytest;
  - đã chạy `/ready` local thành công với RAG manifest `15` chunks;
  - đã chạy productization smoke thành công: app contract `27 views`, tool map `20 tools`, raw inventory `56 tables`, RAG registry `3 sources`, MVP/productization scenario `26/26`, backend tests `220 passed`.
- Bắt đầu Batch 1 Scheduling expansion:
  - thêm view `robo_app.appointment_requests` từ `robo_raw.appointment_requests`;
  - view chuẩn hóa patient JSON thành `patient_name`, `patient_phone`, `patient_gender`;
  - chuẩn hóa preferred date/time, flexible flag, chief complaint, review/convert/expiry timestamps;
  - cập nhật `db/app/contract.json`, `db/app/tool_map.json`, `db/app/raw_table_inventory.json`;
  - write flow `clinic.create_appointment_request` vẫn đang disabled, nhưng đã có app contract nền để mở ở bước sau.
- Mở rộng contract service/lab/package foundation:
  - thêm view `robo_app.service_lab_indicators` từ `robo_raw.service_lab_indicators`;
  - thêm view `robo_app.service_packages` từ `robo_raw.service_packages`;
  - thêm view `robo_app.service_package_items` từ `robo_raw.service_package_items`;
  - cập nhật `db/app/contract.json` và `db/app/raw_table_inventory.json`;
  - nối public SQL tool `clinic.lookup_lab_indicator_detail` cho câu hỏi chỉ số/analyte xét nghiệm;
  - nối public SQL tool `clinic.lookup_service_package_detail` cho câu hỏi gói khám/gói dịch vụ gồm gì.
- Mở rộng currency/price foundation:
  - thêm view `robo_app.ref_currencies` từ `robo_raw.ref_currencies`;
  - thêm view `robo_app.clinic_currencies` từ `robo_raw.clinic_currencies`, join danh mục tiền để có tên/symbol/decimal places;
  - thêm view `robo_app.clinic_currency_rate_versions` từ `robo_raw.clinic_currency_rate_versions`, có cờ `is_latest`;
  - cập nhật `db/app/contract.json` và `db/app/raw_table_inventory.json`;
  - các view này là nền cho `future.currency_normalization`, chưa đổi formatter/trả lời giá của chatbot.
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
- Bắt đầu P1 auth/account production foundation:
  - tạo schema `robo_auth`;
  - thêm `robo_auth.accounts`, `account_identities`, `account_roles`, `sessions`;
  - tách seed account demo sang `db/auth/seed_demo.sql`;
  - thêm script `scripts/apply_auth_schema.sh`;
  - backend `/auth/login` đọc account từ `robo_auth` thay vì `robo_app`.

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

Task tiếp theo đề xuất lúc đó:

```text
Hoàn thiện email/SMS/OTP delivery thật hoặc account admin nâng cao dựa trên auth productization foundation.
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

- Account/session production foundation đã có; account admin UI/API cơ bản đã có, chưa có tạo/sửa role/identity nâng cao.
- Đã có refresh token rotate server-side.
- Chưa có email/SMS/OTP delivery thật.
- Audit DB nền tảng đã có, nhưng chưa đầy đủ token invalid/expired, parser/tool sub-latency và retention policy.
- Chưa có tạo lịch hẹn.
- Chưa có STT/TTS.
- Chưa có memory hội thoại dài hạn.
- Chưa có domain adapter thật cho:
  - khách sạn
  - nhà hàng
  - trường học
- Chưa có admin UI cho tạo/sửa role/identity nâng cao.
- Chưa có integration test với Postgres thật.

## Việc nên làm tiếp theo

Ưu tiên đề xuất:

1. P1 auth/account production foundation theo `docs/productization/AUTH_PLAN.md`.
2. P2 data/application layer hardening theo `docs/productization/DATA_PLAN.md`.
3. P3 private data expansion + audit hardening theo `docs/productization/AUDIT_DEPLOYMENT_TEST_PLAN.md`.
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
- Build index ban đầu thành công sau khi lọc: `4 chunks` từ `4 rows` vào collection `clinic_knowledge`.
- Sửa backend `knowledge_search` để ưu tiên Qdrant vector search, fallback keyword/fuzzy search.
- Test `Quy trình check-in bệnh nhân như thế nào?` trả source `qdrant:clinic_knowledge`.
- Cập nhật tài liệu flow RAG:
  - hiện tại build vector từ `scripts/rag_documents.py`.
  - `scripts/rag_documents.py` hiện gom `robo_app.knowledge_articles` và `robo_app.patient_question_templates`; sau này thêm nguồn text hợp lệ vào file này.
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
