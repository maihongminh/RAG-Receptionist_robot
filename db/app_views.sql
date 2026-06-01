-- Clean application-facing views for the chatbot.
-- Source data stays unchanged in robo_raw.

DROP SCHEMA IF EXISTS robo_app CASCADE;
CREATE SCHEMA robo_app;

CREATE VIEW robo_app.clinics AS
SELECT
  id,
  name,
  name_short,
  phone,
  email,
  address,
  district,
  city,
  timezone,
  currency,
  locale,
  status,
  clinic_type,
  clinic_type_new,
  NULLIF(latitude, '')::numeric AS latitude,
  NULLIF(longitude, '')::numeric AS longitude
FROM robo_raw.clinics
WHERE COALESCE(is_deleted, 'f') <> 't';

CREATE VIEW robo_app.clinic_settings AS
SELECT
  id,
  clinic_id,
  timezone,
  date_format,
  time_format,
  NULLIF(working_hours_start, '')::time AS working_hours_start,
  NULLIF(working_hours_end, '')::time AS working_hours_end,
  NULLIF(lunch_break_start, '')::time AS lunch_break_start,
  NULLIF(lunch_break_end, '')::time AS lunch_break_end,
  NULLIF(appointment_slot_duration, '')::integer AS appointment_slot_duration,
  NULLIF(max_advance_booking_days, '')::integer AS max_advance_booking_days,
  CASE allow_online_booking WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS allow_online_booking,
  currency
FROM robo_raw.clinic_general_settings;

CREATE VIEW robo_app.rooms AS
SELECT
  id,
  clinic_id,
  room_code,
  room_name,
  room_type,
  floor,
  NULLIF(capacity, '')::integer AS capacity,
  CASE is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active,
  NULLIF(display_order, '')::integer AS display_order
FROM robo_raw.rooms;

CREATE VIEW robo_app.staff AS
SELECT
  id,
  clinic_id,
  full_name,
  phone,
  email,
  role,
  employee_code,
  NULLIF(date_of_birth, '')::date AS date_of_birth,
  gender,
  academic_title,
  specialty,
  sub_specialty,
  CASE
    WHEN years_of_experience ~ '^[0-9]+$' THEN years_of_experience::integer
    ELSE NULL
  END AS years_of_experience,
  license_number,
  position AS title,
  bio,
  avatar_url,
  CASE is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active
FROM robo_raw.staff;

CREATE VIEW robo_app.doctors AS
SELECT *
FROM robo_app.staff
WHERE role ILIKE '%doctor%' AND COALESCE(is_active, true) = true;

CREATE VIEW robo_app.doctor_schedules AS
SELECT
  s.id,
  s.clinic_id,
  s.doctor_id,
  d.full_name AS doctor_name,
  s.room_id,
  r.room_name,
  r.room_code,
  r.floor,
  NULLIF(s.day_of_week, '')::integer AS day_of_week,
  NULLIF(s.start_time, '')::time AS start_time,
  NULLIF(s.end_time, '')::time AS end_time,
  CASE s.is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active,
  s.notes
FROM robo_raw.doctor_schedules s
LEFT JOIN robo_app.staff d ON d.id = s.doctor_id
LEFT JOIN robo_app.rooms r ON r.id = s.room_id;

CREATE VIEW robo_app.service_categories AS
SELECT
  id,
  clinic_id,
  name,
  name_en,
  description,
  parent_id,
  NULLIF(display_order, '')::integer AS display_order,
  CASE is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active
FROM robo_raw.service_categories
WHERE COALESCE(is_deleted, 'f') <> 't';

CREATE VIEW robo_app.services AS
SELECT
  s.id,
  s.clinic_id,
  s.code,
  s.name,
  s.name_en,
  s.description,
  s.category_id,
  c.name AS category_name,
  c.name_en AS category_name_en,
  CASE
    WHEN s.price_amount ~ '^[0-9]+(\.[0-9]+)?$' THEN s.price_amount::numeric
    WHEN s.price_vnd ~ '^[0-9]+(\.[0-9]+)?$' THEN s.price_vnd::numeric
    ELSE NULL
  END AS price_amount,
  COALESCE(NULLIF(s.currency_code, ''), 'VND') AS currency_code,
  CASE
    WHEN s.duration_minutes ~ '^[0-9]+$' THEN s.duration_minutes::integer
    ELSE NULL
  END AS duration_minutes,
  s.service_type,
  CASE s.is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active,
  CASE s.requires_doctor WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS requires_doctor
FROM robo_raw.service_catalog s
LEFT JOIN robo_app.service_categories c ON c.id = s.category_id
WHERE COALESCE(s.is_deleted, 'f') <> 't';

CREATE VIEW robo_app.patients AS
SELECT
  id,
  clinic_id,
  patient_code,
  full_name,
  NULLIF(date_of_birth, '')::date AS date_of_birth,
  gender,
  id_number,
  id_type,
  phone_primary,
  phone_secondary,
  email,
  address,
  district,
  city,
  patient_category
FROM robo_raw.patients
WHERE COALESCE(is_deleted, 'f') <> 't';

CREATE VIEW robo_app.appointments AS
SELECT
  a.id,
  a.clinic_id,
  a.patient_id,
  p.full_name AS patient_name,
  p.phone_primary AS patient_phone,
  a.doctor_id,
  d.full_name AS doctor_name,
  NULLIF(a.appointment_date, '')::date AS appointment_date,
  NULLIF(a.start_time, '')::time AS start_time,
  NULLIF(a.end_time, '')::time AS end_time,
  CASE
    WHEN a.duration_minutes ~ '^[0-9]+$' THEN a.duration_minutes::integer
    ELSE NULL
  END AS duration_minutes,
  a.visit_type,
  a.status,
  a.service_id,
  sv.name AS service_name,
  a.chief_complaint,
  a.notes
FROM robo_raw.appointments a
LEFT JOIN robo_app.patients p ON p.id = a.patient_id
LEFT JOIN robo_app.staff d ON d.id = a.doctor_id
LEFT JOIN robo_app.services sv ON sv.id = a.service_id
WHERE COALESCE(a.is_deleted, 'f') <> 't';

CREATE VIEW robo_app.paraclinical_results AS
SELECT
  po.id,
  po.clinic_id,
  po.visit_id,
  po.patient_id,
  p.full_name AS patient_name,
  p.phone_primary AS patient_phone,
  po.order_type,
  po.service_id,
  po.service_code,
  COALESCE(NULLIF(po.service_name, ''), sv.name) AS service_name,
  sv.category_name AS service_category_name,
  po.status,
  po.priority,
  po.ordered_by,
  ordered_staff.full_name AS ordered_by_name,
  NULLIF(po.ordered_at, '')::timestamptz AS ordered_at,
  po.collected_by,
  collected_staff.full_name AS collected_by_name,
  NULLIF(po.collected_at, '')::timestamptz AS collected_at,
  po.processed_by,
  processed_staff.full_name AS processed_by_name,
  NULLIF(po.processed_at, '')::timestamptz AS processed_at,
  po.completed_by,
  completed_staff.full_name AS completed_by_name,
  NULLIF(po.completed_at, '')::timestamptz AS completed_at,
  po.result_summary,
  po.result_file_url,
  po.result_data,
  po.notes,
  po.ris_accession,
  po.ris_placer_line_id,
  po.walk_in_id,
  po.lis_sent_at,
  po.lis_received_at,
  po.lis_machine_code,
  po.lis_technician_code,
  po.lis_approved_by,
  po.lis_status,
  CASE
    WHEN NULLIF(po.result_summary, '') IS NOT NULL
      OR NULLIF(po.result_file_url, '') IS NOT NULL
      OR NULLIF(po.result_data, '') IS NOT NULL
    THEN true
    ELSE false
  END AS has_result
FROM robo_raw.paraclinical_orders po
LEFT JOIN robo_app.patients p ON p.id = po.patient_id
LEFT JOIN robo_app.services sv ON sv.id = po.service_id
LEFT JOIN robo_app.staff ordered_staff ON ordered_staff.id = po.ordered_by
LEFT JOIN robo_app.staff collected_staff ON collected_staff.id = po.collected_by
LEFT JOIN robo_app.staff processed_staff ON processed_staff.id = po.processed_by
LEFT JOIN robo_app.staff completed_staff ON completed_staff.id = po.completed_by
WHERE COALESCE(po.is_deleted, 'f') <> 't';

CREATE VIEW robo_app.knowledge_articles AS
SELECT
  id,
  topic,
  title,
  title_vi,
  content,
  content_vi,
  CASE is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active
FROM robo_raw.admin_help_templates
WHERE COALESCE(is_active, 't') = 't';

CREATE VIEW robo_app.patient_question_templates AS
SELECT
  id,
  category,
  question_text,
  question_text_vi,
  NULLIF(display_order, '')::integer AS display_order,
  CASE is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active
FROM robo_raw.patient_question_templates
WHERE COALESCE(is_active, 't') = 't';

CREATE TABLE robo_app.auth_accounts (
  id text PRIMARY KEY,
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  role text NOT NULL,
  user_id text,
  clinic_id text,
  patient_id text,
  doctor_id text,
  staff_id text,
  display_name text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_auth_accounts_email_lower
ON robo_app.auth_accounts (lower(email));
