-- MVP demo data patch for chatbot testing.
--
-- This file is intentionally separate from schema.sql/load.sql.
-- It keeps the Excel import intact and only fills coherent demo data for
-- current MVP flows: clinic info, appointments, service lookup and lab results.

BEGIN;

-- 1) Complete public clinic profile data for active demo clinics.
UPDATE robo_raw.clinics
SET
  address = COALESCE(NULLIF(address, ''), '45 Nguyen Trai, District 1'),
  email = COALESCE(NULLIF(email, ''), 'contact@indica.example'),
  updated_at = COALESCE(NULLIF(updated_at, ''), '2026-05-22 09:00:00+00')
WHERE id = '99efa33e-8a21-4b1f-a5ac-92f920e69179';

UPDATE robo_raw.clinics
SET
  email = COALESCE(NULLIF(email, ''), 'contact@mauclinic.example'),
  updated_at = COALESCE(NULLIF(updated_at, ''), '2026-05-22 09:00:00+00')
WHERE id = 'e137130e-ce05-403d-aa63-d4d63e03699d';

UPDATE robo_raw.clinics
SET
  address = COALESCE(NULLIF(address, ''), 'No.12, Street 271, Phnom Penh'),
  city = COALESCE(NULLIF(city, ''), 'Phnom Penh'),
  updated_at = COALESCE(NULLIF(updated_at, ''), '2026-05-22 09:00:00+00')
WHERE id = '640f49d1-dcef-4fdf-9fa2-420308e3e776';

-- 2) Add missing clinic settings for active clinics that had no working hours.
INSERT INTO robo_raw.clinic_general_settings (
  _excel_row_number,
  id,
  clinic_id,
  timezone,
  date_format,
  time_format,
  working_hours_start,
  working_hours_end,
  lunch_break_start,
  lunch_break_end,
  appointment_slot_duration,
  max_advance_booking_days,
  allow_online_booking,
  require_phone_verification,
  send_appointment_reminders,
  reminder_hours_before,
  auto_cancel_no_show_minutes,
  created_at,
  updated_at,
  patient_code_prefix,
  patient_code_min_length,
  appointment_code_prefix,
  appointment_code_min_length,
  payment_code_prefix,
  payment_code_min_length,
  visit_code_prefix,
  visit_code_min_length,
  imaging_code_prefix,
  imaging_code_min_length,
  lab_code_prefix,
  lab_code_min_length,
  currency
)
SELECT
  -900101,
  '9c1a9f5a-3c2a-4fd1-b8d7-000000000101',
  '99efa33e-8a21-4b1f-a5ac-92f920e69179',
  'Asia/Ho_Chi_Minh',
  'DD/MM/YYYY',
  '24h',
  '07:30',
  '17:00',
  '12:00',
  '13:00',
  '30',
  '30',
  't',
  't',
  't',
  '24',
  '15',
  '2026-05-22 09:00:00+00',
  '2026-05-22 09:00:00+00',
  'PT',
  '5',
  'APT',
  '5',
  'PAY',
  '5',
  'VIS',
  '5',
  'IMG',
  '5',
  'LAB',
  '5',
  'VND'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.clinic_general_settings
  WHERE clinic_id = '99efa33e-8a21-4b1f-a5ac-92f920e69179'
);

INSERT INTO robo_raw.clinic_general_settings (
  _excel_row_number,
  id,
  clinic_id,
  timezone,
  date_format,
  time_format,
  working_hours_start,
  working_hours_end,
  lunch_break_start,
  lunch_break_end,
  appointment_slot_duration,
  max_advance_booking_days,
  allow_online_booking,
  require_phone_verification,
  send_appointment_reminders,
  reminder_hours_before,
  auto_cancel_no_show_minutes,
  created_at,
  updated_at,
  patient_code_prefix,
  patient_code_min_length,
  appointment_code_prefix,
  appointment_code_min_length,
  payment_code_prefix,
  payment_code_min_length,
  visit_code_prefix,
  visit_code_min_length,
  imaging_code_prefix,
  imaging_code_min_length,
  lab_code_prefix,
  lab_code_min_length,
  currency
)
SELECT
  -900102,
  '9c1a9f5a-3c2a-4fd1-b8d7-000000000102',
  'e137130e-ce05-403d-aa63-d4d63e03699d',
  'Asia/Ho_Chi_Minh',
  'DD/MM/YYYY',
  '24h',
  '08:00',
  '17:30',
  '12:00',
  '13:00',
  '30',
  '30',
  't',
  't',
  't',
  '24',
  '15',
  '2026-05-22 09:00:00+00',
  '2026-05-22 09:00:00+00',
  'PT',
  '5',
  'APT',
  '5',
  'PAY',
  '5',
  'VIS',
  '5',
  'IMG',
  '5',
  'LAB',
  '5',
  'VND'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.clinic_general_settings
  WHERE clinic_id = 'e137130e-ce05-403d-aa63-d4d63e03699d'
);

INSERT INTO robo_raw.clinic_general_settings (
  _excel_row_number,
  id,
  clinic_id,
  timezone,
  date_format,
  time_format,
  working_hours_start,
  working_hours_end,
  lunch_break_start,
  lunch_break_end,
  appointment_slot_duration,
  max_advance_booking_days,
  allow_online_booking,
  require_phone_verification,
  send_appointment_reminders,
  reminder_hours_before,
  auto_cancel_no_show_minutes,
  created_at,
  updated_at,
  patient_code_prefix,
  patient_code_min_length,
  appointment_code_prefix,
  appointment_code_min_length,
  payment_code_prefix,
  payment_code_min_length,
  visit_code_prefix,
  visit_code_min_length,
  imaging_code_prefix,
  imaging_code_min_length,
  lab_code_prefix,
  lab_code_min_length,
  currency
)
SELECT
  -900103,
  '9c1a9f5a-3c2a-4fd1-b8d7-000000000103',
  '640f49d1-dcef-4fdf-9fa2-420308e3e776',
  'Asia/Phnom_Penh',
  'DD/MM/YYYY',
  '24h',
  '08:00',
  '16:30',
  '12:00',
  '13:00',
  '30',
  '30',
  't',
  't',
  't',
  '24',
  '15',
  '2026-05-22 09:00:00+00',
  '2026-05-22 09:00:00+00',
  'PT',
  '5',
  'APT',
  '5',
  'PAY',
  '5',
  'VIS',
  '5',
  'IMG',
  '5',
  'LAB',
  '5',
  'VND'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.clinic_general_settings
  WHERE clinic_id = '640f49d1-dcef-4fdf-9fa2-420308e3e776'
);

-- 3) Add the missing demo doctor referenced by existing appointments.
INSERT INTO robo_raw.staff (
  _excel_row_number,
  id,
  clinic_id,
  full_name,
  phone,
  email,
  role,
  employee_code,
  is_active,
  academic_title,
  specialty,
  sub_specialty,
  years_of_experience,
  license_number,
  position,
  bio,
  created_at,
  updated_at
)
SELECT
  -900201,
  'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
  'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
  'Dr. MVP Demo',
  '+85510000001',
  'mvp.doctor@example.test',
  'doctor',
  'DR-MVP-001',
  't',
  'Dr.',
  'Internal Medicine',
  'General consultation',
  '8',
  'MVP-LIC-001',
  'Doctor',
  'Demo doctor used to keep MVP appointment data relationally complete.',
  '2026-05-22 09:00:00+00',
  '2026-05-22 09:00:00+00'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.staff
  WHERE id = 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4'
);

-- 4) Fill service_id on existing demo appointments where possible.
UPDATE robo_raw.appointments
SET service_id = '26e03be4-6efc-428f-88a3-5dc80f518acf'
WHERE id = '955328c2-9322-47d5-97c3-031135a075c6'
  AND COALESCE(service_id, '') = '';

UPDATE robo_raw.appointments
SET service_id = '4e7e1a3f-9190-4d7e-8949-3305585bcc49'
WHERE id = 'a5680669-86cd-4ed5-8d78-032168eba6d8'
  AND COALESCE(service_id, '') = '';

-- 5) Add future appointments for patient/doctor MVP scenarios.
INSERT INTO robo_raw.appointments (
  _excel_row_number,
  id,
  clinic_id,
  patient_id,
  doctor_id,
  appointment_date,
  start_time,
  end_time,
  duration_minutes,
  visit_type,
  status,
  service_id,
  chief_complaint,
  notes,
  confirmed_at,
  created_at,
  updated_at,
  is_deleted
)
SELECT
  -900301,
  'c9c0f8e5-6d3d-4f0f-bf7c-000000000301',
  'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
  'd7402d44-a12f-420b-93b9-90372a3b2e6e',
  'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
  '2026-05-25',
  '09:00',
  '09:30',
  '30',
  'scheduled',
  'scheduled',
  '26e03be4-6efc-428f-88a3-5dc80f518acf',
  'Follow-up for lab result review',
  'MVP demo appointment for patient schedule lookup.',
  '2026-05-22 09:05:00+00',
  '2026-05-22 09:00:00+00',
  '2026-05-22 09:00:00+00',
  'f'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.appointments
  WHERE id = 'c9c0f8e5-6d3d-4f0f-bf7c-000000000301'
);

INSERT INTO robo_raw.appointments (
  _excel_row_number,
  id,
  clinic_id,
  patient_id,
  doctor_id,
  appointment_date,
  start_time,
  end_time,
  duration_minutes,
  visit_type,
  status,
  service_id,
  chief_complaint,
  notes,
  confirmed_at,
  created_at,
  updated_at,
  is_deleted
)
SELECT
  -900302,
  'c9c0f8e5-6d3d-4f0f-bf7c-000000000302',
  'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
  'e3482173-8341-49b8-ad4c-b0ae3ec16730',
  'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
  '2026-05-25',
  '10:00',
  '10:30',
  '30',
  'scheduled',
  'scheduled',
  'd8d8d5ad-f397-4443-8afe-c785a1111058',
  'Headache follow-up',
  'MVP demo appointment for doctor schedule lookup.',
  '2026-05-22 09:05:00+00',
  '2026-05-22 09:00:00+00',
  '2026-05-22 09:00:00+00',
  'f'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.appointments
  WHERE id = 'c9c0f8e5-6d3d-4f0f-bf7c-000000000302'
);

-- 6) Add coherent lab/imaging result rows for authenticated result lookup.
INSERT INTO robo_raw.paraclinical_orders (
  _excel_row_number,
  id,
  clinic_id,
  patient_id,
  order_type,
  service_id,
  service_code,
  service_name,
  status,
  priority,
  ordered_by,
  ordered_at,
  collected_at,
  processed_at,
  completed_by,
  completed_at,
  result_summary,
  result_file_url,
  result_data,
  notes,
  created_at,
  updated_at,
  is_deleted,
  lis_status
)
SELECT
  -900401,
  '3b28fd6c-1c56-4f27-a2c4-000000000401',
  'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
  'd7402d44-a12f-420b-93b9-90372a3b2e6e',
  'lab',
  '26e03be4-6efc-428f-88a3-5dc80f518acf',
  'FBG001',
  'Glucose',
  'completed',
  'routine',
  'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
  '2026-05-21 08:30:00+00',
  '2026-05-21 08:45:00+00',
  '2026-05-21 09:20:00+00',
  '87952bb5-34c7-4b88-8bab-39b8925299aa',
  '2026-05-21 09:40:00+00',
  'Glucose 5.2 mmol/L. Result is available for physician review.',
  'https://example.test/results/glucose-d740.pdf',
  '{"glucose_mmol_l":5.2,"unit":"mmol/L","status":"available"}',
  'MVP demo completed lab result.',
  '2026-05-21 08:30:00+00',
  '2026-05-21 09:40:00+00',
  'f',
  'completed'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.paraclinical_orders
  WHERE id = '3b28fd6c-1c56-4f27-a2c4-000000000401'
);

INSERT INTO robo_raw.paraclinical_orders (
  _excel_row_number,
  id,
  clinic_id,
  patient_id,
  order_type,
  service_id,
  service_code,
  service_name,
  status,
  priority,
  ordered_by,
  ordered_at,
  collected_at,
  processed_at,
  completed_by,
  completed_at,
  result_summary,
  result_file_url,
  result_data,
  notes,
  created_at,
  updated_at,
  is_deleted,
  lis_status
)
SELECT
  -900402,
  '3b28fd6c-1c56-4f27-a2c4-000000000402',
  'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
  '75b7ebc8-a572-42d5-bc70-27a7276f2441',
  'lab',
  '4e7e1a3f-9190-4d7e-8949-3305585bcc49',
  'BLD004',
  'CBC',
  'completed',
  'routine',
  'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
  '2026-05-20 08:00:00+00',
  '2026-05-20 08:15:00+00',
  '2026-05-20 09:00:00+00',
  '87952bb5-34c7-4b88-8bab-39b8925299aa',
  '2026-05-20 09:30:00+00',
  'CBC completed. Result is available for physician review.',
  'https://example.test/results/cbc-75b7.pdf',
  '{"cbc_status":"available"}',
  'MVP demo completed CBC result.',
  '2026-05-20 08:00:00+00',
  '2026-05-20 09:30:00+00',
  'f',
  'completed'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.paraclinical_orders
  WHERE id = '3b28fd6c-1c56-4f27-a2c4-000000000402'
);

INSERT INTO robo_raw.paraclinical_orders (
  _excel_row_number,
  id,
  clinic_id,
  patient_id,
  order_type,
  service_id,
  service_code,
  service_name,
  status,
  priority,
  ordered_by,
  ordered_at,
  processed_at,
  completed_by,
  completed_at,
  result_summary,
  result_file_url,
  result_data,
  notes,
  created_at,
  updated_at,
  is_deleted
)
SELECT
  -900403,
  '3b28fd6c-1c56-4f27-a2c4-000000000403',
  'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
  'e3482173-8341-49b8-ad4c-b0ae3ec16730',
  'imaging',
  'd8d8d5ad-f397-4443-8afe-c785a1111058',
  'CT001',
  'CT Brain without contrast',
  'completed',
  'routine',
  'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
  '2026-05-19 10:00:00+00',
  '2026-05-19 10:40:00+00',
  'f726e781-03bf-4eb2-9cf6-8a628f6badf6',
  '2026-05-19 11:00:00+00',
  'CT Brain without contrast completed. Report is available for physician review.',
  'https://example.test/results/ct-e348.pdf',
  '{"imaging_status":"available"}',
  'MVP demo imaging result.',
  '2026-05-19 10:00:00+00',
  '2026-05-19 11:00:00+00',
  'f'
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.paraclinical_orders
  WHERE id = '3b28fd6c-1c56-4f27-a2c4-000000000403'
);

-- 6) Demo auth accounts for real email/password login.
-- Password for all accounts below: demo123
INSERT INTO robo_app.auth_accounts (
  id,
  email,
  password_hash,
  role,
  user_id,
  clinic_id,
  patient_id,
  doctor_id,
  staff_id,
  display_name,
  is_active
)
VALUES
  (
    'auth-patient-demo-001',
    'patient.demo@robo.local',
    'pbkdf2_sha256$260000$patient-demo-salt$apjsX0RTRBwqdEdt33iocDwV1IvCZCRrHvTyd6vkeM4',
    'patient',
    'd7402d44-a12f-420b-93b9-90372a3b2e6e',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    'd7402d44-a12f-420b-93b9-90372a3b2e6e',
    NULL,
    NULL,
    'Trần Thị Bình',
    true
  ),
  (
    'auth-doctor-demo-001',
    'doctor@clinic.local',
    'pbkdf2_sha256$260000$doctor-demo-salt$XZgOBja8alI6e497oLK98eZ_4gf5pTVsJRn4RLIvZ_Y',
    'doctor',
    'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    NULL,
    'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
    'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4',
    'Dr. MVP Demo',
    true
  ),
  (
    'auth-receptionist-demo-001',
    'receptionist@clinic.local',
    'pbkdf2_sha256$260000$receptionist-demo-salt$ngveihVdxS9QN3EfzvKxNTJH7sRQ3kx11RWIWeDvfk8',
    'receptionist',
    'cad02e6c-fb13-4f5f-869d-a97d07491c26',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    NULL,
    NULL,
    'cad02e6c-fb13-4f5f-869d-a97d07491c26',
    'Receptionist Le Minh C',
    true
  ),
  (
    'auth-clinic-admin-demo-001',
    'admin@clinic.local',
    'pbkdf2_sha256$260000$admin-demo-salt$dlK8eenUlYi56QqyD5vXdoTdnaA_P-ghwdYg4DexZmY',
    'clinic_admin',
    '9c3b4180-18d9-46c2-9059-aaaa40d73118',
    'd5ac6269-d8cf-4821-ac8b-a6341e68987b',
    NULL,
    NULL,
    '9c3b4180-18d9-46c2-9059-aaaa40d73118',
    'Clinic Admin Nguyen Van F',
    true
  )
ON CONFLICT (email) DO UPDATE
SET
  password_hash = EXCLUDED.password_hash,
  role = EXCLUDED.role,
  user_id = EXCLUDED.user_id,
  clinic_id = EXCLUDED.clinic_id,
  patient_id = EXCLUDED.patient_id,
  doctor_id = EXCLUDED.doctor_id,
  staff_id = EXCLUDED.staff_id,
  display_name = EXCLUDED.display_name,
  is_active = EXCLUDED.is_active,
  updated_at = now();

COMMIT;
