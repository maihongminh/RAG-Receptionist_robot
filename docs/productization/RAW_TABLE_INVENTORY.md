# Raw table inventory

Mục tiêu của file này là khóa lại bức tranh 56 bảng `robo_raw` trước khi mở rộng productization.

Nguồn máy đọc được:

```text
db/app/raw_table_inventory.json
```

Checker:

```bash
cd /home/minhmh/tool/robo
backend/.venv/bin/python scripts/check_raw_table_inventory.py
```

## Tổng quan

```text
robo_raw: 56 bảng
robo_app contract hiện tại: 22 view
backend policy/tool map hiện tại: 18 mapped tools
```

Nguyên tắc:

- Không expose toàn bộ 56 bảng trực tiếp cho backend.
- Không đưa toàn bộ 56 bảng vào RAG.
- Mỗi bảng chỉ mở khi có use case, app view, policy, test và demo data rõ.
- Dữ liệu riêng tư/nhạy cảm phải đi qua `PolicyGuard` và audit.

## Nhóm current

Các bảng đã được dùng qua `robo_app`, SQL tool hoặc RAG:

| Raw table | App view/RAG | Mục đích |
| --- | --- | --- |
| `admin_help_templates` | `robo_app.knowledge_articles`, RAG | hướng dẫn/quy trình/FAQ public |
| `appointment_requests` | `robo_app.appointment_requests` | contract nền cho yêu cầu đặt lịch |
| `appointments` | `robo_app.appointments` | lịch hẹn cá nhân, timeline |
| `clinic_general_settings` | `robo_app.clinic_settings` | giờ làm việc/cấu hình phòng khám |
| `clinics` | `robo_app.clinics` | thông tin cơ sở public |
| `diagnostic_walk_in_patients` | `robo_app.billing_records` | billing/payment summary |
| `doctor_schedules` | `robo_app.doctor_schedules` | lịch bác sĩ |
| `medical_records` | `robo_app.patient_visit_summaries` | visit/medical summary |
| `partner_lab_requests` | `robo_app.partner_lab_requests` | theo dõi yêu cầu xét nghiệm từ đối tác |
| `partner_onsite_collections` | `robo_app.partner_onsite_collections` | theo dõi lịch/trạng thái lấy mẫu tận nơi |
| `paraclinical_orders` | `robo_app.paraclinical_results` | kết quả/chỉ định cận lâm sàng |
| `patient_question_templates` | `robo_app.patient_question_templates`, RAG | mẫu câu hỏi gợi ý cho bệnh nhân |
| `patients` | `robo_app.patients` | hồ sơ hành chính bệnh nhân, scope private |
| `rooms` | `robo_app.rooms`, schedule join | phòng/tầng/phòng khám |
| `service_catalog` | `robo_app.services`, `robo_app.service_rag_guides` | dịch vụ/giá/catalog và guide RAG public không chứa giá |
| `service_categories` | `robo_app.service_categories`, `robo_app.service_rag_guides` | nhóm dịch vụ và guide RAG public |
| `service_lab_indicators` | `robo_app.service_lab_indicators` | chỉ số/analyte của xét nghiệm |
| `service_package_items` | `robo_app.service_package_items` | thành phần dịch vụ trong gói |
| `service_packages` | `robo_app.service_packages` | gói dịch vụ/giá gói |
| `staff` | `robo_app.staff`, `robo_app.doctors` | nhân sự/bác sĩ |
| `visits` | `robo_app.patient_visit_summaries` | visit summary |
| `vital_signs` | `robo_app.patient_visit_summaries` | sinh hiệu gần nhất |

## Batch đề xuất

### Batch 1 - Scheduling

Mở rộng đặt lịch/request:

- `appointment_requests`

Use case:

- contract nền đã có qua `robo_app.appointment_requests`;
- tạo yêu cầu đặt lịch;
- xem trạng thái yêu cầu đặt lịch;
- receptionist duyệt/chuyển thành appointment.

### Batch 2 - Lab/Diagnostics

Mở rộng xét nghiệm/chẩn đoán:

- `service_lab_indicators`
- `partner_lab_requests`
- `partner_onsite_collections`
- `security_check_results`
- `ref_icd10_codes`

Use case:

- public SQL tool đã có qua `clinic.lookup_lab_indicator_detail`;
- xem chỉ số xét nghiệm thuộc dịch vụ nào;
- private SQL tool đã có qua `clinic.lookup_partner_lab_requests`;
- theo dõi yêu cầu xét nghiệm từ đối tác;
- xem trạng thái lấy mẫu tận nơi;
- dùng ICD10 làm reference, không dùng để chẩn đoán tự động.

### Batch 3 - Billing/Packages/Corporate

Mở rộng tài chính/dịch vụ gói:

- `clinic_currencies`
- `clinic_currency_rate_versions`
- `ref_currencies`
- `service_packages`
- `service_package_items`
- `crm_corporate_accounts`
- `crm_loyalty_tiers`
- `group_examinations`

Use case:

- public SQL tool đã có qua `clinic.lookup_service_package_detail`;
- chuẩn hóa tiền tệ/giá;
- tra gói dịch vụ;
- group/corporate examination;
- billing doanh nghiệp.

### Batch 4 - Account Scope/Operations

Mở rộng vận hành và phân quyền thật:

- `clinic_memberships`
- `organization_memberships`
- `organizations`
- `platform_admins`
- `profiles`
- `user_roles`
- `beds`
- `diagnostic_machines`
- `examination_zones`
- `lis_accession_counters`
- `tasks`

Use case:

- role/scope từ dữ liệu thật thay vì seed demo;
- multi-clinic/organization;
- vận hành phòng/khu/máy/giường/task.

### Partner/Platform Later

Giữ lại sau khi core product ổn:

- `partner_audit_logs`
- `partner_clinics`
- `partner_users`
- `clinic_feature_flags`
- `clinic_subscriptions`
- `clinic_type_ai_capabilities`
- `clinic_type_modules`
- `platform_pricing_config`
- `ref_clinic_type_features`
- `subscription_plans`
- `ai_boundary_metadata`
- `sensitive_field_definitions`
- `location_countries`
- `location_provinces`
- `translations`

## Cách mở một bảng mới

Quy trình chuẩn:

```text
1. Chọn use case cụ thể.
2. Cập nhật db/app/raw_table_inventory.json nếu batch/status thay đổi.
3. Tạo/sửa view trong db/app/views.sql.
4. Cập nhật db/app/contract.json.
5. Cập nhật db/app/tool_map.json nếu có tool mới.
6. Thêm demo data vào db/app/seed_productization_demo.sql nếu thiếu.
7. Thêm SQL tool/RAG source/policy/test.
8. Chạy smoke:
   scripts/check_productization_smoke.sh
```

Không mở bảng mới chỉ vì “có trong Excel”. Mỗi bảng cần có đường đi rõ:

```text
raw table -> app contract -> tool/RAG -> policy -> test -> docs
```
