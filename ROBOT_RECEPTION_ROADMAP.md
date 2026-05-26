# Robot lễ tân - định hướng project

## 1. Project hiện tại là gì?

Mục tiêu hiện tại là xây dựng một robot lễ tân có thể nghe câu hỏi của khách hoặc bệnh nhân, truy xuất dữ liệu của đơn vị, rồi trả lời lại bằng văn bản hoặc giọng nói.

Thư mục hiện có:

- `idea.txt`: mô tả ý tưởng tổng quan.
- `Robot_Le_Tan_Chat_Flow.png`: flow từ Speech-to-Text -> LLM/router -> DB/API -> response -> Text-to-Speech.
- `clinic_full_export.xlsx`: dữ liệu export từ hệ thống phòng khám/bệnh viện.

Kết luận: thư mục này chưa phải là code project. Đây đang là bộ artifact để thiết kế MVP.

## 2. Hướng kiến trúc nên đi

Không nên xây hệ thống chỉ dành riêng cho bệnh viện. Nên tách thành 2 lớp:

1. Core AI Reception Engine
   - Nhận câu hỏi.
   - Phân loại ý định của người hỏi.
   - Lấy dữ liệu từ knowledge base hoặc database/API.
   - Tạo câu trả lời ngắn gọn, đúng ngữ cảnh, đúng ngôn ngữ.
   - Khi dùng LLM để diễn đạt, câu trả lời phải grounded theo dữ liệu đã truy xuất.
   - Kiểm soát bảo mật và giới hạn câu trả lời.

2. Domain Adapter
   - Adapter cho bệnh viện/phòng khám.
   - Adapter cho nhà hàng.
   - Adapter cho khách sạn.
   - Adapter cho trường học.

Lý do: sau này nếu đổi từ bệnh viện sang nhà hàng, khách sạn hoặc trường học thì không phải viết lại toàn bộ AI core. Mình chỉ cần thêm adapter và mapping schema dữ liệu cho từng ngành.

## 3. Phân loại câu hỏi nên hỗ trợ

Nên chia câu hỏi thành 4 nhóm:

1. Thông tin chung
   - Địa chỉ, số điện thoại, giờ làm việc, khoa/phòng, quy trình tiếp nhận.
   - Nguồn dữ liệu: Vector DB hoặc knowledge base.

2. Dữ liệu có cấu trúc
   - Bác sĩ nào làm hôm nay?
   - Giá dịch vụ X bao nhiêu?
   - Phòng nào ở tầng mấy?
   - Lịch khám còn slot nào?
   - Nguồn dữ liệu: SQL/API.

3. Dữ liệu cá nhân
   - Lịch hẹn của tôi?
   - Kết quả xét nghiệm của tôi?
   - Hồ sơ bệnh án của tôi?
   - Bắt buộc xác thực bằng số điện thoại/CCCD/OTP/QR trước khi trả lời.

4. Ngoài phạm vi
   - Tư vấn chẩn đoán/y khoa nhạy cảm.
   - Yêu cầu đọc thông tin riêng tư của người khác.
   - Câu hỏi không có dữ liệu.
   - Hệ thống phải từ chối mềm và đề xuất gặp nhân viên.

## 4. MVP nên làm trước

MVP không nên bắt đầu bằng robot vật lý. Nên làm chatbot web/API trước.

MVP đề xuất:

1. Import Excel vào Postgres.
2. Tạo schema raw `robo_raw` để giữ nguyên dữ liệu gốc từ Excel.
3. Tạo schema view `robo_app` để backend/chatbot query dữ liệu đã làm sạch.
4. Tạo một backend API `/ask` nhận câu hỏi dạng text.
5. Tạo UI chatbot web chạy trên localhost để test hội thoại trước khi gắn robot.
6. Làm intent router với các intent cơ bản:
   - `general_info`
   - `doctor_schedule`
   - `service_price`
   - `appointment_lookup`
   - `personal_data`
   - `out_of_scope`
7. Tạo tool/query cho các bảng quan trọng:
   - `clinics`
   - `clinic_general_settings`
   - `rooms`
   - `staff`
   - `doctor_schedules`
   - `service_catalog`
   - `service_categories`
   - `appointments`
   - `patients`
   - `admin_help_templates`
8. Câu trả lời nên có confidence/source để biết dữ liệu lấy từ đâu.
9. Sau khi chatbot text chạy ổn định mới thêm RAG, Speech-to-Text và Text-to-Speech.

## 5. Dữ liệu trong Excel đang dùng được như thế nào?

Các bảng đang hữu ích cho robot lễ tân:

- `clinics`: tên cơ sở, địa chỉ, số điện thoại, email, timezone, tiền tệ, loại phòng khám.
- `clinic_general_settings`: giờ làm việc, giờ nghỉ trưa, slot đặt lịch, quy tắc đặt lịch.
- `rooms`: phòng, tầng, loại phòng.
- `staff`: bác sĩ/nhân viên.
- `doctor_schedules`: lịch làm việc theo thứ.
- `service_catalog`: dịch vụ, giá, thời lượng, loại dịch vụ.
- `service_categories`: nhóm dịch vụ.
- `appointments`: lịch hẹn.
- `patients`: thông tin bệnh nhân, chỉ dùng sau khi xác thực.
- `admin_help_templates`: nội dung hướng dẫn/quy trình, phù hợp để đưa vào knowledge base.

Các bảng chưa nên đưa vào MVP nếu chưa cần:

- Hồ sơ bệnh án, sinh hiệu, chi tiết kết quả: nên làm sau vì rủi ro bảo mật cao.
- Audit/security/subscription/platform admin: không liên quan trực tiếp tới robot lễ tân.
- ICD10: dữ liệu quá lớn và chưa cần cho lễ tân giai đoạn đầu.

## 6. Thiết kế module để scale nhiều ngành

Nên tạo interface chung:

```text
DomainAdapter
  - get_public_profile()
  - search_knowledge(query)
  - list_services(filters)
  - check_availability(params)
  - lookup_customer_private_data(identity, query)
  - create_request(params)
```

Hospital adapter sẽ map như sau:

- `services` -> `service_catalog`
- `staff` -> bác sĩ/nhân viên
- `availability` -> `doctor_schedules` + `appointments`
- `private_data` -> `patients`, `appointments`, `medical_records`

Hotel adapter sau này có thể map như sau:

- `services` -> loại phòng/dịch vụ.
- `staff` -> lễ tân/housekeeping.
- `availability` -> phòng trống.
- `private_data` -> booking của khách.

Core AI không cần biết domain là gì. Nó chỉ gọi adapter.

## 7. Kiến trúc kỹ thuật đề xuất

Giai đoạn prototype:

```text
Chatbot Web UI / Robot UI
  -> STT optional, thêm sau MVP text
  -> Backend API /ask
  -> LLM Intent Parser hoặc rule fallback
  -> Intent Router + PolicyGuard
  -> Tools:
       - SQL query tools
       - Vector search tools
       - Auth/identity tools
  -> Template Response Generator hiện tại
  -> Grounded LLM Response Generator sau RAG vector
  -> TTS optional, thêm sau MVP text
```

Stack gợi ý:

- Backend: Python FastAPI hoặc Node.js/NestJS.
- Database prototype: Postgres.
- Vector DB prototype: Chroma/pgvector.
- LLM: OpenAI/Gemini/Claude tùy ngân sách.
- STT/TTS: để sau MVP, có thể dùng cloud API trước.

Cấu trúc backend nên đi theo hướng core + domain adapter:

```text
backend/
  app/
    main.py
    api/
      ask.py
    core/
      orchestrator.py
      llm_client.py
      schemas.py
      decision_router.py
      tool_registry.py
      response_generator.py
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

Trong đó:

- `orchestrator.py`: tương ứng khối AI Agent Orchestrator trong flow.
- `llm_client.py`: abstraction để sau này đổi OpenAI/Gemini/Claude không ảnh hưởng core.
- `decision_router.py`: quyết định dùng SQL, RAG, auth hay từ chối.
- `tool_registry.py`: đăng ký tool theo domain.
- `response_generator.py`: tạo câu trả lời cuối.
- `domains/*`: chứa logic riêng của từng lĩnh vực.

Luồng LLM nên có fallback:

```text
Nếu có LLM API key:
  LLM parse intent + entities -> decision router -> tool -> response generator

Nếu chưa có LLM API key:
  rule-based router -> tool -> template response
```

Như vậy MVP vẫn chạy local được, nhưng sau này thêm LLM không phải viết lại core.

Sau khi có RAG vector, nên tách rõ 2 lần dùng LLM:

```text
LLM Intent Parser:
  question -> intent/entities

Grounded LLM Response Generator:
  question + SQL/RAG result + sources -> answer
```

Grounded generator không được tự trả lời từ kiến thức chung của model. Nó chỉ được diễn đạt lại dữ liệu đã truy xuất từ SQL/RAG/API. Nếu context không đủ, phải nói chưa tìm thấy dữ liệu phù hợp.

## 8. Việc cần làm tiếp theo

Thứ tự nên làm:

1. Tạo Postgres database `robo_reception`.
2. Import toàn bộ `clinic_full_export.xlsx` vào schema `robo_raw`.
3. Tạo schema view `robo_app` cho dữ liệu sạch mà chatbot được phép query.
4. Xây backend API text `/ask`.
5. Viết router intent ban đầu bằng rule + LLM structured output.
6. Viết SQL tools cho 3 use case:
   - Hỏi giờ làm việc/địa chỉ.
   - Hỏi giá dịch vụ.
   - Hỏi lịch bác sĩ.
7. Tạo UI chatbot web trên localhost để test trực tiếp.
8. Viết bộ test câu hỏi mẫu.
9. Thêm RAG cho dữ liệu hướng dẫn/quy trình/FAQ.
10. Thêm grounded LLM response generator sau retrieval.
11. Thêm authentication cho câu hỏi cá nhân.
12. Thêm authorization/policy guard/audit log theo `AUTHORIZATION_PLAN.md`.
13. Thêm STT/TTS và kết nối robot.

Trạng thái hiện tại:

- Đã tạo script import Excel sang Postgres.
- Đã import dữ liệu vào `robo_raw`.
- Đã tạo schema view `robo_app`.
- Đã scaffold backend API `/ask` theo kiến trúc core + domain adapter.
- Đã có rule fallback cho MVP khi chưa cấu hình LLM provider.
- Đã có UI chatbot web tách riêng trong `frontend/`, chạy tại `http://localhost:5173`.
- Đã có `RUNBOOK.md` hướng dẫn chạy backend + frontend + kiểm tra database.
- Đã có `PROGRESS.md` để cập nhật tiến độ sau mỗi lần làm.
- Đã có `AUTHORIZATION_PLAN.md` cho xác thực/phân quyền.
- Đã có test backend bước đầu cho intent parser, policy guard và orchestrator.
- Đã có RAG vector bằng Qdrant local mode trên `robo_app.knowledge_articles`.
- Vẫn giữ keyword/fuzzy search làm fallback khi Qdrant chưa có index hoặc lỗi.
- Đã có LLM local qua Ollama để parse intent/entities.
- Bước tiếp theo là thêm grounded LLM response generator.

## 9. Câu hỏi mẫu để test MVP

Thông tin chung:

- Bệnh viện mở cửa mấy giờ?
- Địa chỉ phòng khám ở đâu?
- Có nhận kết quả qua email không?

Dịch vụ/giá:

- CT Brain without contrast giá bao nhiêu?
- Có dịch vụ chụp CT ngực không?
- Xét nghiệm đường huyết có không?

Bác sĩ/lịch:

- Hôm nay bác sĩ SUON SAVUTH có khám không?
- Bác sĩ LEANG THY làm ở phòng nào?
- Có lịch khám buổi sáng không?

Dữ liệu cá nhân:

- Tôi có lịch hẹn nào không?
- Kết quả xét nghiệm của tôi có chưa?

Với nhóm dữ liệu cá nhân, hệ thống phải hỏi xác thực trước.

## 10. Ranh giới an toàn

Cần đặt rule ngay từ đầu:

- Không tự chẩn đoán bệnh.
- Không đọc hồ sơ cá nhân nếu chưa xác thực.
- Không trả lời nếu dữ liệu không có trong DB/knowledge base.
- Với thông tin lịch/giá/slot, ưu tiên structured DB/API hơn Vector DB.
- Nếu LLM diễn đạt câu trả lời sau retrieval, prompt phải bắt buộc chỉ dùng context đã cung cấp.
- Mỗi câu trả lời quan trọng nên nói rõ nếu cần nhân viên xác nhận thêm.

## 11. Kết luận ngắn

Hướng đúng nhất: làm "AI receptionist platform" có adapter theo từng ngành, không làm chatbot riêng cứng cho bệnh viện.

MVP nên bắt đầu bằng chatbot text trả lời 3 nhóm: thông tin chung, giá dịch vụ, lịch bác sĩ. Khi phần này chạy đúng, mới mở rộng sang dữ liệu cá nhân, đặt lịch, Speech-to-Text, Text-to-Speech và robot vật lý.
