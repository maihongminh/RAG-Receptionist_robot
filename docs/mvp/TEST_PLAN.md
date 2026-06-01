# MVP test plan

Tài liệu này gom các test smoke thủ công cho MVP.

## Chạy backend/frontend

Backend:

```bash
cd /home/minhmh/tool/robo/backend
./.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd /home/minhmh/tool/robo/frontend
python3 -m http.server 5173
```

Mở:

```text
http://localhost:5173
```

## Automated checks

Backend tests:

```bash
cd /home/minhmh/tool/robo/backend
./.venv/bin/python -m pytest
```

MVP scenario:

```bash
cd /home/minhmh/tool/robo
./backend/.venv/bin/python scripts/test_mvp_chatbot.py --llm-provider none
```

Frontend JS syntax:

```bash
cd /home/minhmh/tool/robo
node --check frontend/app.js
```

## Guest/public tests

Không login hoặc bấm `Vào như guest`.

Hỏi:

```text
Địa chỉ phòng khám ở đâu?
Phòng khám mở cửa lúc mấy giờ?
CT Brain without contrast giá bao nhiêu?
danh sách xét nghiệm
các dịch vụ hiện có
Quy trình check-in bệnh nhân như thế nào?
Quy trình trả kết quả như thế nào?
Tôi đau ngực, nên khám gì?
```

Kỳ vọng:

- public info trả lời từ SQL/RAG;
- câu triệu chứng không chẩn đoán;
- câu private bị yêu cầu đăng nhập.

## Patient tests

Login:

```text
patient.demo@robo.local / demo123
```

Hỏi:

```text
Tôi có lịch hẹn nào không?
Tôi muốn nhận kết quả xét nghiệm
```

Kỳ vọng:

- chỉ thấy dữ liệu theo `patient_id` của patient đang login.

## Doctor tests

Login:

```text
doctor@clinic.local / demo123
```

Hỏi:

```text
Tôi có lịch hẹn nào không?
Hôm nay bác sĩ có khám không?
```

Kỳ vọng:

- lịch hẹn trả theo `doctor_id`;
- câu trả lời lịch hẹn của bác sĩ nên nêu bệnh nhân, không nói nhầm doctor là patient.

## Receptionist tests

Login:

```text
receptionist@clinic.local / demo123
```

Hỏi:

```text
Tôi có lịch hẹn nào không?
Tôi muốn nhận kết quả xét nghiệm
Địa chỉ phòng khám ở đâu?
```

Kỳ vọng:

- dữ liệu private giới hạn theo `clinic_id`.

## Clinic admin tests

Login:

```text
admin@clinic.local / demo123
```

Hỏi:

```text
Tôi có lịch hẹn nào không?
Tôi muốn nhận kết quả xét nghiệm
các dịch vụ hiện có
```

Kỳ vọng:

- dữ liệu private giới hạn theo `clinic_id`;
- public/service flow vẫn hoạt động.

## Follow-up/session tests

Hỏi liên tục:

```text
các dịch vụ hiện có
xem thêm
xem chi tiết nhóm 8
```

Hoặc:

```text
danh sách xét nghiệm
các nhóm còn lại là nhóm nào
xem chi tiết nhóm 35
```

Kỳ vọng:

- backend dùng `session_id` để giữ context ngắn;
- `xem thêm` không quay lại trang đầu nếu context còn.

