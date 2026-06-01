# Tài liệu hệ thống

## 1. Trạng thái hiện tại

Project hiện tại đã hoàn thành phần nền tảng dữ liệu cho domain bệnh viện/phòng khám:

```text
Excel export
  -> robo_raw tables
  -> robo_app views
  -> backend API /ask
  -> frontend chatbot web
```

Database local:

```text
Database: robo_reception
Host: localhost
Port: 5432
User: minhmh
```

Không lưu password database trong tài liệu hoặc source code. Password nên nhập qua terminal hoặc đặt trong `.env` local không commit.

Lệnh kết nối:

```bash
psql -U minhmh -d robo_reception -h localhost
```

Hướng dẫn chạy backend + frontend nằm ở `docs/RUNBOOK.md`.

Kế hoạch xác thực/phân quyền nằm ở `docs/AUTHORIZATION_PLAN.md`.

Mục lục tài liệu nằm ở `docs/DOCS_INDEX.md`.

## 2. Data layer

### `robo_raw`

`robo_raw` chứa dữ liệu gốc import từ Excel.

Đặc điểm:

- Có đủ 56 bảng từ toàn bộ workbook.
- Các cột đang để dạng `TEXT` để giữ nguyên dữ liệu và tránh lỗi import.
- Dùng để đối chiếu, debug, import lại.
- Backend/chatbot không nên query trực tiếp nếu không cần.

### `robo_app`

`robo_app` là schema sạch cho backend/chatbot.

Hiện tại `robo_app` là view, chưa phải table thật.

Các view đang có:

- `robo_app.clinics`
- `robo_app.clinic_settings`
- `robo_app.rooms`
- `robo_app.staff`
- `robo_app.doctors`
- `robo_app.doctor_schedules`
- `robo_app.service_categories`
- `robo_app.services`
- `robo_app.patients`
- `robo_app.appointments`
- `robo_app.paraclinical_results`
- `robo_app.knowledge_articles`
- `robo_app.patient_question_templates`

Các bảng raw đang được dùng để tạo view:

- `robo_raw.clinics`
- `robo_raw.clinic_general_settings`
- `robo_raw.rooms`
- `robo_raw.staff`
- `robo_raw.doctor_schedules`
- `robo_raw.service_categories`
- `robo_raw.service_catalog`
- `robo_raw.patients`
- `robo_raw.appointments`
- `robo_raw.paraclinical_orders`
- `robo_raw.admin_help_templates`
- `robo_raw.patient_question_templates`

## 3. Đánh giá khả năng RAG

Project đã có RAG vector local bằng Qdrant cho dữ liệu hướng dẫn/quy trình/FAQ.

Nguồn dữ liệu nên đưa vào RAG:

- Hiện tại: `scripts/rag_documents.py`
- Nguồn ban đầu trong registry: `robo_app.knowledge_articles`
- nội dung hướng dẫn/quy trình
- FAQ
- mô tả dịch vụ nếu cần semantic search

Không nên vector hóa toàn bộ 56 bảng.

Dữ liệu cần chính xác nên query SQL:

- giá dịch vụ
- lịch bác sĩ
- lịch hẹn
- thông tin bệnh nhân
- phòng/tầng

Luồng đúng:

```text
Question
  -> LLM Intent Parser hoặc rule fallback
  -> PolicyGuard
  -> Intent/Decision Router
  -> SQL nếu là dữ liệu chính xác
  -> Vector search nếu là hướng dẫn/quy trình/FAQ
  -> Response Generator
```

Sau khi có Qdrant vector store, nên nâng response layer thành grounded generation:

```text
Question
  -> Intent/entities
  -> SQL/RAG retrieval
  -> Context + sources
  -> LLM diễn đạt câu trả lời dựa trên context
  -> Answer + trace
```

RAG không thay thế SQL. Vector search chỉ dùng để tìm đoạn hướng dẫn/quy trình/FAQ phù hợp. Với giá dịch vụ, lịch bác sĩ, lịch hẹn và dữ liệu bệnh nhân, backend vẫn phải query SQL/API có kiểm soát.

Flow RAG hiện tại:

```text
robo_raw.admin_help_templates
  -> robo_app.knowledge_articles
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Ollama nomic-embed-text
  -> Qdrant qdrant_data / clinic_knowledge
```

Flow RAG khi nhiều bảng/view được phép vector hóa:

```text
robo_app.knowledge_articles
robo_app.patient_question_templates
robo_app.clinic_policies sau này
robo_app.service_descriptions sau này
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Qdrant
```

`scripts/rag_documents.py` nên là registry tổng hợp có schema ổn định:

```text
source_table
source_id
topic
title
content
language
access_level
updated_at
is_active
```

Khi cần thêm nguồn RAG mới, ưu tiên thêm source vào `scripts/rag_documents.py` và tham chiếu các app view sạch từ `db/app_views.sql`.

## 4. Đánh giá khả năng LLM

Project đã có backend core để gắn LLM và đã có provider OpenAI-compatible/Ollama local cho bước parse intent/entities.

Mặc định LLM đang tắt:

```text
LLM_PROVIDER=none
```

Khi bật provider LLM, backend gọi LLM để chuyển câu hỏi thành `Intent` JSON. Nếu LLM lỗi, thiếu key hoặc trả sai schema, backend fallback về rule parser.

LLM nên nằm trong khối:

```text
AI Agent Orchestrator
```

Vai trò LLM hiện tại:

- hiểu câu hỏi người dùng
- phân loại intent
- trích xuất tham số
- hỗ trợ chọn route/tool qua decision router

Vai trò LLM cuối flow hiện có 2 chế độ:

- `knowledge_search`: nhận context đã truy xuất từ RAG/SQL và diễn đạt câu trả lời tự nhiên hơn.
- SQL/Auth formatter: chỉ chạy khi `LLM_PROVIDER=ollama`, nhận `ToolResult.rows` đã qua policy và viết lại cho dễ đọc.
- tóm tắt nhiều đoạn dữ liệu thành câu trả lời ngắn gọn
- giữ đúng nguồn dữ liệu và không tự bổ sung thông tin ngoài context

LLM không phải nguồn sự thật. SQL/RAG/API mới là nguồn dữ liệu. Với `knowledge_search`, `GroundedResponseGenerator` thử diễn đạt từ context. Với dữ liệu cá nhân, formatter chỉ dùng Ollama local sau khi `PolicyGuard` đã cho phép. Nếu LLM lỗi hoặc tắt thì fallback về `ResponseGenerator` template.

Luồng backend đã scaffold:

```text
POST /ask
  -> Orchestrator
  -> LLM Intent Parser hoặc rule fallback
  -> Normalize intent routing contracts
  -> PolicyGuard
  -> Decision Router
  -> Tool Registry
  -> Domain Adapter
  -> SQL/RAG/Auth tool
  -> Grounded LLM Response Generator cho knowledge_search nếu có context
  -> Template Response Generator fallback
  -> answer
```

Prompt/contract cho grounded generation hiện tại và khi mở rộng:

```text
Input:
  - question
  - intent/entities
  - retrieved rows/chunks
  - sources
  - auth/policy decision đã được kiểm tra

Rules:
  - chỉ trả lời dựa trên retrieved context
  - không bịa giá, lịch, địa chỉ, kết quả cá nhân
  - không expose dữ liệu cá nhân nếu PolicyGuard chưa cho phép
  - nếu context không đủ, trả lời rằng chưa tìm thấy dữ liệu phù hợp
  - giữ trace để debug được nguồn câu trả lời
```

## 5. Đánh giá khả năng scale đa lĩnh vực

Hiện tại data layer mới phục vụ domain bệnh viện/phòng khám.

Tuy nhiên hướng kiến trúc đã đúng để scale nếu backend được viết theo core + domain adapter.

Cấu trúc backend nên làm:

```text
backend/
  app/
    main.py
    api/
      ask.py
    core/
      orchestrator.py
      schemas.py
      decision_router.py
      tool_registry.py
      response_generator.py
    auth/
      auth_context.py
      permissions.py
      policy_guard.py
      audit_logger.py
    llm/
      llm_client.py
    rag/
      grounded_response_generator.py
      embedding_client.py
      qdrant_store.py
      rag_config.py
    domains/
      clinic/
        adapter.py
        sql_tools.py
        prompts.py
      hotel/
        adapter.py
      restaurant/
        adapter.py
      school/
        adapter.py
```

Nguyên tắc:

- `core` không biết chi tiết bệnh viện/khách sạn/nhà hàng/trường học.
- `core` chỉ điều phối intent, route, tool registry và response template.
- `auth`, `llm`, `rag` giữ phần phân quyền, model và retrieval riêng để dễ kiểm soát.
- domain adapter mới biết bảng nào cần query và nghiệp vụ riêng của từng ngành.

Mapping ví dụ:

```text
Clinic:
  services -> service_catalog
  staff -> doctors/staff
  availability -> doctor_schedules + appointments

Hotel:
  services -> room types / amenities
  staff -> reception / housekeeping
  availability -> room inventory + bookings

Restaurant:
  services -> menu items
  staff -> waiters / managers
  availability -> tables + reservations

School:
  services -> programs / courses
  staff -> teachers / admin
  availability -> class schedules
```

## 6. Kết luận kiểm tra

Đã đáp ứng:

- Có Postgres database.
- Có `robo_raw` đủ 56 bảng từ Excel.
- Có `robo_app` view sạch cho chatbot.
- Có hướng hybrid SQL + RAG.
- Có roadmap scale đa lĩnh vực.
- Có LLM provider OpenAI-compatible trong flow, mặc định tắt.
- Có LLM provider Ollama local trong flow để parse intent/entities.
- Có kế hoạch phân quyền trong `docs/AUTHORIZATION_PLAN.md`.

Đã có thêm:

- Backend API `/ask`.
- Frontend chatbot web tách riêng.
- AI Agent Orchestrator trong code.
- LLM client abstraction.
- LLM intent parser OpenAI-compatible.
- Decision router.
- Policy guard.
- Tool registry.
- Domain adapter `clinic`.
- Auth context, permission matrix và audit logger skeleton.
- Auth password/token MVP bằng `/auth/login`, `/auth/me`, bearer token cho `/ask`; request `auth` mock vẫn giữ để test/backward compatibility.
- RAG vector bằng Qdrant local mode, quản lý nguồn qua `scripts/rag_documents.py`.
- Keyword/fuzzy RAG fallback nếu Qdrant chưa có index hoặc lỗi.
- RAG loại topic `overview`, `roles` khỏi retrieval để tránh dùng tài liệu platform/permission làm context trả lời bệnh nhân.
- Cấu hình local LLM bằng Ollama `qwen2.5:3b`.
- Grounded LLM response generator cho `knowledge_search`.
- Ollama local formatter cho SQL/Auth answers sau khi đã truy xuất dữ liệu và qua policy.

Chưa có và cần làm tiếp:

- Domain adapter cho `hotel`, `restaurant`, `school`.
- OTP/refresh token/account chính thức.
- Audit log ghi xuống database.

Kết luận: project hiện tại **đã có nền tảng dữ liệu + backend core + UI chatbot web + LLM intent parser có fallback + Qdrant vector RAG + auth password/token MVP**. MVP đã được lưu ở branch `mvp-v1` và tài liệu snapshot nằm trong `docs/mvp/`. Bước tiếp theo là phase productization theo bộ tài liệu:

- `docs/productization/PLAN.md`
- `docs/productization/ROADMAP.md`
- `docs/productization/AUTH_PLAN.md`
- `docs/productization/DATA_PLAN.md`
- `docs/productization/RAG_PLAN.md`
- `docs/productization/AUDIT_DEPLOYMENT_TEST_PLAN.md`
