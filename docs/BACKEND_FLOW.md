# Backend flow và cấu trúc project

Tài liệu này giải thích backend đang hoạt động như thế nào khi người dùng hỏi một câu hỏi, các bước xử lý trong backend, và chức năng của từng folder/file chính trong project.

## 1. Mục tiêu backend hiện tại

Backend hiện tại là MVP hỏi đáp cơ bản cho robot lễ tân.

Nó đã được thiết kế theo hướng có thể mở rộng:

```text
Frontend chatbot
  -> Backend API /ask
  -> AI Agent Orchestrator
  -> LLM Intent Parser hoặc rule fallback
  -> Decision Router
  -> Tool Registry
  -> Domain Adapter
  -> SQL/RAG/Auth tools
  -> Grounded/Local LLM Response Generator nếu có context
  -> Response Generator template fallback
```

Hiện tại:

- Đã có backend API `/ask`.
- Đã có frontend chatbot web.
- Đã query được Postgres schema `robo_app`.
- Đã có domain đầu tiên là `clinic`.
- Đã có rule-based router.
- Đã có RAG vector bằng Qdrant local mode, quản lý nguồn qua `scripts/rag_documents.py`.
- Keyword/fuzzy search vẫn được giữ làm fallback nếu Qdrant chưa có index hoặc lỗi.
- Đã có LLM provider OpenAI-compatible và Ollama local để parse intent/entities.
- LLM hiện dùng ở đầu flow để hiểu câu hỏi.
- LLM cuối flow đã bật:
  - `knowledge_search`: grounded answer từ RAG context.
  - SQL/Auth answers: local formatter chỉ chạy với Ollama để viết lại dữ liệu đã truy xuất cho dễ đọc.
- Đã có auth/RBAC/policy guard.
- Đã có auth password/token MVP qua `/auth/login`, `/auth/me`, và `/ask` đọc `Authorization: Bearer <token>`.
- `auth` mock trong request vẫn giữ để test/backward compatibility.
- Chưa có OTP/refresh token/account production.

## 2. Flow tổng quát khi người dùng hỏi

Ví dụ người dùng hỏi trên UI:

```text
CT Brain without contrast giá bao nhiêu?
```

Luồng đi qua hệ thống:

```text
1. frontend/app.js
   Người dùng nhập câu hỏi và bấm Gửi.

2. POST http://localhost:8000/ask
   Frontend gửi JSON request sang backend.

3. backend/app/api/ask.py
   Endpoint /ask nhận request và gọi Orchestrator.

4. backend/app/core/orchestrator.py
   Điều phối toàn bộ luồng xử lý.

5. backend/app/llm/llm_client.py
   Thử gọi LLM parser nếu đã cấu hình LLM.
   Nếu LLM_PROVIDER=none hoặc provider lỗi, trả None để fallback.

6. backend/app/core/rule_intent_parser.py
   Rule fallback phân loại intent và trích xuất tham số khi LLM tắt/lỗi.

7. backend/app/core/decision_router.py
   Quyết định câu hỏi đi nhánh SQL, RAG, Auth hay None.

8. backend/app/auth/policy_guard.py
   Kiểm tra role/auth context có được dùng tool hoặc xem dữ liệu không.

9. backend/app/core/tool_registry.py
   Chọn tool phù hợp dựa trên intent và domain.

10. backend/app/domains/clinic/adapter.py
   Domain adapter của clinic nhận lệnh chung từ core.

11. backend/app/domains/clinic/sql_tools.py
    Query Postgres schema robo_app.

12. backend/app/rag/grounded_response_generator.py
    Nhận question + intent + tool result + sources/context.
    Với knowledge_search, dùng LLM để diễn đạt tự nhiên hơn nhưng chỉ dựa trên dữ liệu đã truy xuất.
    Nếu context không đủ, phải trả lời không tìm thấy dữ liệu phù hợp.

13. backend/app/core/response_generator.py
    Tạo câu trả lời template nếu grounded LLM không áp dụng hoặc bị lỗi.

14. backend/app/auth/audit_logger.py
    Ghi audit log mức MVP ra application logger.

15. Response JSON trả về frontend.

16. frontend/app.js
    Hiển thị answer, intent, source, confidence và data debug.
```

## 3. Request và response

Frontend gửi request:

```json
{
  "question": "CT Brain without contrast giá bao nhiêu?",
  "domain": "clinic"
}
```

Backend trả response:

```json
{
  "question": "CT Brain without contrast giá bao nhiêu?",
  "answer": "Dịch vụ CT Brain without contrast có giá 120000 USD.",
  "domain": "clinic",
  "intent": "service_price",
  "confidence": 1.0,
  "parser_source": "llm",
  "answer_source": "template",
  "sources": ["robo_app.services"],
  "data": [
    {
      "code": "CT001",
      "name": "CT Brain without contrast",
      "price_amount": "120000",
      "currency_code": "USD"
    }
  ],
  "requires_auth": false
}
```

Ý nghĩa:

- `answer`: câu trả lời hiển thị cho người dùng.
- `domain`: domain đang xử lý, hiện là `clinic`.
- `intent`: ý định đã phân loại.
- `confidence`: độ tự tin.
- `parser_source`: `llm` nếu LLM parse intent thành công, `rule` nếu dùng rule fallback.
- `answer_source`: `llm_grounded` nếu LLM diễn đạt từ RAG context, `llm_formatted` nếu Ollama local format dữ liệu SQL/Auth, `template` nếu dùng template fallback.
- `sources`: nguồn dữ liệu đã dùng.
- `data`: dữ liệu debug/tracing trả về UI.
- `requires_auth`: câu hỏi có cần xác thực không.

## 3.1. Quy ước hai vai trò LLM

Project dùng LLM theo 2 vai trò tách biệt:

```text
1. LLM Intent Parser
   User question -> Intent JSON/entities/confidence

2. Grounded/Formatted LLM Response Generator
   User question + SQL/RAG/Auth result + sources -> natural answer
```

Vai trò 1 đã có trong code:

- file chính: `backend/app/llm/llm_client.py`
- provider: `ollama`, `openai/openai_compatible`
- fallback: `RuleIntentParser`
- output được backend chuẩn hóa lại `data_source/requires_auth` để route SQL/RAG/Auth không phụ thuộc hoàn toàn vào model.

Vai trò 2 hiện có 2 chế độ:

- `knowledge_search`: grounded answer, có thể dùng provider LLM đang cấu hình.
- SQL/Auth formatter: chỉ bật với `LLM_PROVIDER=ollama`, để dữ liệu cá nhân không bị gửi ra provider cloud.

Nguyên tắc bắt buộc:

- LLM không được tự tạo giá, lịch, địa chỉ, kết quả cá nhân.
- LLM chỉ viết lại từ `ToolResult.rows`, RAG chunks, và `sources`.
- SQL vẫn là nguồn sự thật cho giá dịch vụ, lịch bác sĩ, thông tin cơ sở, lịch hẹn.
- Vector RAG chỉ dùng cho hướng dẫn/quy trình/FAQ/nội dung mô tả.
- Nếu dữ liệu truy xuất không đủ, answer phải nói không tìm thấy trong dữ liệu hiện có.
- Dữ liệu cá nhân vẫn phải qua `PolicyGuard` trước khi đưa vào LLM response generator.

## 4. Các intent hiện có

File định nghĩa: `backend/app/core/schemas.py`

Các intent hiện tại:

```text
greeting
general_info
service_price
doctor_schedule
knowledge_search
appointment_booking
appointment_lookup
personal_data
out_of_scope
```

Ý nghĩa:

- `greeting`: người dùng chào hoặc hỏi bot làm được gì.
- `general_info`: hỏi thông tin chung như địa chỉ, phone, email, giờ làm việc.
- `service_price`: hỏi dịch vụ hoặc giá dịch vụ.
- `doctor_schedule`: hỏi lịch bác sĩ.
- `knowledge_search`: hỏi quy trình/hướng dẫn/FAQ, dùng Qdrant vector RAG trước và keyword fallback sau.
- `appointment_booking`: yêu cầu đặt lịch/tạo lịch hẹn, hiện trả placeholder vì chưa bật booking tự động.
- `appointment_lookup`: tra lịch hẹn sau khi có auth context hợp lệ.
- `personal_data`: dữ liệu cá nhân, phải xác thực trước; MVP hiện tra được lịch hẹn theo scope.
- `out_of_scope`: câu hỏi ngoài phạm vi hiện tại.

## 5. Flow chi tiết theo từng loại câu hỏi

### 5.1. Người dùng chào bot

Câu hỏi:

```text
xin chào
```

Flow:

```text
frontend/app.js
  -> POST /ask
  -> ask.py
  -> orchestrator.py
  -> llm_client.py parse bằng LLM nếu bật, hoặc trả None
  -> rule_intent_parser.py
       intent = greeting
       data_source = none
  -> orchestrator.py
  -> tool_registry.py
       tool = core.greeting
  -> response_generator.py
       trả lời giới thiệu bot và chức năng hiện có
  -> frontend hiển thị answer
```

Kết quả:

```text
Xin chào, tôi là robot lễ tân. Hiện tôi có thể hỗ trợ tra cứu thông tin phòng khám, địa chỉ, số điện thoại, giờ làm việc, giá dịch vụ và lịch bác sĩ...
```

### 5.2. Hỏi thông tin chung

Câu hỏi:

```text
Địa chỉ phòng khám ở đâu?
```

Flow:

```text
rule_intent_parser.py
  -> intent = general_info
  -> data_source = sql

decision_router.py
  -> route = sql

tool_registry.py
  -> adapter.get_public_profile()

clinic/adapter.py
  -> sql_tools.get_public_profile()

clinic/sql_tools.py
  -> query robo_app.clinics
  -> join robo_app.clinic_settings

response_generator.py
  -> format tên, địa chỉ, phone, email, giờ làm việc
```

SQL nguồn:

```text
robo_app.clinics
robo_app.clinic_settings
```

### 5.3. Hỏi giá dịch vụ

Câu hỏi:

```text
CT Brain without contrast giá bao nhiêu?
```

Flow:

```text
rule_intent_parser.py
  -> intent = service_price
  -> entities.service_query = "CT Brain without contrast"
  -> data_source = sql

decision_router.py
  -> route = sql

tool_registry.py
  -> adapter.list_services(entities)

clinic/adapter.py
  -> sql_tools.search_services(service_query)

clinic/sql_tools.py
  -> query robo_app.services
  -> rank kết quả bằng text matching
  -> trả top 5 kết quả

response_generator.py
  -> lấy kết quả đầu tiên
  -> trả câu "Dịch vụ ... có giá ..."
```

SQL nguồn:

```text
robo_app.services
```

### 5.4. Hỏi lịch bác sĩ

Câu hỏi:

```text
Hôm nay bác sĩ SUON SAVUTH có khám không?
```

Flow:

```text
rule_intent_parser.py
  -> intent = doctor_schedule
  -> entities.doctor_query = "SUON SAVUTH"
  -> entities.date = "today"
  -> entities.weekday = ngày hiện tại theo Python
  -> data_source = sql

decision_router.py
  -> route = sql

tool_registry.py
  -> adapter.check_availability(entities)

clinic/adapter.py
  -> sql_tools.search_doctor_schedules(doctor_query, weekday)

clinic/sql_tools.py
  -> query robo_app.doctor_schedules
  -> nếu có weekday thì lọc theo thứ
  -> rank theo doctor_name

response_generator.py
  -> format lịch bác sĩ, giờ bắt đầu/kết thúc, phòng
```

SQL nguồn:

```text
robo_app.doctor_schedules
```

### 5.5. Hỏi dữ liệu cá nhân

Câu hỏi:

```text
Tôi có lịch hẹn nào không?
```

Flow:

```text
rule_intent_parser.py
  -> intent = personal_data
  -> requires_auth = true
  -> data_source = auth

decision_router.py
  -> route = auth

orchestrator.py
  -> nếu chưa có auth hợp lệ: PolicyGuard chặn trước tool
  -> nếu có auth hợp lệ: ToolRegistry gọi clinic.lookup_private_data

response_generator.py
  -> nếu bị chặn: yêu cầu xác thực
  -> nếu được phép: format lịch hẹn đã lọc theo scope
```

MVP hiện có password login cơ bản. Frontend có màn hình đăng nhập riêng để gọi `/auth/login` bằng `email/password`, nhận bearer token rồi gửi token vào `/ask`. Backend sinh auth context từ `robo_app.auth_accounts` trong phạm vi:

```text
patient      -> patient_id
doctor       -> doctor_id
receptionist -> clinic_id
clinic_admin -> clinic_id
```

Tài khoản demo dùng chung mật khẩu `demo123`:

```text
patient.demo@robo.local
doctor@clinic.local
receptionist@clinic.local
admin@clinic.local
```

## 6. Backend đang xử lý những gì?

Hiện tại backend có các xử lý:

```text
1. Validate request bằng Pydantic.
2. Chọn domain, mặc định là clinic.
3. Thử parse intent/entities bằng LLM client nếu `LLM_PROVIDER` được bật.
4. Nếu chưa bật LLM, thiếu key, provider lỗi hoặc response sai schema, dùng rule parser.
5. Trích xuất entity đơn giản như service_query, doctor_query, weekday.
6. Quyết định route: sql, auth, none.
7. Gọi tool qua tool registry.
8. Gọi domain adapter clinic.
9. Query Postgres schema robo_app.
10. Rank kết quả gần đúng bằng text matching.
11. Tạo câu trả lời template fallback.
12. Thử dùng Grounded/Local LLM Response Generator để diễn đạt từ context.
    - `knowledge_search`: grounded answer từ RAG context.
    - SQL/Auth: formatter chỉ chạy với Ollama local.
13. Nếu LLM generation tắt/lỗi/rỗng, dùng template fallback.
14. Trả JSON có answer + trace.
```

Backend chưa xử lý:

```text
1. Auth/phân quyền thật.
2. Chuyển conversation context từ in-memory sang Redis/PostgreSQL nếu cần production.
3. Mở rộng Grounded LLM Response Generator sang các intent phù hợp khác nếu cần.
4. Tạo lịch hẹn.
5. STT/TTS.
6. Domain thật ngoài clinic.
```

Kế hoạch auth/RBAC chi tiết nằm ở:

```text
docs/AUTHORIZATION_PLAN.md
```

Test tự động hiện có:

```text
backend/tests/test_rule_intent_parser.py
backend/tests/test_policy_guard.py
backend/tests/test_orchestrator.py
```

Chạy bằng:

```bash
cd /home/minhmh/tool/robo/backend
source .venv/bin/activate
pytest
```

## 7. Cây thư mục project

```text
/home/minhmh/tool/robo
├── .env.example
├── .gitignore
├── docs/
│   ├── BACKEND_FLOW.md
│   ├── DOCS_INDEX.md
│   ├── PROGRESS.md
│   ├── ROBOT_RECEPTION_ROADMAP.md
│   ├── RUNBOOK.md
│   ├── AUTHORIZATION_PLAN.md
│   └── doc_system.md
├── backend/
├── frontend/
├── db/
├── data/
├── qdrant_data/
├── scripts/
└── info_project/
```

Ý nghĩa root files:

- `.env.example`: ví dụ cấu hình môi trường cấp project.
- `.gitignore`: loại trừ `.env`, `.venv`, cache Python.
- `docs/`: chứa toàn bộ tài liệu cấp project.
- `docs/BACKEND_FLOW.md`: tài liệu này, giải thích flow backend và cấu trúc project.
- `docs/DOCS_INDEX.md`: mục lục tài liệu, task hiện tại, quy tắc cập nhật docs.
- `docs/PROGRESS.md`: ghi tiến độ hiện tại và note sau mỗi lần làm.
- `docs/ROBOT_RECEPTION_ROADMAP.md`: roadmap tổng thể.
- `docs/AUTHORIZATION_PLAN.md`: kế hoạch auth/RBAC/audit/row-level filtering.
- `docs/RUNBOOK.md`: hướng dẫn chạy backend, frontend, database.
- `docs/doc_system.md`: tài liệu hệ thống và trạng thái kỹ thuật.
- `qdrant_data/`: dữ liệu Qdrant local mode cho vector RAG, là index có thể rebuild, không commit.

## 8. Cây thư mục backend

```text
backend/
├── .env.example
├── README.md
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── db.py
    ├── api/
    │   ├── __init__.py
    │   └── ask.py
    ├── core/
    │   ├── __init__.py
    │   ├── schemas.py
    │   ├── orchestrator.py
    │   ├── rule_intent_parser.py
    │   ├── decision_router.py
    │   ├── tool_registry.py
    │   └── response_generator.py
    ├── auth/
    │   ├── __init__.py
    │   ├── auth_context.py
    │   ├── permissions.py
    │   ├── policy_guard.py
    │   └── audit_logger.py
    ├── llm/
    │   ├── __init__.py
    │   └── llm_client.py
    ├── rag/
    │   ├── __init__.py
    │   ├── grounded_response_generator.py
    │   ├── embedding_client.py
    │   ├── qdrant_store.py
    │   └── rag_config.py
    └── domains/
        ├── __init__.py
        ├── base.py
        └── clinic/
            ├── __init__.py
            ├── adapter.py
            ├── sql_tools.py
            └── prompts.py
```

Ý nghĩa:

- `backend/.env.example`: ví dụ env backend.
- `backend/README.md`: hướng dẫn riêng cho backend.
- `backend/requirements.txt`: dependency Python.
- `backend/app/main.py`: khởi tạo FastAPI, CORS, route `/health`, include `/ask`.
- `backend/app/config.py`: đọc `DATABASE_URL`, `DEFAULT_DOMAIN`, cấu hình LLM, embedding, Qdrant, API keys.
- `backend/app/db.py`: helper kết nối Postgres và chạy query.
- `backend/app/api/ask.py`: endpoint `POST /ask`.

Core:

- `schemas.py`: định nghĩa `AskRequest`, `AskResponse`, `Intent`, `ToolResult`.
- `orchestrator.py`: điều phối toàn bộ flow hỏi đáp.
- `rule_intent_parser.py`: parser bằng keyword hiện tại.
- `decision_router.py`: quyết định route `sql`, `rag`, `auth`, `none`.
- `tool_registry.py`: gọi tool phù hợp theo intent/domain.
- `response_generator.py`: tạo câu trả lời cuối bằng template; là fallback khi grounded LLM không chạy được.

Auth:

- `auth_context.py`: resolve auth context từ request, hiện guest nếu chưa có auth.
- `permissions.py`: permission matrix theo role/tool.
- `policy_guard.py`: chặn hoặc cho phép intent/tool trước khi truy vấn dữ liệu.
- `audit_logger.py`: audit skeleton, hiện log ra application logger.

LLM:

- `llm_client.py`: gọi LLM OpenAI-compatible hoặc Ollama local để parse `Intent`; hỗ trợ grounded answer và Ollama local formatter; fallback về rule/template nếu tắt/lỗi.

RAG:

- `grounded_response_generator.py`: tạo context từ `ToolResult.rows` và gọi LLM để diễn đạt câu trả lời grounded/formatted.
- `embedding_client.py`: gọi Ollama embedding API với model `nomic-embed-text` để tạo vector cho RAG.
- `qdrant_store.py`: wrapper Qdrant local/server, tạo collection, upsert chunks, search vector.
- `rag_config.py`: gom tham số retrieval như `RAG_TOP_K`, `RAG_MIN_SCORE`, keyword fallback limit và confidence mặc định.

Domains:

- `domains/base.py`: interface chung cho domain adapter.
- `domains/clinic/adapter.py`: adapter bệnh viện/phòng khám.
- `domains/clinic/sql_tools.py`: query SQL vào `robo_app`; riêng `knowledge_search` ưu tiên Qdrant vector rồi fallback keyword/fuzzy.
- `domains/clinic/prompts.py`: prompt intent parser dành cho LLM domain clinic.

Tests:

```text
backend/tests/
├── test_clinic_sql_tools.py
├── test_llm_client.py
├── test_orchestrator.py
├── test_policy_guard.py
└── test_rule_intent_parser.py
```

Ý nghĩa:

- `test_clinic_sql_tools.py`: kiểm tra `knowledge_search` ưu tiên Qdrant và fallback keyword.
- `test_llm_client.py`: kiểm tra OpenAI-compatible/Ollama parser và fallback.
- `test_orchestrator.py`: kiểm tra flow tổng hợp, policy, LLM normalization.
- `test_policy_guard.py`: kiểm tra RBAC/policy guard.
- `test_rule_intent_parser.py`: kiểm tra rule intent parser.

## 9. Cây thư mục frontend

```text
frontend/
├── README.md
├── index.html
├── styles.css
└── app.js
```

Ý nghĩa:

- `frontend/index.html`: markup màn đăng nhập, UI chatbot và trace panel.
- `frontend/styles.css`: style màn đăng nhập, chatbot và trace panel.
- `frontend/app.js`: gọi `/auth/login`, gửi bearer token vào `/ask`, render chat và trace panel.
- `frontend/README.md`: hướng dẫn chạy frontend.

Frontend chạy tách khỏi backend:

```text
frontend: http://localhost:5173
backend:  http://localhost:8000
```

## 10. Cây thư mục database

```text
db/
├── README.md
├── schema.sql
├── load.sql
├── import_all.sql
├── app_views.sql
└── manifest.json
```

Ý nghĩa:

- `db/schema.sql`: tạo schema `robo_raw` và 56 bảng raw.
- `db/load.sql`: load CSV vào Postgres bằng `\copy`.
- `db/import_all.sql`: chạy cả schema và load.
- `db/app_views.sql`: tạo schema view `robo_app`.
- `db/manifest.json`: mapping Excel sheet -> Postgres table/columns.
- `db/README.md`: giải thích database layer.

## 11. Cây thư mục data

```text
data/
└── postgres_csv/
    ├── clinics.csv
    ├── service_catalog.csv
    ├── staff.csv
    ├── doctor_schedules.csv
    └── ...
```

Ý nghĩa:

- Chứa CSV sinh từ file Excel.
- Có 56 CSV tương ứng 56 sheet/bảng.
- Dùng bởi `db/load.sql` để import vào Postgres.

## 12. Cây thư mục scripts

```text
scripts/
├── build_qdrant_index.py
├── export_excel_to_postgres.py
├── import_to_postgres.sh
├── setup_local_postgres.sh
└── apply_app_views.sh
```

Ý nghĩa:

- `export_excel_to_postgres.py`: đọc Excel, sinh CSV, `schema.sql`, `load.sql`, `manifest.json`.
- `rag_documents.py`: registry các app view/bảng được phép đưa vào RAG.
- `build_qdrant_index.py`: đọc documents từ `scripts/rag_documents.py`, gọi Ollama embedding, build Qdrant collection `clinic_knowledge`.
- `import_to_postgres.sh`: import vào Postgres qua `DATABASE_URL`.
- `setup_local_postgres.sh`: tạo local role/database Postgres.
- `apply_app_views.sh`: chạy `db/app_views.sql` để tạo lại `robo_app`.

## 12.1. Cây thư mục Qdrant local

```text
qdrant_data/
├── .lock
├── meta.json
└── ...
```

Ý nghĩa:

- Đây là storage nội bộ của Qdrant local mode.
- Không phải nguồn dữ liệu thật; nguồn thật vẫn là Postgres.
- Có thể xóa và rebuild bằng `backend/.venv/bin/python scripts/build_qdrant_index.py`.
- Nếu rebuild bị lock, dừng backend trước rồi chạy lại script.

## 13. Cây thư mục info_project

```text
info_project/
├── Robot_Le_Tan_Chat_Flow.png
├── clinic_full_export.xlsx
└── idea.txt
```

Ý nghĩa:

- `Robot_Le_Tan_Chat_Flow.png`: flow ý tưởng ban đầu.
- `clinic_full_export.xlsx`: dữ liệu export gốc.
- `idea.txt`: mô tả ý tưởng ban đầu.

## 14. Điểm mở rộng sau này

### LLM provider

File cần sửa chính:

```text
backend/app/llm/llm_client.py
```

Hiện đã có:

```text
question -> LLM -> Intent JSON -> orchestrator
```

LLM chỉ parse intent/entities. Provider hiện có:

```text
openai / openai_compatible
ollama
```

Sau đó core vẫn chạy:

```text
Intent -> PolicyGuard -> ToolRegistry -> SQL/RAG/Auth -> ResponseGenerator
```

### Grounded/Formatted Response Generation

File dự kiến thêm hoặc mở rộng:

```text
backend/app/core/response_generator.py
backend/app/rag/grounded_response_generator.py
backend/app/llm/llm_client.py
```

Luồng mục tiêu:

```text
Intent -> PolicyGuard -> ToolRegistry -> SQL/RAG/Auth
  -> ToolResult/context/sources
  -> Grounded/Local LLM Response Generator
  -> answer
```

Ràng buộc prompt bắt buộc:

```text
Chỉ trả lời dựa trên context đã cung cấp.
Không tự suy luận giá, lịch, địa chỉ, dữ liệu cá nhân.
Với dữ liệu cá nhân, chỉ dùng Ollama local formatter sau khi PolicyGuard đã cho phép.
Nếu context không chứa câu trả lời, nói không tìm thấy trong dữ liệu hiện có.
Giữ câu trả lời ngắn, rõ, đúng vai trò robot lễ tân.
```

Trong UI trace vẫn phải hiển thị:

```text
parser_source: llm/rule
sources: bảng SQL hoặc RAG chunks
data: dữ liệu truy xuất
```

Nếu muốn thêm provider khác sau này, giữ nguyên contract `Intent` và thêm provider branch trong `llm_client.py`.

### Thêm RAG

Flow RAG hiện tại:

```text
robo_raw.admin_help_templates
  -> robo_app.knowledge_articles
  -> scripts/rag_documents.py
  -> scripts/build_qdrant_index.py
  -> Ollama embedding model nomic-embed-text
  -> Qdrant local qdrant_data / collection clinic_knowledge
  -> backend knowledge_search
```

Source đang được vector hóa:

```text
scripts/build_qdrant_index.py
  load_rag_documents() từ scripts/rag_documents.py
```

Retrieval hiện loại topic theo cấu hình:

```text
RAG_EXCLUDED_TOPICS=overview,roles
```

Các topic này là tài liệu platform/system overview hoặc phân quyền, không phải hướng dẫn trả lời bệnh nhân. Bộ lọc được áp dụng ở cả Qdrant vector result và SQL keyword fallback. Khi đổi cấu hình hoặc dữ liệu, rebuild Qdrant index.

Flow RAG khi có nhiều nguồn:

```text
raw/app tables
  -> scripts/rag_documents.py
       source_table
       source_id
       title
       content
       access_level
       updated_at
  -> scripts/build_qdrant_index.py
  -> Qdrant collection clinic_knowledge
```

Quy tắc thêm nguồn mới:

```text
Thêm nguồn hợp lệ vào scripts/rag_documents.py.
Nguồn nên tham chiếu các app view sạch do db/app_views.sql tạo ra.
Chỉ đưa dữ liệu text dài như FAQ, hướng dẫn, quy trình, policy, mô tả dịch vụ.
Không đưa bảng structured như giá dịch vụ, lịch bác sĩ, lịch hẹn, bệnh nhân.
```

### Thêm domain mới

Ví dụ hotel:

```text
backend/app/domains/hotel/
├── __init__.py
├── adapter.py
├── sql_tools.py
└── prompts.py
```

Sau đó đăng ký trong:

```text
backend/app/api/ask.py
```

Core vẫn giữ nguyên.

## 15. Kết luận

Backend hiện tại chưa phải AI đầy đủ. Nó là khung backend có kiến trúc đúng:

```text
LLM intent parser + rule fallback + SQL + Qdrant vector RAG hiện tại
Grounded response generation cho knowledge_search hiện tại
Auth thật + multi-domain sau này
```

Điểm quan trọng là core đã được tách khỏi domain clinic. Vì vậy khi thêm LLM, RAG hoặc các domain như khách sạn, nhà hàng, trường học, mình không phải viết lại toàn bộ backend.
