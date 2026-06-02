# Productization roadmap

Roadmap này bắt đầu sau khi MVP đã được lưu ở branch `mvp-v1`.

## Phase P0 - Baseline freeze

Mục tiêu: khóa lại mốc MVP và chuẩn bị đường phát triển mới.

Đã làm:

- Tạo branch `mvp-v1`.
- Push `mvp-v1` lên GitHub.
- Giữ `main` để phát triển tiếp.

Việc đã xong trước khi code production:

- Hoàn thiện bộ docs productization.
- Ghi rõ milestone, rủi ro, thứ tự triển khai.
- Không còn hiểu nhầm giữa MVP và production trong docs.

Done khi:

- `docs/productization/*.md` tồn tại và được link từ `DOCS_INDEX.md`.
- `PROGRESS.md` ghi project đã chuyển sang productization implementation.

## Phase P1 - Auth/account production foundation

Mục tiêu: thay lớp account demo bằng nền account/session có thể vận hành.

Deliverables:

- Schema account chính thức, không đặt trong app view tạm nếu sau này cần migration bền vững.
- Password hash chuẩn, có policy độ dài/tối thiểu.
- Access token + session DB.
- Refresh token rotate server-side.
- Logout server-side hoặc session revoke.
- `GET /auth/me` trả auth context đáng tin cậy.
- Account liên kết rõ với patient/staff/clinic/profile.
- Test auth service và API auth.

Không làm trong P1:

- OTP phức tạp nếu chưa cần.
- Social login.
- Admin UI quản lý account đầy đủ.

Done khi:

- Frontend login bằng email/password.
- Token hết hạn xử lý rõ.
- Logout vô hiệu hóa session nếu dùng session table.
- Private `/ask` chỉ dựa vào token/session, không dựa vào auth mock của frontend.

Trạng thái hiện tại:

- Đã có `robo_auth.accounts/account_roles/account_identities/sessions`.
- Đã có `/auth/login`, `/auth/me`, `/auth/logout`.
- Đã có `/auth/refresh` rotate refresh token.
- Đã có `/auth/change-password`.
- Đã có `/auth/password-reset/request` và `/auth/password-reset/complete` với token reset có TTL.
- Đã có Account admin API/UI cơ bản cho `clinic_admin`/`system_admin`: list/detail account, unlock account, revoke sessions.
- Đã khóa `payload.auth` mặc định và tắt login legacy `role + UUID`.
- Đã có `failed_login_count` và khóa tạm thời bằng `locked_until`.
- Đã có rate limit login in-memory theo IP/email.
- Chưa có email/SMS/OTP delivery thật và màn tạo/sửa role/identity nâng cao.

## Phase P2 - Data/application layer hardening

Mục tiêu: làm rõ `robo_raw` là import layer, `robo_app` là contract cho backend.

Deliverables:

- Danh sách bảng production cần dùng trước.
- View/table contract cho từng tool.
- Index cho các lookup hay dùng.
- Migration/idempotent seed script.
- Quy tắc không query trực tiếp `robo_raw` từ domain tool.

Done khi:

- SQL tools chỉ dùng `robo_app`.
- Có tài liệu mapping source table -> app view/table -> tool.
- Có test tích hợp cho các tool quan trọng.

Trạng thái hiện tại:

- Đã thêm `db/app/contract.json` cho 13 view `robo_app` đang phục vụ MVP.
- Đã thêm `scripts/check_app_contract.py` để kiểm tra live DB theo contract.
- Đã thêm test guardrail để domain SQL tools không query trực tiếp `robo_raw`.
- Đã thêm `db/app/tool_map.json` cho 12 mapped tools, gồm tool private mới `clinic.lookup_patient_profile`.
- Đã mở rộng contract `robo_app.patients` cho patient profile summary.
- Chưa có mapping chi tiết cho toàn bộ 56 bảng raw; sẽ mở theo use case.

## Phase P3 - Private data expansion + audit

Mục tiêu: mở rộng dữ liệu riêng tư nhưng vẫn kiểm soát quyền.

Deliverables:

- Audit log DB cho private tool access.
- Policy matrix chi tiết cho:
  - appointment;
  - lab/paraclinical result;
  - patient profile summary;
  - visit/medical summary nếu mở.
- Response redaction cho dữ liệu nhạy cảm.
- Trace/debug tách dev/prod.

Done khi:

- Mọi private lookup ghi audit log.
- Guest luôn bị chặn private data.
- Patient chỉ thấy dữ liệu của mình.
- Doctor chỉ thấy dữ liệu được phân công.
- Receptionist/clinic_admin bị giới hạn theo clinic.

Trạng thái hiện tại:

- Đã có audit DB nền tảng cho `policy_decision` và `tool_result`.
- Đã có private tool `clinic.lookup_patient_profile`:
  - patient scope theo `patient_id`;
  - receptionist/clinic_admin scope theo `clinic_id`;
  - system_admin có quyền toàn cục theo permission wildcard;
  - doctor chưa mở quyền cho hồ sơ tổng quát khi chưa có rule phân công bệnh nhân rõ.
- Cần tiếp tục mở từng use case riêng như visit/medical summary thay vì query rộng toàn bộ patient data.

## Phase P4 - RAG production sync

Mục tiêu: biến RAG từ build thủ công thành quy trình quản lý index rõ ràng.

Deliverables:

- `rag_documents.py` thành registry có metadata chuẩn.
- Qdrant payload có `source`, `source_table`, `source_id`, `clinic_id`, `language`, `updated_at`.
- Script rebuild toàn bộ.
- Script sync incremental theo `updated_at` hoặc manifest hash.
- Chính sách xóa/reindex document stale.

Done khi:

- Có thể build lại Qdrant từ Postgres bằng một lệnh.
- Có thể biết document vector đến từ bảng/dòng nào.
- Query RAG filter được theo domain/clinic/source khi cần.

## Phase P5 - Deployment/test hardening

Mục tiêu: chạy được môi trường nhất quán và kiểm thử end-to-end.

Deliverables:

- Docker compose cho:
  - backend;
  - frontend;
  - Postgres;
  - Qdrant;
  - Ollama optional.
- `.env.example` rõ cho dev/prod.
- Integration tests với Postgres.
- E2E smoke cho login + `/ask`.
- Healthcheck/readiness endpoints.

Done khi:

- Clone repo -> chạy setup -> test MVP/productization smoke được.
- CI hoặc script local có thể chạy test quan trọng.

## Thứ tự khuyến nghị

```text
P1 auth/account
  -> P2 data layer
  -> P3 private data/audit
  -> P4 RAG sync
  -> P5 deployment/test
```

Lý do: auth và data contract là nền. Nếu mở rộng RAG/private tools trước khi có auth/audit tốt, rủi ro bảo mật và refactor sẽ tăng.
