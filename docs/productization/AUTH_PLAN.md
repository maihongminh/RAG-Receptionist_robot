# Productization auth plan

MVP hiện có:

- `POST /auth/login` bằng email/password.
- Password hash PBKDF2-SHA256.
- Bearer token HMAC local.
- Account demo đã bắt đầu được tách sang schema `robo_auth`.
- Login tạo row trong `robo_auth.sessions`.
- `POST /auth/logout` revoke session bằng `revoked_at`.
- `/auth/me` và `/ask` chỉ chấp nhận token có session còn active nếu token có `session_id`.
- `POST /auth/refresh` rotate refresh token.
- `POST /auth/change-password` đổi mật khẩu cho user đã đăng nhập.
- `POST /auth/password-reset/request` và `/auth/password-reset/complete` tạo nền reset password bằng token có TTL.
- `auth` mock trong request đã chuyển thành dev-only path và mặc định tắt.

P1 foundation đã bắt đầu với:

- `db/auth/schema.sql`;
- `db/auth/seed_demo.sql`;
- `scripts/apply_auth_schema.sh`;
- backend login đọc `robo_auth.accounts/account_roles/account_identities`.
- backend tạo session DB khi login và revoke session khi logout.
- backend đã có refresh token rotation, change password, login lock/rate-limit, audit DB và password reset token foundation.

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

robo_auth.password_reset_tokens
  id
  account_id
  token_hash
  expires_at
  used_at
  created_at
```

P1 hiện đã có `accounts`, `account_identities`, `account_roles`, `sessions` và `password_reset_tokens`.

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
  -> create session in robo_auth.sessions
  -> issue access token with session_id
  -> frontend stores access token
```

Access token chỉ nên chứa thông tin tối thiểu:

```text
sub/account_id
session_id
role
clinic_id/patient_id/doctor_id/staff_id
iat/exp
```

## 4. Session/logout/refresh

Đã có session/logout server-side nền tảng:

- `POST /auth/login` tạo `robo_auth.sessions`;
- access token chứa `session_id`;
- refresh token được hash vào `sessions.refresh_token_hash`;
- `GET /auth/me` và `/ask` kiểm tra session còn active;
- `POST /auth/refresh` rotate refresh token và phát access token mới;
- `POST /auth/logout` set `sessions.revoked_at`;
- frontend logout gọi `/auth/logout` rồi xóa local token.

Refresh token hiện là opaque token, backend chỉ lưu SHA-256 hash. Refresh token cũ mất hiệu lực sau mỗi lần rotate.

## 5. Password policy

Tối thiểu:

- không lưu plaintext;
- hash bằng PBKDF2-SHA256 hiện tại hoặc nâng lên Argon2/bcrypt nếu thêm dependency;
- password tối thiểu 8 ký tự cho production;
- `POST /auth/change-password` cho user đã đăng nhập;
- đổi mật khẩu revoke các session khác của cùng account;
- `failed_login_count` tăng khi sai mật khẩu;
- account bị khóa tạm thời bằng `locked_until` khi vượt `AUTH_MAX_FAILED_LOGIN_ATTEMPTS`;
- `AUTH_LOCK_SECONDS` quy định thời gian khóa;
- rate limit login theo IP/email bằng `AUTH_LOGIN_RATE_LIMIT_ATTEMPTS` và `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS`;
- reset password token:
  - `/auth/password-reset/request` nhận email và luôn trả `ok=true` để hạn chế dò account;
  - token chỉ lưu hash trong DB;
  - token hết hạn theo `AUTH_PASSWORD_RESET_TOKEN_TTL_SECONDS`;
  - khi tạo token mới, token reset cũ chưa dùng của account đó bị vô hiệu hóa;
  - `/auth/password-reset/complete` đổi password, clear lock/counter và revoke toàn bộ session;
  - local/dev có thể bật `AUTH_PASSWORD_RESET_EXPOSE_TOKEN=true` để hiện token trên UI khi test;
  - email/SMS/OTP delivery thật chưa gắn provider, đây là điểm tích hợp tiếp theo.

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
- change password with current password;
- issue/verify access token;
- issue/rotate refresh token;
- expired token;
- refresh token;
- logout revoked session.
- request password reset does not expose token by default;
- complete password reset rejects invalid/expired token;
- complete password reset revokes sessions.

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
