# Productization auth plan

MVP hiện có:

- `POST /auth/login` bằng email/password.
- Password hash PBKDF2-SHA256.
- Bearer token HMAC local.
- Account demo đã bắt đầu được tách sang schema `robo_auth`.
- `auth` mock trong request đã chuyển thành dev-only path và mặc định tắt.

P1 foundation đã bắt đầu với:

- `db/auth/schema.sql`;
- `db/auth/seed_demo.sql`;
- `scripts/apply_auth_schema.sh`;
- backend login đọc `robo_auth.accounts/account_roles/account_identities`.

Mục tiêu productization là biến lớp này thành auth/account chính thức.

## 1. Account model mục tiêu

Đề xuất tách account production khỏi `robo_app` view layer.

Schema gợi ý:

```text
robo_auth.accounts
  id
  email
  phone
  password_hash
  password_algorithm
  password_updated_at
  status
  failed_login_count
  locked_until
  last_login_at
  created_at
  updated_at

robo_auth.account_identities
  id
  account_id
  profile_id
  patient_id
  staff_id
  clinic_id
  organization_id
  identity_type
  is_primary
  created_at
  updated_at

robo_auth.account_roles
  id
  account_id
  role
  clinic_id
  organization_id
  is_active
  created_at
  updated_at

robo_auth.sessions
  id
  account_id
  refresh_token_hash
  user_agent
  ip_address
  expires_at
  revoked_at
  created_at
  updated_at
```

Không nhất thiết làm hết ngay. P1 có thể bắt đầu với `accounts`, `account_identities`, `account_roles`, `sessions`.

## 2. Liên kết với dữ liệu hiện tại

Nguồn đang có:

- `robo_raw.profiles`: email, full_name, user_id.
- `robo_raw.user_roles`: user_id, clinic_id, role.
- `robo_app.staff`: staff/doctor/receptionist/clinic_admin.
- `robo_app.patients`: patient.
- `robo_app.clinics`: clinic.

Auth context sau login cần sinh ra:

```text
role
user_id/account_id
clinic_id
patient_id nếu role patient
doctor_id nếu role doctor
staff_id nếu role nhân viên
organization_id nếu sau này cần
```

## 3. Login flow mục tiêu

```text
frontend login
  -> POST /auth/login {email, password}
  -> validate account status
  -> verify password hash
  -> resolve identities/roles
  -> create session/refresh token
  -> issue short-lived access token
  -> frontend stores access token + refresh token policy
```

Access token chỉ nên chứa thông tin tối thiểu:

```text
sub/account_id
session_id
role
clinic_id/patient_id/doctor_id/staff_id
iat/exp
```

## 4. Refresh/logout

MVP hiện chưa có refresh/logout server-side.

Productization cần:

- `POST /auth/refresh`
- `POST /auth/logout`
- revoke session bằng `sessions.revoked_at`
- logout frontend xóa local token
- khi refresh token bị revoke/expired thì bắt login lại

## 5. Password policy

Tối thiểu:

- không lưu plaintext;
- hash bằng PBKDF2-SHA256 hiện tại hoặc nâng lên Argon2/bcrypt nếu thêm dependency;
- password tối thiểu 8 ký tự cho production;
- rate limit login;
- failed_login_count + lock ngắn hạn;
- reset password/OTP ở phase sau nếu cần.

## 6. Backward compatibility

Trong khi chuyển đổi:

- backend chỉ nhận `payload.auth` nếu bật `AUTH_ALLOW_REQUEST_CONTEXT=true`;
- legacy login bằng `role + UUID` chỉ chạy nếu bật `AUTH_ALLOW_LEGACY_ROLE_LOGIN=true`;
- frontend production không gửi `payload.auth` và không login bằng UUID;
- khi test production auth, ưu tiên Bearer token.

Khi production auth ổn:

- chỉ giữ `payload.auth` trong test helper/dev-only path;
- document rõ không dùng auth mock ở production.

## 7. Test plan cho auth

Unit tests:

- hash/verify password;
- reject wrong password;
- reject inactive account;
- issue/verify access token;
- expired token;
- refresh token;
- logout revoked session.

Integration tests:

- login patient -> ask appointment -> chỉ thấy appointment của patient;
- login doctor -> ask schedule/appointment -> chỉ thấy scope doctor;
- login receptionist -> scope clinic;
- invalid token -> 401;
- guest private question -> blocked.

## 8. Rủi ro cần chú ý

- Một email có thể có nhiều role/clinic.
- Một profile có thể vừa là staff vừa là platform admin.
- Patient có thể chưa có email trong data gốc.
- Staff trong `robo_app.staff` và `profiles/user_roles` có thể chưa đồng nhất.

Giải pháp: auth production nên có bảng mapping identity riêng, không suy luận trực tiếp từ một bảng duy nhất.
