# Productization data plan

Mục tiêu của data phase là chuyển từ dữ liệu MVP đủ chạy sang data contract đủ tin cậy để mở rộng.

## 1. Tầng dữ liệu

Giữ ba tầng:

```text
data/postgres_csv
  -> robo_raw
  -> robo_app
  -> backend tools
```

Ý nghĩa:

- `data/postgres_csv`: export gốc.
- `robo_raw`: mirror gần nguyên trạng dữ liệu nhập.
- `robo_app`: contract sạch cho app/backend.
- backend tools: chỉ query `robo_app`, không query `robo_raw` trực tiếp.

## 2. Vấn đề hiện tại

- `robo_raw` có nhiều bảng dạng text từ import.
- `robo_app` hiện chủ yếu là view phục vụ MVP.
- Auth account đã bắt đầu tách ra schema riêng `robo_auth`.
- Một số dữ liệu chưa đồng nhất:
  - doctor name/null;
  - currency/price;
  - patient/staff/profile/user_id mapping;
  - active clinic nhiều cơ sở.

## 3. Nguyên tắc mở rộng 56 bảng

Không đưa 56 bảng vào backend tool hoặc RAG cùng lúc.

Mỗi bảng được mở khi có use case rõ:

```text
use case
  -> bảng nguồn
  -> app view/table contract
  -> SQL tool hoặc RAG document
  -> policy
  -> test
  -> docs
```

## 4. Nhóm bảng ưu tiên

### Public/operational

- `clinics`
- `clinic_general_settings`
- `rooms`
- `staff`
- `doctor_schedules`
- `service_catalog`
- `service_categories`

Dùng cho:

- địa chỉ/giờ làm việc;
- dịch vụ/giá;
- lịch bác sĩ;
- phòng/khu vực.

### Private/patient

- `patients`
- `appointments`
- `visits`
- `paraclinical_orders`
- `medical_records`
- `vital_signs`

Dùng cho:

- lịch hẹn cá nhân;
- kết quả xét nghiệm/cận lâm sàng;
- visit summary;
- patient summary.

Mở từng phần vì cần policy/audit.

### Account/role/platform

- `profiles`
- `user_roles`
- `clinic_memberships`
- `platform_admins`
- `organization_memberships`

Dùng cho:

- account mapping;
- role mapping;
- clinic/org scope.

## 5. App contract đề xuất

Mỗi app view/table nên có:

- id stable;
- clinic_id nếu dữ liệu theo clinic;
- status/is_active nếu có;
- các field đã cast đúng type;
- tên field nhất quán;
- không để empty string thay null;
- không expose field nhạy cảm nếu không cần.

Ví dụ:

```text
robo_app.appointments
  id
  clinic_id
  patient_id
  patient_name
  doctor_id
  doctor_name
  appointment_date
  start_time
  end_time
  visit_type
  status
  service_name
```

## 6. Migration/seed policy

Hiện tại:

- `db/raw/schema.sql`: tạo raw schema.
- `db/raw/load.sql`: load CSV.
- `db/app/views.sql`: tạo app schema/views.
- `db/app/seed_mvp_demo.sql`: patch demo data.

Productization cần:

- idempotent scripts;
- tách seed demo khỏi migration thật;
- đặt version hoặc thứ tự script rõ hơn.

Đề xuất sau này:

```text
db/migrations/
  001_raw_schema.sql
  002_app_schema.sql
  003_auth_schema.sql
  004_audit_schema.sql

db/seeds/
  demo_mvp.sql
  demo_productization.sql
```

## 7. Index/FK

Ưu tiên index:

- appointment: `patient_id`, `doctor_id`, `clinic_id`, `appointment_date`;
- paraclinical result: `patient_id`, `clinic_id`, `completed_at`;
- service: `name`, `code`, `category_id`, `service_type`;
- auth account: `lower(email)`, `account_id`, `session_id`.

FK production nên đặt trên table thật. Nếu `robo_app` còn là view-heavy schema, FK sẽ cần đặt ở schema production riêng hoặc materialized/app tables.

## 8. Test data strategy

Cần có dữ liệu test cố định cho:

- patient có lịch hẹn;
- doctor có lịch hẹn;
- receptionist/clinic_admin theo clinic;
- patient có lab result;
- clinic có đủ public info;
- service exact và generic.

Không rely hoàn toàn vào dữ liệu export vì export có thể thay đổi.
