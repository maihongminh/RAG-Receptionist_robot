-- Demo auth accounts for local/MVP testing.
-- Password for all accounts below: demo123

BEGIN;

INSERT INTO robo_auth.accounts (
  id,
  email,
  password_hash,
  password_algorithm,
  status,
  password_updated_at
)
VALUES
  (
    'auth-patient-demo-001',
    'patient.demo@robo.local',
    'pbkdf2_sha256$260000$patient-demo-salt$apjsX0RTRBwqdEdt33iocDwV1IvCZCRrHvTyd6vkeM4',
    'pbkdf2_sha256',
    'active',
    now()
  ),
  (
    'auth-doctor-demo-001',
    'doctor@clinic.local',
    'pbkdf2_sha256$260000$doctor-demo-salt$XZgOBja8alI6e497oLK98eZ_4gf5pTVsJRn4RLIvZ_Y',
    'pbkdf2_sha256',
    'active',
    now()
  ),
  (
    'auth-receptionist-demo-001',
    'receptionist@clinic.local',
    'pbkdf2_sha256$260000$receptionist-demo-salt$ngveihVdxS9QN3EfzvKxNTJH7sRQ3kx11RWIWeDvfk8',
    'pbkdf2_sha256',
    'active',
    now()
  ),
  (
    'auth-clinic-admin-demo-001',
    'admin@clinic.local',
    'pbkdf2_sha256$260000$admin-demo-salt$dlK8eenUlYi56QqyD5vXdoTdnaA_P-ghwdYg4DexZmY',
    'pbkdf2_sha256',
    'active',
    now()
  )
ON CONFLICT (email) DO UPDATE
SET
  password_hash = EXCLUDED.password_hash,
  password_algorithm = EXCLUDED.password_algorithm,
  status = EXCLUDED.status,
  password_updated_at = EXCLUDED.password_updated_at,
  updated_at = now();

INSERT INTO robo_auth.account_identities (
  id,
  account_id,
  identity_type,
  user_id,
  patient_id,
  staff_id,
  doctor_id,
  clinic_id,
  is_primary
)
VALUES
  (
    'auth-ident-patient-demo-001',
    'auth-patient-demo-001',
    'patient',
    'd7402d44-a12f-420b-93b9-90372a3b2e6e',
    'd7402d44-a12f-420b-93b9-90372a3b2e6e',
    NULL,
    NULL,
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true
  ),
  (
    'auth-ident-doctor-demo-001',
    'auth-doctor-demo-001',
    'staff',
    'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
    NULL,
    'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
    'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true
  ),
  (
    'auth-ident-receptionist-demo-001',
    'auth-receptionist-demo-001',
    'staff',
    'cad02e6c-fb13-4f5f-869d-a97d07491c26',
    NULL,
    'cad02e6c-fb13-4f5f-869d-a97d07491c26',
    NULL,
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true
  ),
  (
    'auth-ident-clinic-admin-demo-001',
    'auth-clinic-admin-demo-001',
    'staff',
    '9c3b4180-18d9-46c2-9059-aaaa40d73118',
    NULL,
    '9c3b4180-18d9-46c2-9059-aaaa40d73118',
    NULL,
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true
  )
ON CONFLICT (id) DO UPDATE
SET
  account_id = EXCLUDED.account_id,
  identity_type = EXCLUDED.identity_type,
  user_id = EXCLUDED.user_id,
  patient_id = EXCLUDED.patient_id,
  staff_id = EXCLUDED.staff_id,
  doctor_id = EXCLUDED.doctor_id,
  clinic_id = EXCLUDED.clinic_id,
  is_primary = EXCLUDED.is_primary,
  updated_at = now();

INSERT INTO robo_auth.account_roles (
  id,
  account_id,
  role,
  clinic_id,
  is_primary,
  is_active
)
VALUES
  (
    'auth-role-patient-demo-001',
    'auth-patient-demo-001',
    'patient',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true,
    true
  ),
  (
    'auth-role-doctor-demo-001',
    'auth-doctor-demo-001',
    'doctor',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true,
    true
  ),
  (
    'auth-role-receptionist-demo-001',
    'auth-receptionist-demo-001',
    'receptionist',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true,
    true
  ),
  (
    'auth-role-clinic-admin-demo-001',
    'auth-clinic-admin-demo-001',
    'clinic_admin',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    true,
    true
  )
ON CONFLICT (id) DO UPDATE
SET
  account_id = EXCLUDED.account_id,
  role = EXCLUDED.role,
  clinic_id = EXCLUDED.clinic_id,
  is_primary = EXCLUDED.is_primary,
  is_active = EXCLUDED.is_active,
  updated_at = now();

COMMIT;
