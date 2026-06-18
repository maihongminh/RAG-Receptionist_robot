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

Inventory chính thức:

```text
db/app/raw_table_inventory.json
docs/productization/RAW_TABLE_INVENTORY.md
```

Checker:

```bash
backend/.venv/bin/python scripts/check_raw_table_inventory.py
```

Inventory hiện khóa đủ `56` bảng `robo_raw` và phân loại từng bảng theo group, access level, status, batch, app view/tool hiện có hoặc dự kiến.

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
- `service_lab_indicators`
- `service_packages`
- `service_package_items`

Dùng cho:

- địa chỉ/giờ làm việc;
- dịch vụ/giá;
- chỉ số xét nghiệm và thành phần gói khám;
- lịch bác sĩ;
- phòng/khu vực.

### Private/patient

- `patients`
- `appointments`
- `visits`
- `paraclinical_orders`
- `partner_lab_requests`
- `partner_onsite_collections`
- `medical_records`
- `vital_signs`

Dùng cho:

- lịch hẹn cá nhân;
- kết quả xét nghiệm/cận lâm sàng;
- yêu cầu xét nghiệm từ đối tác và trạng thái lấy mẫu tận nơi;
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
- `db/app/contract.json`: contract view/cột/access-level/source/tool cho `robo_app`.
- `db/app/tool_map.json`: mapping intent/tool -> view contract -> source table -> policy/test.
- `db/app/seed_mvp_demo.sql`: patch demo data.
- `db/app/seed_productization_demo.sql`: demo data cho các use case mở sau MVP.

Productization cần:

- idempotent scripts;
- tách seed demo khỏi migration thật;
- giữ seed MVP ở `seed_mvp_demo.sql`, seed mở rộng productization ở `seed_productization_demo.sql`;
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

Trong cấu trúc hiện tại, chưa tách sang `db/seeds/` để tránh đổi lớn. Quy ước đang dùng:

```text
db/app/seed_mvp_demo.sql
db/app/seed_productization_demo.sql
scripts/apply_productization_seed.sh
```

## 7. Index/FK

Ưu tiên index:

- appointment: `patient_id`, `doctor_id`, `clinic_id`, `appointment_date`;
- paraclinical result: `patient_id`, `clinic_id`, `completed_at`;
- service: `name`, `code`, `category_id`, `service_type`;
- auth account: `lower(email)`, `account_id`, `session_id`.

FK production nên đặt trên table thật. Nếu `robo_app` còn là view-heavy schema, FK sẽ cần đặt ở schema production riêng hoặc materialized/app tables.

## 8. Contract validation

P2 bắt đầu có guardrail bằng:

```text
db/app/contract.json
db/app/tool_map.json
scripts/check_app_contract.py
scripts/check_tool_map.py
backend/tests/test_app_data_contract.py
```

Quy trình khi thêm bảng/view cho tool mới:

```text
1. Thêm hoặc sửa view trong db/app/views.sql.
2. Cập nhật db/app/contract.json:
   - view name;
   - source_tables;
   - access_level public/operational/private;
   - tool sử dụng;
   - các cột bắt buộc và data_type.
3. Cập nhật db/app/tool_map.json:
   - intent gọi tool;
   - data_source sql/rag/auth/none;
   - app view trực tiếp được query;
   - source table gốc;
   - allowed_roles;
   - scope_rule;
   - test bảo vệ.
4. Chạy scripts/apply_app_views.sh.
5. Chạy backend/.venv/bin/python scripts/check_app_contract.py.
6. Chạy backend/.venv/bin/python scripts/check_tool_map.py.
7. Nếu bảng/source thiếu data, thêm khoảng 5 record demo vào `db/app/seed_productization_demo.sql`.
8. Thêm/cập nhật SQL tool + policy + test.
```

Backend domain tools không được query `robo_raw` trực tiếp. Raw chỉ là import/debug layer.

## 9. Batch đã mở sau MVP

Các use case productization đã có app contract, tool map, policy và test:

- Patient profile: `robo_app.patients` -> `clinic.lookup_patient_profile`.
- Patient timeline: `robo_app.appointments`, `robo_app.paraclinical_results` -> `clinic.lookup_patient_timeline`.
- Visit summary: `robo_app.patient_visit_summaries` -> `clinic.lookup_visit_summary`.
- Billing summary: `robo_app.billing_records` -> `clinic.lookup_billing_summary`.
- Service/package detail: `robo_app.service_lab_indicators`, `robo_app.service_packages`, `robo_app.service_package_items`.
- Partner lab tracking: `robo_app.partner_lab_requests`, `robo_app.partner_onsite_collections` -> `clinic.lookup_partner_lab_requests`.

Smoke hiện tại:

```text
app contract: 21 views
tool map: 18 tools
raw inventory: 56 tables
chatbot scenarios: 24/24
backend tests: 207 passed
```

Ví dụ đã làm sau productization foundation:

```text
patient_profile_summary
  -> robo_raw.patients
  -> robo_app.patients
  -> clinic.lookup_patient_profile
  -> PolicyGuard + role permission
  -> backend tests + MVP scenario
```

Tool này dùng `data_source="auth"` vì phải đi qua auth scope. `patient` chỉ thấy hồ sơ của chính mình; `receptionist` và `clinic_admin` chỉ thấy bệnh nhân trong clinic của account; `system_admin` có thể xem toàn bộ khi role này được dùng trong môi trường quản trị thật.

```text
patient_timeline_summary
  -> robo_raw.patients + robo_raw.appointments + robo_raw.paraclinical_orders
  -> robo_app.patients + robo_app.appointments + robo_app.paraclinical_results
  -> clinic.lookup_patient_timeline
  -> PolicyGuard + role permission
  -> backend tests + MVP scenario
```

Timeline hiện chỉ gom lịch hẹn và cận lâm sàng vì đây là các view đã có contract sạch. `receptionist`, `clinic_admin` và `system_admin` phải nêu bệnh nhân cụ thể trước khi tool trả timeline. Dữ liệu hiện có đã đủ cho test, nên `seed_productization_demo.sql` chưa cần thêm record ở bước này.

```text
visit_summary_lookup
  -> robo_raw.medical_records + robo_raw.visits + robo_raw.vital_signs
  -> robo_app.patient_visit_summaries
  -> clinic.lookup_visit_summary
  -> PolicyGuard + role permission
  -> backend tests + MVP scenario
```

Visit summary mở nhóm dữ liệu khám bệnh nhạy cảm hơn timeline. Vì vậy `patient` chỉ thấy chính mình; `doctor`, `receptionist`, `clinic_admin` và `system_admin` đều phải nêu bệnh nhân cụ thể trước khi tool trả dữ liệu. Bước này đã thêm 5 demo records cho từng bảng `visits`, `medical_records`, `vital_signs` trong `db/app/seed_productization_demo.sql`.

```text
billing_summary_lookup
  -> robo_raw.diagnostic_walk_in_patients
  -> robo_app.billing_records
  -> clinic.lookup_billing_summary
  -> PolicyGuard + role permission
  -> backend tests + MVP scenario
```

Billing summary hiện chỉ mở hóa đơn/thanh toán cá nhân từ diagnostic walk-in. Billing doanh nghiệp/group examination chưa mở vì đó là use case khác. Bước này đã thêm 5 demo billing records trong `db/app/seed_productization_demo.sql`.

```text
partner_lab_request_lookup
  -> robo_raw.partner_lab_requests + robo_raw.partner_onsite_collections
  -> robo_app.partner_lab_requests + robo_app.partner_onsite_collections
  -> clinic.lookup_partner_lab_requests
  -> PolicyGuard + role permission
  -> backend tests + MVP/productization scenario
```

Partner lab tracking mở dữ liệu yêu cầu xét nghiệm và lấy mẫu tận nơi. `patient` chỉ thấy request đã match với `patient_id` của mình; `receptionist`, `clinic_admin` và `system_admin` phải nêu bệnh nhân hoặc mã yêu cầu cụ thể trước khi tool trả dữ liệu. Bước này đã thêm 5 demo partner lab requests và 2 demo onsite collections trong `db/app/seed_productization_demo.sql`.

## 9. Test data strategy

Cần có dữ liệu test cố định cho:

- patient có lịch hẹn;
- patient có hồ sơ hành chính để test `patient_profile_summary`;
- doctor có lịch hẹn;
- receptionist/clinic_admin theo clinic;
- patient có lab result;
- clinic có đủ public info;
- service exact và generic.

Không rely hoàn toàn vào dữ liệu export vì export có thể thay đổi.
