# Mục lục tài liệu

File này mô tả chức năng của từng tài liệu trong project. Toàn bộ tài liệu cấp project hiện nằm trong `docs/` để root thư mục gọn hơn.

## Tài liệu nên đọc theo thứ tự

1. `PROGRESS.md`
   - Xem project đang ở đâu.
   - Ghi lại phần đã làm, chưa làm, bước tiếp theo.
   - Sau mỗi lần hoàn thành một task, cập nhật file này.

2. `RUNBOOK.md`
   - Cách chạy backend/frontend.
   - Cách test API bằng curl.
   - Cách kiểm tra database.
   - Cách xử lý port bị chiếm.

3. `BACKEND_FLOW.md`
   - Giải thích flow backend khi người dùng hỏi.
   - Mô tả từng bước trong orchestrator.
   - Mô tả cây thư mục và chức năng từng file backend/frontend/db/scripts.
   - Đã bao gồm các file mới của RAG vector: `embedding_client.py`, `qdrant_store.py`, `build_qdrant_index.py`, `qdrant_data/`.

4. `doc_system.md`
   - Tài liệu tổng quan hệ thống.
   - Đánh giá trạng thái data layer, RAG, LLM, scale đa lĩnh vực.
   - Mô tả flow hiện tại `knowledge_articles -> Qdrant` và hướng sau này `rag_documents -> Qdrant`.

5. `ROBOT_RECEPTION_ROADMAP.md`
   - Roadmap sản phẩm/kiến trúc dài hạn.
   - Thứ tự triển khai từ DB, backend, UI, RAG, LLM, auth, STT/TTS.

6. `AUTHORIZATION_PLAN.md`
   - Kế hoạch xác thực và phân quyền.
   - Role, quyền theo role, policy guard, audit log, row-level filtering.

7. `db/README.md`
   - Giải thích `robo_raw`, `robo_app`.
   - Cách import Excel vào Postgres.
   - Cách tạo app views.
   - Ghi chú nguồn nào phù hợp vector/RAG và cách quản lý source trong `scripts/rag_documents.py`.

8. `backend/README.md`
   - Hướng dẫn riêng cho backend.
   - Kiến trúc backend core + domain adapter.

9. `frontend/README.md`
   - Hướng dẫn riêng cho frontend.

## Cấu trúc docs

```text
docs/
├── AUTHORIZATION_PLAN.md
├── BACKEND_FLOW.md
├── DOCS_INDEX.md
├── PROGRESS.md
├── ROBOT_RECEPTION_ROADMAP.md
├── RUNBOOK.md
└── doc_system.md
```

## Quy tắc cập nhật tài liệu

Trước khi làm một phần lớn mới:

1. Cập nhật `PROGRESS.md` để ghi rõ task sắp làm.
2. Nếu task ảnh hưởng kiến trúc, cập nhật `BACKEND_FLOW.md` hoặc `doc_system.md`.
3. Nếu task ảnh hưởng cách chạy/test, cập nhật `RUNBOOK.md`.
4. Sau khi làm xong, cập nhật lại `PROGRESS.md` với kết quả và số test.

## Task hiện tại

Task tiếp theo:

```text
Hoàn thiện auth/login thật sau khi ổn định MVP chat flow
```

Mục tiêu:

- Thay auth mock hiện tại bằng cơ chế xác thực thật.
- Sinh auth context tin cậy gồm `role`, `patient_id`, `doctor_id`, `clinic_id`.
- Dữ liệu cá nhân tiếp tục đi qua `PolicyGuard` trước khi query tool.
- MVP hiện đã lookup lịch hẹn theo scope auth mock.
- Grounded LLM answer đã có bước đầu cho `knowledge_search`; không đưa dữ liệu cá nhân vào LLM nếu chưa được policy cho phép.
- Flow RAG hiện tại build vector từ registry `scripts/rag_documents.py`.
- `scripts/rag_documents.py` hiện gom `robo_app.knowledge_articles`; sau này thêm nguồn text hợp lệ vào file này.
- SQL vẫn xử lý giá dịch vụ, lịch bác sĩ, thông tin cơ sở và dữ liệu cá nhân.
- UI Trace vẫn phải hiện parser, sources và data/debug để kiểm tra nguồn câu trả lời.
- MVP đã có short conversation context in-memory cho follow-up như `xem tiếp`, `xem chi tiết nhóm 35`.
- Medical advice đang trả lời theo hướng triage an toàn, bám triệu chứng nhưng không chẩn đoán.
- Auth mock đã manual test ổn cho guest, patient, doctor, receptionist và clinic_admin.
