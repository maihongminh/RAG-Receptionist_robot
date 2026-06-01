# MVP test accounts

Các account này được seed trong:

```text
db/seed_mvp_demo.sql
```

Mật khẩu chung:

```text
demo123
```

## Patient

```text
email: patient.demo@robo.local
role: patient
patient_id: d7402d44-a12f-420b-93b9-90372a3b2e6e
clinic_id: d5ac6269-d8cf-4821-ac8b-a6341e68987b
name: Trần Thị Bình
```

## Doctor

```text
email: doctor@clinic.local
role: doctor
doctor_id: d1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4
clinic_id: d5ac6269-d8cf-4821-ac8b-a6341e68987b
name: Dr. MVP Demo
```

## Receptionist

```text
email: receptionist@clinic.local
role: receptionist
staff_id: cad02e6c-fb13-4f5f-869d-a97d07491c26
clinic_id: d5ac6269-d8cf-4821-ac8b-a6341e68987b
name: Receptionist Le Minh C
```

## Clinic admin

```text
email: admin@clinic.local
role: clinic_admin
staff_id: 9c3b4180-18d9-46c2-9059-aaaa40d73118
clinic_id: d5ac6269-d8cf-4821-ac8b-a6341e68987b
name: Clinic Admin Nguyen Van F
```

## Curl login mẫu

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient.demo@robo.local","password":"demo123"}'
```

Response trả `access_token`.

```bash
TOKEN="paste_access_token_here"

curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

