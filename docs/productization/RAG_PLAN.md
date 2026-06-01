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

`scripts/rag_documents.py` nên là registry duy nhất quy định nguồn nào được vector hóa.

Mỗi source nên khai báo:

```text
source_name
source_table
query
id_field
title_field
content_fields
metadata_fields
visibility
clinic_scope
updated_at_field
```

Ví dụ:

```text
knowledge_articles
  source_table: robo_app.knowledge_articles
  visibility: public
  metadata: topic, title, language
```

## 3. Qdrant payload chuẩn

Mỗi vector point cần payload:

```json
{
  "source": "knowledge_articles",
  "source_table": "robo_app.knowledge_articles",
  "source_id": "uuid",
  "domain": "clinic",
  "clinic_id": null,
  "visibility": "public",
  "language": "vi",
  "title": "Quy trình check-in",
  "updated_at": "2026-06-01T00:00:00Z",
  "content_hash": "..."
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
```

Khi dùng full rebuild:

- dễ kiểm soát;
- phù hợp giai đoạn đầu;
- chậm hơn khi dữ liệu lớn.

## 5. Incremental sync flow

Sau full rebuild ổn, thêm incremental:

```text
read source updated_at/content_hash
  -> compare with index manifest
  -> upsert changed docs
  -> delete stale docs
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

Có thể lưu trong Postgres:

```text
robo_rag.index_manifest
```

## 6. Filtering

RAG query production phải có filter:

- `domain = clinic`
- `visibility in allowed_visibility`
- `clinic_id is null OR clinic_id = auth.clinic_id`
- `source not in excluded_sources`

Không để patient data riêng tư vào collection public.

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

