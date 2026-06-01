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

6. `mvp/README.md`
   - Snapshot MVP đã hoàn thành.
   - Link branch `mvp-v1`, commit MVP, phạm vi đã có/chưa có.

7. `mvp/SCOPE.md`
   - Phạm vi MVP, flow chính, bảng/app views đã dùng.

8. `mvp/TEST_ACCOUNTS.md`
   - Account demo cho patient/doctor/receptionist/clinic_admin.

9. `mvp/TEST_PLAN.md`
   - Test smoke thủ công và automated checks cho MVP.

10. `productization/PLAN.md`
   - Cửa vào cho phase productization sau MVP.
   - Nguyên tắc, milestone tổng quan, definition of done.

11. `productization/ROADMAP.md`
   - Roadmap productization theo P0-P5.
   - Thứ tự triển khai auth, data, private tools, RAG, deployment/test.

12. `productization/AUTH_PLAN.md`
   - Kế hoạch account/session/refresh/logout/OTP production.
   - Cách nối account với patient/staff/clinic/profile.

13. `productization/DATA_PLAN.md`
   - Kế hoạch chuẩn hóa `robo_raw`, `robo_app`, migration và mở rộng 56 bảng.

14. `productization/RAG_PLAN.md`
   - Kế hoạch RAG registry, Qdrant payload, rebuild/incremental sync.

15. `productization/AUDIT_DEPLOYMENT_TEST_PLAN.md`
   - Audit log DB, observability, test strategy và deployment checklist.

16. `AUTHORIZATION_PLAN.md`
   - Kế hoạch xác thực và phân quyền.
   - Role, quyền theo role, policy guard, audit log, row-level filtering.

17. `db/README.md`
   - Giải thích `robo_raw`, `robo_app`.
   - Cách import Excel vào Postgres.
   - Cách tạo app views.
   - Ghi chú nguồn nào phù hợp vector/RAG và cách quản lý source trong `scripts/rag_documents.py`.

18. `backend/README.md`
   - Hướng dẫn riêng cho backend.
   - Kiến trúc backend core + domain adapter.

19. `frontend/README.md`
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
├── doc_system.md
├── mvp/
│   ├── README.md
│   ├── SCOPE.md
│   ├── TEST_ACCOUNTS.md
│   └── TEST_PLAN.md
└── productization/
    ├── AUDIT_DEPLOYMENT_TEST_PLAN.md
    ├── AUTH_PLAN.md
    ├── DATA_PLAN.md
    ├── PLAN.md
    ├── RAG_PLAN.md
    └── ROADMAP.md
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
Phase productization: tiếp tục P1 auth hardening sau session/refresh/change-password/password-reset-token foundation
```

Mục tiêu:

- Giữ branch `mvp-v1` làm snapshot MVP.
- Tiếp tục phát triển trên `main`.
- Làm theo bộ tài liệu trong `docs/productization/`.
- P1 hiện đã có account/session/logout/failed-login lock nền tảng.
- Audit DB, refresh token, change-password, password reset token foundation và login rate-limit nền tảng đã có; ưu tiên tiếp theo: email/SMS/OTP delivery thật, admin account UI và auth hardening.
- Sau đó mới mở rộng data layer, private tools, RAG sync và deployment.
