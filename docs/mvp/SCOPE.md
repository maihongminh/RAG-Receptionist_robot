# MVP scope

MVP tập trung chứng minh robot lễ tân có thể:

```text
user hỏi
  -> LLM/rule phân tích intent
  -> route SQL/RAG/Auth
  -> PolicyGuard kiểm tra quyền
  -> truy xuất dữ liệu
  -> template/local LLM formatter trả lời
  -> frontend hiển thị answer + trace
```

## Phạm vi domain

MVP chỉ làm domain:

```text
clinic
```

Chưa làm:

- hotel;
- restaurant;
- school.

## Nhóm câu hỏi public

Đã hỗ trợ:

- địa chỉ phòng khám;
- số điện thoại;
- email;
- giờ làm việc;
- danh sách dịch vụ;
- nhóm xét nghiệm/dịch vụ;
- giá dịch vụ cụ thể;
- lịch bác sĩ công khai;
- quy trình check-in/nhận kết quả qua RAG.

## Nhóm câu hỏi private

Đã hỗ trợ sau login:

- patient xem lịch hẹn/kết quả của chính mình;
- doctor xem lịch hẹn theo bác sĩ;
- receptionist xem dữ liệu trong clinic;
- clinic_admin xem dữ liệu trong clinic.

Guest hỏi dữ liệu cá nhân phải bị chặn.

## RAG MVP

Nguồn RAG hiện tại:

```text
robo_app.knowledge_articles
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Qdrant local qdrant_data
```

RAG dùng cho nội dung text/procedure, không dùng cho dữ liệu cần chính xác theo dòng như giá, lịch hẹn, kết quả cá nhân.

## Auth MVP

Frontend login bằng email/password.

Backend:

- kiểm tra account schema hiện hành;
- verify password hash PBKDF2-SHA256;
- tạo `robo_auth.sessions`;
- sinh bearer token HMAC;
- `/ask` đọc `Authorization: Bearer <token>` và kiểm tra session còn active;
- `/auth/logout` revoke session hiện tại;
- `PolicyGuard` lọc dữ liệu theo auth context.

`payload.auth` mock chỉ còn là dev-only path và mặc định bị bỏ qua.

Login legacy bằng `role + UUID` cũng mặc định tắt. Muốn bật lại các đường debug này:

```text
AUTH_ALLOW_REQUEST_CONTEXT=true
AUTH_ALLOW_LEGACY_ROLE_LOGIN=true
```

## Data MVP

Dữ liệu nguồn:

```text
data/postgres_csv
  -> robo_raw
  -> robo_app
```

Backend chỉ nên query `robo_app`.

Các bảng/app views chính MVP dùng:

- `robo_app.clinics`
- `robo_app.clinic_settings`
- `robo_app.rooms`
- `robo_app.staff`
- `robo_app.doctors`
- `robo_app.doctor_schedules`
- `robo_app.service_categories`
- `robo_app.services`
- `robo_app.patients`
- `robo_app.appointments`
- `robo_app.paraclinical_results`
- `robo_app.knowledge_articles`
- `robo_app.patient_question_templates`
- auth account schema hiện hành

## Tiêu chí MVP đã đạt

- Frontend login riêng, không phá layout chat.
- Guest/public/private flow rõ.
- RAG/SQL phân biệt đúng nguồn.
- Có trace để kiểm chứng source.
- Backend tests pass.
- Scenario MVP pass.
- Branch `mvp-v1` đã lưu snapshot.
