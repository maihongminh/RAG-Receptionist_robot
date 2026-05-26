# Kế hoạch xác thực và phân quyền

Tài liệu này mô tả hướng xác thực/phân quyền cho robot lễ tân khi project đi từ MVP sang hệ thống thật.

## 1. Nguyên tắc chính

AI bot không tự có quyền truy cập dữ liệu.

Bot chỉ được dùng quyền của người đang tương tác:

```text
người dùng là ai
  -> role là gì
  -> thuộc clinic/organization nào
  -> được dùng tool nào
  -> được xem dòng dữ liệu nào
```

Mọi truy cập dữ liệu nhạy cảm phải đi qua policy guard.

## 2. Các nhóm người dùng

Các role tối thiểu nên có:

```text
guest
patient
doctor
receptionist
clinic_admin
system_admin
```

## 3. Quyền theo role

### `guest`

Khách chưa xác thực.

Được hỏi:

- địa chỉ
- số điện thoại
- email
- giờ làm việc
- dịch vụ/giá
- lịch bác sĩ công khai nếu clinic cho phép
- quy trình khám, quy trình lấy mẫu, cách nhận kết quả

Không được hỏi:

- lịch hẹn cá nhân
- hồ sơ bệnh án
- kết quả xét nghiệm
- thông tin bệnh nhân
- dữ liệu nội bộ

### `patient`

Bệnh nhân đã xác thực.

Được hỏi:

- lịch hẹn của chính mình
- trạng thái kết quả của chính mình
- thông tin cá nhân của chính mình
- hướng dẫn trước/sau khi khám

Không được hỏi:

- thông tin bệnh nhân khác
- danh sách bệnh nhân
- dữ liệu vận hành nội bộ
- dữ liệu tài chính/admin

### `doctor`

Bác sĩ.

Được hỏi:

- lịch khám của mình
- danh sách bệnh nhân được phân công
- hồ sơ bệnh án của bệnh nhân thuộc quyền phụ trách
- kết quả cận lâm sàng liên quan đến bệnh nhân mình phụ trách

Không mặc định được hỏi:

- toàn bộ bệnh nhân trong clinic
- dữ liệu tài chính
- dữ liệu admin hệ thống

### `receptionist`

Lễ tân.

Được hỏi:

- lịch hẹn
- check-in
- thông tin bệnh nhân cơ bản
- thông tin dịch vụ/giá
- phòng/bác sĩ/lịch khám

Không nên được hỏi:

- chẩn đoán chi tiết
- hồ sơ bệnh án nhạy cảm
- dữ liệu tài chính/admin nếu không được cấp quyền

### `clinic_admin`

Admin của một clinic/cơ sở.

Được hỏi trong phạm vi clinic của mình:

- nhân sự
- dịch vụ
- lịch bác sĩ
- lịch hẹn
- cấu hình clinic
- báo cáo vận hành

Vẫn cần audit log khi truy cập dữ liệu nhạy cảm.

### `system_admin`

Admin nền tảng.

Được quyền cao nhất ở cấp hệ thống, nhưng vẫn cần:

- audit log
- giới hạn thao tác nguy hiểm
- phân biệt quyền xem dữ liệu và quyền cấu hình hệ thống

## 4. Luồng backend sau này

Backend nên mở rộng thành:

```text
POST /ask
  -> Auth Context Resolver
  -> LLM/rule Intent Parser
  -> Decision Router
  -> Policy Guard
  -> Tool Registry
  -> Domain Adapter
  -> SQL/RAG/API Tool
  -> Response Generator
  -> Audit Logger
```

Trong đó:

- `Auth Context Resolver`: xác định user/role/clinic/patient/doctor.
- `Policy Guard`: kiểm tra role có được dùng tool và xem dữ liệu không.
- `Audit Logger`: ghi lại truy cập dữ liệu nhạy cảm.

## 5. Auth context đề xuất

Request sau này nên có context đã xác thực:

```json
{
  "question": "Tôi có lịch hẹn nào không?",
  "domain": "clinic",
  "auth": {
    "user_id": "user-uuid",
    "role": "patient",
    "organization_id": "org-uuid",
    "clinic_id": "clinic-uuid",
    "patient_id": "patient-uuid",
    "doctor_id": null
  }
}
```

Ở MVP hiện tại chưa có login/OTP/JWT thật, nhưng API đã nhận `auth` mock trong request để test row-level filtering.

Ví dụ patient đã xác thực trong MVP:

```json
{
  "question": "Tôi có lịch hẹn nào không?",
  "domain": "clinic",
  "auth": {
    "role": "patient",
    "patient_id": "patient-uuid"
  }
}
```

Nếu không có `auth`, bot trả:

```text
requires_auth = true
```

cho dữ liệu cá nhân. Nếu có `auth` hợp lệ, backend lọc `robo_app.appointments` theo scope:

```text
patient      -> WHERE patient_id = auth.patient_id
doctor       -> WHERE doctor_id = auth.doctor_id
receptionist -> WHERE clinic_id = auth.clinic_id
clinic_admin -> WHERE clinic_id = auth.clinic_id
```

Đây là auth context mock để hoàn thiện MVP, chưa thay thế auth thật.

## 6. Tool permission matrix

Ví dụ ma trận quyền ban đầu:

| Tool | guest | patient | doctor | receptionist | clinic_admin | system_admin |
| --- | --- | --- | --- | --- | --- | --- |
| `clinic.get_public_profile` | yes | yes | yes | yes | yes | yes |
| `clinic.search_services` | yes | yes | yes | yes | yes | yes |
| `clinic.search_doctor_schedules` | yes | yes | yes | yes | yes | yes |
| `clinic.lookup_own_appointments` | no | own | no | assigned clinic | clinic | all |
| `clinic.lookup_patient_record` | no | own summary | assigned patients | no | clinic audited | all audited |
| `clinic.create_appointment` | no | self | no | clinic | clinic | all |
| `clinic.manage_services` | no | no | no | no | clinic | all |

Ghi chú:

- `own`: chỉ dữ liệu của chính user/patient.
- `assigned patients`: chỉ bệnh nhân được phân công cho bác sĩ.
- `clinic`: chỉ dữ liệu trong clinic mà user có quyền.
- `audited`: bắt buộc ghi audit log.

## 7. Row-level filtering

Không chỉ kiểm tra role. Query dữ liệu cũng phải lọc theo phạm vi.

Ví dụ patient:

```sql
WHERE patient_id = :auth_patient_id
```

Ví dụ doctor:

```sql
WHERE doctor_id = :auth_doctor_id
```

Ví dụ clinic admin:

```sql
WHERE clinic_id = :auth_clinic_id
```

Không bao giờ để LLM tự tạo SQL vượt qua policy.

## 8. Redaction

Nếu role không đủ quyền, response phải che hoặc bỏ thông tin nhạy cảm.

Ví dụ:

- Che số CCCD/ID.
- Che số điện thoại đầy đủ nếu không cần.
- Không trả nội dung bệnh án chi tiết cho receptionist.
- Chỉ trả trạng thái kết quả, không trả file/kết luận nếu chưa xác thực.

## 9. Audit log

Nên ghi log cho các hành động:

- xem lịch hẹn cá nhân
- xem hồ sơ bệnh án
- xem kết quả xét nghiệm
- xem danh sách bệnh nhân
- tạo/sửa/hủy lịch hẹn
- truy cập dữ liệu bởi admin/system admin

Log tối thiểu:

```text
user_id
role
clinic_id
intent
tool_name
resource_type
resource_id
timestamp
result_status
```

## 10. File backend nên thêm sau

Khi triển khai auth/RBAC thật, nên thêm:

```text
backend/app/core/auth_context.py
backend/app/core/permissions.py
backend/app/core/policy_guard.py
backend/app/core/audit_logger.py
```

Và mở rộng:

```text
backend/app/core/schemas.py
backend/app/core/orchestrator.py
backend/app/core/tool_registry.py
backend/app/domains/clinic/sql_tools.py
```

## 11. Kết luận

Phân quyền là bắt buộc khi project đi vào dữ liệu thật.

Hiện tại MVP mới có:

```text
personal_data -> requires_auth = true
```

Sau này cần bổ sung:

```text
authentication
authorization
policy guard
row-level filtering
redaction
audit log
```

Đặc biệt: LLM chỉ được điều phối, không được bypass policy để truy cập dữ liệu.
