# Productization phase plan

Tài liệu này là cửa vào cho phase productization sau MVP `mvp-v1`.

Mục tiêu của phase này không phải thêm nhiều tính năng nhanh, mà là biến MVP thành nền tảng có thể vận hành lâu dài:

- dữ liệu có ranh giới rõ;
- auth/account không còn là bảng demo;
- quyền truy cập private data có audit;
- RAG có cơ chế sync/rebuild rõ ràng;
- test và deployment có thể lặp lại;
- code vẫn giữ kiến trúc core + domain adapter để sau này mở rộng ngoài clinic.

## Snapshot đầu vào

MVP đã được lưu tại branch:

```text
mvp-v1
```

Commit MVP:

```text
e8477eb Add email password auth login
```

Tiếp tục phát triển productization trên:

```text
main
```

## Nguyên tắc phase productization

1. Không phá MVP đang chạy.
2. Mỗi phần production hóa phải có migration/seed/test/doc đi kèm.
3. Không đưa toàn bộ 56 bảng vào tool/RAG cùng lúc; mở theo domain use case.
4. Dữ liệu cá nhân chỉ được truy xuất sau auth + policy + audit.
5. SQL là source-of-truth cho dữ liệu có cấu trúc; RAG chỉ dùng cho nội dung text/knowledge phù hợp.
6. LLM chỉ diễn đạt sau khi dữ liệu đã được truy xuất và kiểm soát; không được tự quyết quyền truy cập.
7. Debug/trace phải tắt hoặc giới hạn ở production.

## Bộ tài liệu của phase này

Đọc theo thứ tự:

1. `ROADMAP.md`
   - Lộ trình theo milestone.
   - Thứ tự ưu tiên và tiêu chí hoàn thành.

2. `AUTH_PLAN.md`
   - Account production, password, session/refresh token, logout, OTP/reset password.
   - Cách nối account với patient/staff/clinic.

3. `DATA_PLAN.md`
   - Chuẩn hóa `robo_raw`, `robo_app`, migration, view/table application layer.
   - Cách mở rộng từ 12 bảng MVP lên 56 bảng có kiểm soát.

4. `RAG_PLAN.md`
   - RAG document registry, Qdrant collection, metadata, rebuild/incremental sync.
   - Quy tắc bảng nào nên/không nên vector hóa.

5. `AUDIT_DEPLOYMENT_TEST_PLAN.md`
   - Audit log DB, observability, test matrix, Docker/deployment.

## Milestone tổng quan

```text
P0 - Baseline freeze
  -> giữ branch mvp-v1
  -> main sạch
  -> docs productization hoàn thành

P1 - Auth/account production foundation
  -> account schema chính thức
  -> password hash + session DB
  -> refresh token phase sau
  -> logout server-side
  -> auth context đáng tin cậy

P2 - Data/application layer hardening
  -> phân tầng raw/app rõ hơn
  -> migration/idempotent seed
  -> FK/index/contract cho bảng trọng yếu

P3 - Private data expansion + audit
  -> mở rộng tool cho lab result, visit, patient summary
  -> policy matrix chi tiết
  -> audit log DB

P4 - RAG production sync
  -> document registry chuẩn
  -> metadata filter
  -> rebuild/incremental sync script

P5 - Deployment/test hardening
  -> docker compose
  -> env split dev/prod
  -> integration/e2e tests
  -> production trace policy
```

## Definition of Done cho phase productization

Phase này được xem là đạt khi:

- có account/session production tối thiểu thay cho demo account table;
- private `/ask` dựa vào token/session thay vì request-body auth mock;
- private data access đều ghi audit DB;
- các SQL tools chính có test tích hợp với Postgres;
- RAG có script rebuild rõ ràng và registry nguồn dữ liệu có kiểm soát;
- backend/frontend/Qdrant/Postgres có thể chạy bằng Docker compose;
- docs/runbook đủ để người khác clone repo, seed DB, build RAG, chạy demo end-to-end.
