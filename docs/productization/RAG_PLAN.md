# Productization RAG plan

MVP hiện dùng:

```text
scripts/rag_documents.py
  -> embedding
  -> Qdrant local qdrant_data
  -> backend knowledge_search
```

Nguồn chính hiện tại:

```text
robo_app.knowledge_articles
```

## 1. RAG dùng cho loại dữ liệu nào?

Nên dùng RAG cho:

- quy trình check-in;
- quy trình nhận kết quả;
- hướng dẫn chuẩn bị trước xét nghiệm;
- FAQ;
- chính sách công khai;
- nội dung mô tả dịch vụ dạng text dài;
- tài liệu vận hành được phép public/internal theo role.

Không nên dùng RAG cho:

- giá dịch vụ chính xác;
- lịch hẹn;
- lịch bác sĩ theo ngày;
- kết quả xét nghiệm;
- hồ sơ bệnh án;
- số dư/thanh toán;
- dữ liệu phải filter chặt theo patient/doctor/clinic.

Dữ liệu có cấu trúc và cần chính xác phải đi SQL/API.

## 2. Document registry

`scripts/rag_documents.py` là registry duy nhất quy định nguồn nào được vector hóa.

Mỗi source hiện khai báo:

```text
source_name
source_view
query
source_tables
domain
default_access_level
default_language
```

Ví dụ:

```text
knowledge_articles
  source_view: robo_app.knowledge_articles
  source_tables: robo_raw.admin_help_templates
  domain: clinic
  default_access_level: public
  default_language: vi
```

Registry có checker riêng:

```bash
cd /home/minhmh/tool/robo
backend/.venv/bin/python scripts/check_rag_registry.py
```

Checker này bắt các lỗi cấu hình như trùng `source_name`, source không đi qua `robo_app`, thiếu source table gốc, access/language sai.

## 3. Qdrant payload chuẩn

Mỗi vector point cần payload:

```json
{
  "source": "knowledge_articles",
  "source_table": "robo_app.knowledge_articles",
  "source_view": "robo_app.knowledge_articles",
  "source_tables": ["robo_raw.admin_help_templates"],
  "source_id": "uuid",
  "chunk_index": 0,
  "domain": "clinic",
  "clinic_id": null,
  "access_level": "public",
  "visibility": "public",
  "language": "vi",
  "title": "Quy trình check-in",
  "updated_at": "2026-06-01T00:00:00Z",
  "content_hash": "...",
  "qdrant_collection": "clinic_knowledge"
}
```

## 4. Build/rebuild flow

Full rebuild:

```text
Postgres
  -> rag_documents.py load all valid documents
  -> embed
  -> recreate Qdrant collection
  -> upsert all points
  -> replace robo_rag.index_manifest for the collection
```

Khi dùng full rebuild:

- dễ kiểm soát;
- phù hợp giai đoạn đầu;
- chậm hơn khi dữ liệu lớn.

## 5. Incremental sync flow

Sau full rebuild ổn, incremental sync hiện có trong:

```text
scripts/build_qdrant_index.py --mode incremental
```

Cần lưu manifest:

```text
source
source_id
content_hash
updated_at
indexed_at
qdrant_point_id
```

Hiện đã có manifest foundation trong Postgres:

```text
robo_rag.index_manifest
```

Schema:

```bash
cd /home/minhmh/tool/robo
scripts/apply_rag_schema.sh
```

`scripts/build_qdrant_index.py` ghi lại manifest sau khi upsert Qdrant thành công. Incremental sync dùng bảng này để so `source/source_id/content_hash` và quyết định document nào cần xử lý.

Trạng thái hiện tại:

- `--mode full`: recreate collection, embed toàn bộ document hợp lệ, replace toàn bộ manifest của collection.
- `--mode incremental`: đọc `robo_rag.index_manifest`, so `source/source_id/content_hash`, chỉ embed/upsert document mới hoặc đã đổi hash, xóa point stale không còn trong registry.
- Nếu thiếu collection hoặc manifest, incremental tự fallback sang full rebuild.

## 6. Filtering

RAG query production phải có filter:

- `domain = clinic`
- `access_level/visibility in allowed_visibility`
- `clinic_id is null OR clinic_id = auth.clinic_id`
- `source not in excluded_sources`

Không để patient data riêng tư vào collection public.

Hiện đã áp dụng filter tối thiểu cho vector search:

```text
domain = clinic
access_level = public
```

Filter theo `clinic_id` và internal/private visibility sẽ mở khi có nguồn RAG scoped theo clinic hoặc role.

## 7. Response rule

LLM grounded answer chỉ được dùng context đã retrieve.

Nếu context thấp score hoặc rỗng:

- trả lời không tìm thấy;
- không tự bịa quy trình;
- có thể gợi ý hỏi lễ tân/nhân viên.

## 8. RAG test plan

Test cần có:

- exact FAQ query;
- paraphrase query;
- query không có dữ liệu;
- query bị filter bởi clinic/visibility;
- stale document sau update;
- rebuild từ zero.
