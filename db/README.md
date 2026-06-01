# Postgres database

Thư mục này chứa bộ file để import toàn bộ `clinic_full_export.xlsx` vào Postgres và tạo lớp view sạch cho chatbot.

Kiến trúc dữ liệu hiện tại:

```text
Excel -> robo_raw tables -> robo_app views -> backend/chatbot
                         -> robo_auth accounts/session
```

Thư mục `db/` được chia theo schema:

```text
db/
├── raw/
│   ├── schema.sql
│   └── load.sql
├── app/
│   ├── views.sql
│   └── seed_mvp_demo.sql
├── auth/
│   ├── schema.sql
│   └── seed_demo.sql
├── import_all.sql
├── manifest.json
└── README.md
```

## Cách import

Nếu đã có database Postgres và user/password:

```bash
psql "postgresql://USER:PASSWORD@HOST:PORT/DB_NAME" -f db/import_all.sql
```

Nếu chạy local và đã có role trùng với user hệ điều hành:

```bash
createdb robo_reception
psql robo_reception -f db/import_all.sql
```

## Nếu local Postgres báo lỗi role không tồn tại

Máy hiện tại đang gặp lỗi role `minhmh` chưa tồn tại. Cần tạo role/database bằng user có quyền admin Postgres, ví dụ chạy trong terminal có quyền sudo:

```bash
sudo -u postgres createuser -P minhmh
sudo -u postgres createdb -O minhmh robo_reception
```

Sau đó import:

```bash
psql robo_reception -f db/import_all.sql
```

## Schema `robo_raw`

`robo_raw` là schema chứa dữ liệu gốc import từ Excel.

Đặc điểm:

- Có đủ 56 bảng từ toàn bộ sheet trong Excel.
- Tất cả cột Excel được import dạng `TEXT`.
- Dữ liệu được giữ gần như nguyên bản để đối chiếu, debug và import lại.
- Backend/chatbot không nên query trực tiếp vào schema này nếu không cần.

Lý do để cột dạng `TEXT`: workbook có nhiều kiểu dữ liệu không đồng nhất, nên import raw bằng `TEXT` giúp tránh lỗi type và tránh mất dữ liệu.

Các file được sinh:

- `db/raw/schema.sql`: tạo schema và bảng.
- `db/raw/load.sql`: load CSV vào bảng bằng `\copy`.
- `db/import_all.sql`: chạy cả schema và load.
- `db/app/views.sql`: tạo schema view `robo_app`.
- `db/app/seed_mvp_demo.sql`: bổ sung dữ liệu demo nhất quán cho test MVP, chạy sau khi import raw.
- `db/auth/schema.sql`: tạo schema `robo_auth` cho account/session production foundation.
- `db/auth/seed_demo.sql`: seed account demo cho login email/password.
- `db/manifest.json`: mapping sheet Excel -> bảng Postgres -> cột.
- `data/postgres_csv/*.csv`: dữ liệu CSV đã export từ từng sheet Excel.

Kiểm tra bảng raw:

```sql
\dt robo_raw.*
SELECT count(*) FROM robo_raw.clinics;
SELECT count(*) FROM robo_raw.service_catalog;
SELECT count(*) FROM robo_raw.ref_icd10_codes;
```

Seed dữ liệu demo cho MVP:

```bash
cd /home/minhmh/tool/robo
psql robo_reception -f db/app/seed_mvp_demo.sql
scripts/apply_auth_schema.sh
```

Seed này tách riêng khỏi dữ liệu Excel gốc. `db/app/seed_mvp_demo.sql` bổ sung doctor demo còn thiếu, giờ làm việc/địa chỉ cho các clinic active, appointment tương lai và vài kết quả lab/imaging để test chatbot. `db/auth/seed_demo.sql` bổ sung account demo vào `robo_auth`.

## Schema `robo_app`

`robo_app` là schema sạch cho backend/chatbot sử dụng.

Hiện tại `robo_app` dùng **view**, không phải table thật. View không copy dữ liệu; nó đọc từ `robo_raw`, đổi tên cột, ép kiểu dữ liệu, lọc record đã xóa và join sẵn một số bảng cần thiết.

Tạo/cập nhật view:

```bash
cd /home/minhmh/tool/robo
scripts/apply_app_views.sh
```

Hoặc chạy trực tiếp:

```bash
psql -U minhmh -d robo_reception -h localhost -f db/app/views.sql
```

Các view hiện có:

- `robo_app.clinics`: thông tin cơ sở/phòng khám.
- `robo_app.clinic_settings`: giờ làm việc, slot đặt lịch, cấu hình chung.
- `robo_app.rooms`: phòng, tầng, loại phòng.
- `robo_app.staff`: nhân viên/bác sĩ đã chuẩn hóa một số cột.
- `robo_app.doctors`: subset từ `staff` cho role bác sĩ.
- `robo_app.doctor_schedules`: lịch bác sĩ, join sẵn tên bác sĩ và phòng.
- `robo_app.service_categories`: nhóm dịch vụ.
- `robo_app.services`: dịch vụ, giá, tiền tệ, thời lượng, loại dịch vụ.
- `robo_app.patients`: thông tin bệnh nhân, chỉ dùng sau khi có xác thực.
- `robo_app.appointments`: lịch hẹn, join sẵn bệnh nhân/bác sĩ/dịch vụ.
- `robo_app.paraclinical_results`: chỉ định/kết quả xét nghiệm, chẩn đoán hình ảnh, join sẵn bệnh nhân/dịch vụ/nhân sự liên quan.
- `robo_app.knowledge_articles`: nội dung hướng dẫn/quy trình từ `admin_help_templates`.
- `robo_app.patient_question_templates`: câu hỏi mẫu/gợi ý cho bệnh nhân.

## Schema `robo_auth`

`robo_auth` là schema account/session tách khỏi `robo_app`.

Lý do tách:

- `robo_app` được rebuild từ views trong quá trình development.
- Account/session là dữ liệu vận hành, không nên bị drop khi rebuild app views.
- Productization cần schema auth có thể tiến tới migration/refresh token/logout/audit rõ ràng.

Tạo/cập nhật auth schema:

```bash
cd /home/minhmh/tool/robo
scripts/apply_auth_schema.sh
```

Các bảng auth hiện có:

- `robo_auth.accounts`: email/password hash/status.
- `robo_auth.account_identities`: mapping account với patient/staff/doctor/clinic.
- `robo_auth.account_roles`: role theo scope clinic/organization.
- `robo_auth.sessions`: nền cho refresh token/logout server-side ở bước sau.

Kiểm tra view:

```sql
\dv robo_app.*
SELECT count(*) FROM robo_app.clinics;
SELECT count(*) FROM robo_app.services;
SELECT count(*) FROM robo_app.doctors;
SELECT count(*) FROM robo_app.doctor_schedules;
SELECT count(*) FROM robo_app.appointments;
SELECT count(*) FROM robo_app.paraclinical_results;
```

Query test:

```sql
SELECT name, phone, email, address, city
FROM robo_app.clinics
LIMIT 5;
```

```sql
SELECT code, name, price_amount, currency_code
FROM robo_app.services
WHERE name ILIKE '%CT Brain%'
LIMIT 10;
```

```sql
SELECT doctor_name, day_of_week, start_time, end_time, room_name, floor
FROM robo_app.doctor_schedules
WHERE doctor_name ILIKE '%SUON%'
ORDER BY day_of_week;
```

## Vì sao dùng view trước?

Dùng view ở giai đoạn MVP giúp:

- Không nhân đôi dữ liệu.
- Dễ sửa logic làm sạch dữ liệu.
- Dữ liệu app luôn phản ánh dữ liệu mới trong `robo_raw`.
- Backend có schema dễ query hơn thay vì đọc raw Excel.
- Sau này có thể chuyển view thành table hoặc materialized view nếu cần performance/index/search.

Hướng chuyển đổi sau này:

```text
Hiện tại:
Excel -> robo_raw tables -> robo_app views -> backend/chatbot

Sau này nếu cần production ETL:
Excel/API -> robo_raw tables -> ETL -> robo_app tables/materialized views -> backend/chatbot
```

## Ghi chú RAG

Không vector hóa toàn bộ 56 bảng.

Dữ liệu cần chính xác như giá dịch vụ, lịch bác sĩ, lịch hẹn, thông tin bệnh nhân nên query bằng SQL từ `robo_app`.

Dữ liệu dạng mô tả/ngôn ngữ tự nhiên như quy trình tiếp nhận, hướng dẫn đặt lịch, hướng dẫn trả kết quả, FAQ và nội dung `knowledge_articles` mới phù hợp đưa vào vector/RAG.

Không phải mọi `knowledge_articles` đều nên đưa vào RAG trả lời bệnh nhân. Các tài liệu platform/system overview hoặc phân quyền như topic `overview`, `roles` dễ làm LLM kéo sai ngữ cảnh. Backend hiện lọc bằng:

```text
RAG_EXCLUDED_TOPICS=overview,roles
```

Flow RAG hiện tại:

```text
robo_raw.admin_help_templates
  -> robo_app.knowledge_articles
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Qdrant collection clinic_knowledge
```

`scripts/rag_documents.py` là registry tổng hợp nguồn được phép vector hóa. Hiện file này mới gom `robo_app.knowledge_articles`.

Khi có thêm nhiều nguồn text phù hợp RAG, thêm source vào:

```text
scripts/rag_documents.py
```

Registry này tham chiếu các app view sạch được tạo trong `db/app/views.sql`, ví dụ:

```text
robo_app.knowledge_articles
robo_app.patient_question_templates
clinic policies sau này
service descriptions sau này
```

Mỗi document trong registry nên chuẩn hóa thành schema:

```text
source_table
source_id
topic
title
title_vi
content
content_vi
document_type
access_level
is_active
updated_at
```

Script vector hiện đọc registry:

```text
load_rag_documents() từ scripts/rag_documents.py
```
