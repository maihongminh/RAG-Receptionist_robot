Guest

Không cần nhập UUID.

xin chào
Địa chỉ phòng khám ở đâu?
Phòng khám mở cửa lúc mấy giờ?
Số điện thoại phòng khám là gì?
các dịch vụ hiện có
danh sách xét nghiệm
xem tiếp
24 nhóm khác là nhóm nào
xem chi tiết nhóm 13
xem chi tiết nhóm CT Scan
CT Brain without contrast giá bao nhiêu?
xét nghiệm TIBC có giá bao nhiêu?
tôi muốn chụp ct
Quy trình check-in bệnh nhân như thế nào?
Quy trình nhận kết quả xét nghiệm như thế nào?
tôi đau bụng nên khám gì?
tôi muốn nhận kết quả xét nghiệm
tôi có lịch hẹn nào không?
Kỳ vọng:

Public info, dịch vụ, RAG quy trình trả lời được.
Medical advice bị chặn mềm.
Kết quả xét nghiệm/lịch hẹn yêu cầu xác thực.
Patient

Role: patient
Patient UUID:

d7402d44-a12f-420b-93b9-90372a3b2e6e
Câu hỏi:

tôi có lịch hẹn nào không?
lịch khám của tôi như thế nào?
tôi muốn nhận kết quả xét nghiệm
tôi có kết quả xét nghiệm chưa?
Địa chỉ phòng khám ở đâu?
danh sách xét nghiệm
xem tiếp
xem chi tiết nhóm 13
xét nghiệm Glucose giá bao nhiêu?
Quy trình nhận kết quả xét nghiệm như thế nào?
tôi đau đầu nên xét nghiệm gì?
Kỳ vọng:

Lịch hẹn chỉ trả lịch của patient này.
Kết quả xét nghiệm chỉ trả dữ liệu của patient này.
Public/RAG/service vẫn dùng được.
Tư vấn y khoa vẫn không khuyến nghị thay bác sĩ.
Doctor

Role: doctor
Doctor UUID:

d1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4
Câu hỏi:

tôi có lịch hẹn nào không?
lịch khám của tôi như thế nào?
hôm nay tôi có lịch hẹn nào không?
Hôm nay bác sĩ có khám không?
Hôm nay bác sĩ SUON SAVUTH có khám không?
tôi muốn nhận kết quả xét nghiệm
Địa chỉ phòng khám ở đâu?
các dịch vụ hiện có
xem chi tiết nhóm CT Scan
CT Brain without contrast giá bao nhiêu?
Quy trình check-in bệnh nhân như thế nào?
Kỳ vọng:

Lịch hẹn trả theo doctor_id, có tên bệnh nhân.
Câu hỏi kết quả xét nghiệm không nên trả như patient nếu không có quyền phù hợp.
Doctor vẫn tra public/service/RAG được.
Receptionist

Role: receptionist
Clinic UUID:

d5ac6269-d8cf-4821-ac8b-a6341e68987b
Câu hỏi:

tôi có lịch hẹn nào không?
lịch khám hôm nay như thế nào?
tôi muốn nhận kết quả xét nghiệm
Địa chỉ phòng khám ở đâu?
Phòng khám mở cửa lúc mấy giờ?
danh sách xét nghiệm
xem tiếp
xem chi tiết nhóm 25
xem chi tiết nhóm CT Scan
tôi muốn chụp ct
Quy trình check-in bệnh nhân như thế nào?
Quy trình nhận kết quả xét nghiệm như thế nào?
Kỳ vọng:

Receptionist có thể xem dữ liệu trong phạm vi clinic nếu policy cho phép.
Public/service/RAG hoạt động bình thường.
Follow-up xem tiếp, xem chi tiết nhóm N hoạt động nếu hỏi sau danh sách.
Clinic Admin

Role: clinic_admin
Clinic UUID:

d5ac6269-d8cf-4821-ac8b-a6341e68987b
Câu hỏi:

tôi có lịch hẹn nào không?
lịch khám của phòng khám hôm nay như thế nào?
tôi muốn nhận kết quả xét nghiệm
Địa chỉ phòng khám ở đâu?
các dịch vụ hiện có
danh sách xét nghiệm
xem tiếp
xem chi tiết nhóm 13
xem chi tiết nhóm Laboratories
CT Brain without contrast giá bao nhiêu?
Quy trình check-in bệnh nhân như thế nào?
Quy trình trả kết quả tại phòng khám như thế nào?
Kỳ vọng:

Clinic admin là role quyền cao nhất hiện tại trong MVP.
Có thể xem dữ liệu theo clinic scope.
Service/RAG/public hoạt động.
Test Follow-Up Riêng

Chạy cùng một cuộc trò chuyện, không bấm clear giữa các câu:

danh sách xét nghiệm
xem tiếp
xem tiếp
xem chi tiết nhóm 25
Hoặc:

các dịch vụ hiện có
xem chi tiết nhóm CT Scan
CT Brain without contrast giá bao nhiêu?
Kỳ vọng:

xem tiếp giữ đúng ngữ cảnh danh sách trước.
xem chi tiết nhóm N mở đúng nhóm theo số thứ tự đã hiển thị.
Nếu bấm clear chat, session mới bắt đầu, câu follow-up mơ hồ có thể không hiểu đúng.

account:

patient.demo@robo.local
doctor@clinic.local
receptionist@clinic.local
admin@clinic.local

pass: demo123