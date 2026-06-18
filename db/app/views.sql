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

CREATE VIEW robo_app.service_rag_guides AS
WITH active_services AS (
  SELECT
    clinic_id,
    category_id,
    COALESCE(category_name, 'Uncategorized') AS category_name,
    category_name_en,
    COALESCE(service_type, 'service') AS service_type,
    name,
    duration_minutes,
    ROW_NUMBER() OVER (
      PARTITION BY clinic_id, category_id, COALESCE(service_type, 'service')
      ORDER BY name
    ) AS example_rank
  FROM robo_app.services
  WHERE COALESCE(is_active, true) = true
),
category_guides AS (
  SELECT
    clinic_id,
    category_id,
    category_name,
    category_name_en,
    service_type,
    COUNT(*)::integer AS service_count,
    MIN(duration_minutes) AS min_duration_minutes,
    MAX(duration_minutes) AS max_duration_minutes,
    STRING_AGG(name, ', ' ORDER BY name) FILTER (WHERE example_rank <= 8) AS example_services
  FROM active_services
  GROUP BY clinic_id, category_id, category_name, category_name_en, service_type
)
SELECT
  CONCAT('service-guide-', MD5(CONCAT_WS('|', clinic_id, category_id, category_name, service_type))) AS id,
  clinic_id,
  category_id,
  category_name,
  category_name_en,
  service_type,
  service_count,
  min_duration_minutes,
  max_duration_minutes,
  example_services,
  'service_guide'::text AS topic,
  CONCAT('Service guide: ', category_name) AS title,
  CONCAT('Hướng dẫn nhóm dịch vụ: ', category_name) AS title_vi,
  CONCAT(
    'Service category guide for ', category_name,
    '. Type: ', service_type,
    '. Example services: ', COALESCE(example_services, 'not available'),
    '. Use this document only to explain the service category and ask the user to clarify the exact service name. ',
    'Do not use this document to answer prices, booking status, personal results, diagnosis, or medical advice.'
  ) AS content,
  CONCAT(
    'Hướng dẫn tham khảo về nhóm dịch vụ ', category_name,
    '. Loại dịch vụ: ',
    CASE service_type
      WHEN 'lab' THEN 'xét nghiệm'
      WHEN 'imaging' THEN 'chẩn đoán hình ảnh'
      ELSE service_type
    END,
    '. Nhóm này hiện có ', service_count, ' dịch vụ trong dữ liệu.',
    ' Ví dụ dịch vụ: ', COALESCE(example_services, 'chưa có dữ liệu ví dụ'), '.',
    CASE
      WHEN min_duration_minutes IS NOT NULL AND max_duration_minutes IS NOT NULL THEN
        CONCAT(' Thời lượng tham khảo trong dữ liệu từ ', min_duration_minutes, ' đến ', max_duration_minutes, ' phút.')
      ELSE ''
    END,
    ' Tài liệu này chỉ dùng để giải thích nhóm dịch vụ và gợi ý người dùng hỏi rõ tên dịch vụ cần tra.',
    ' Không dùng tài liệu này để trả giá, đặt lịch, trả kết quả cá nhân, chẩn đoán hoặc tư vấn y khoa.'
  ) AS content_vi,
  'service_guide'::text AS document_type,
  'public'::text AS access_level,
  'vi'::text AS language,
  true AS is_active,
  NULL::text AS updated_at
FROM category_guides;

CREATE VIEW robo_app.service_lab_indicators AS
SELECT
  li.id,
  li.clinic_id,
  li.service_id,
  sv.code AS service_code,
  sv.name AS service_name,
  sv.category_id AS service_category_id,
  sv.category_name AS service_category_name,
  li.code,
  li.name,
  li.name_en,
  li.name_km,
  li.unit,
  li.reference_range_text,
  CASE
    WHEN li.reference_range_low ~ '^-?[0-9]+(\.[0-9]+)?$' THEN li.reference_range_low::numeric
    ELSE NULL
  END AS reference_range_low,
  CASE
    WHEN li.reference_range_high ~ '^-?[0-9]+(\.[0-9]+)?$' THEN li.reference_range_high::numeric
    ELSE NULL
  END AS reference_range_high,
  li.specimen_type,
  li.method,
  CASE
    WHEN li.display_order ~ '^[0-9]+$' THEN li.display_order::integer
    ELSE NULL
  END AS display_order,
  CASE li.is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active
FROM robo_raw.service_lab_indicators li
LEFT JOIN robo_app.services sv ON sv.id = li.service_id
WHERE COALESCE(li.is_deleted, 'f') <> 't';

CREATE VIEW robo_app.service_packages AS
SELECT
  sp.id,
  sp.clinic_id,
  sp.code,
  sp.name,
  sp.name_en,
  sp.name_km,
  sp.description,
  CASE
    WHEN sp.package_price_vnd ~ '^[0-9]+(\.[0-9]+)?$' THEN sp.package_price_vnd::numeric
    ELSE NULL
  END AS package_price_amount,
  CASE
    WHEN sp.original_price_vnd ~ '^[0-9]+(\.[0-9]+)?$' THEN sp.original_price_vnd::numeric
    ELSE NULL
  END AS original_price_amount,
  CASE
    WHEN sp.discount_percent ~ '^[0-9]+(\.[0-9]+)?$' THEN sp.discount_percent::numeric
    ELSE NULL
  END AS discount_percent,
  COALESCE(NULLIF(sp.currency_code, ''), 'VND') AS currency_code,
  CASE
    WHEN sp.valid_days ~ '^[0-9]+$' THEN sp.valid_days::integer
    ELSE NULL
  END AS valid_days,
  CASE
    WHEN sp.display_order ~ '^[0-9]+$' THEN sp.display_order::integer
    ELSE NULL
  END AS display_order,
  CASE sp.is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active,
  NULLIF(sp.created_at, '')::timestamptz AS created_at,
  NULLIF(sp.updated_at, '')::timestamptz AS updated_at
FROM robo_raw.service_packages sp
WHERE COALESCE(sp.is_deleted, 'f') <> 't';

CREATE VIEW robo_app.service_package_items AS
SELECT
  pi.id,
  pi.clinic_id,
  pi.package_id,
  sp.code AS package_code,
  sp.name AS package_name,
  pi.service_id,
  sv.code AS service_code,
  sv.name AS service_name,
  sv.category_id AS service_category_id,
  sv.category_name AS service_category_name,
  CASE
    WHEN pi.quantity ~ '^[0-9]+(\.[0-9]+)?$' THEN pi.quantity::numeric
    ELSE NULL
  END AS quantity,
  pi.notes,
  sv.price_amount AS service_price_amount,
  sv.currency_code AS service_currency_code,
  NULLIF(pi.created_at, '')::timestamptz AS created_at
FROM robo_raw.service_package_items pi
LEFT JOIN robo_app.service_packages sp ON sp.id = pi.package_id
LEFT JOIN robo_app.services sv ON sv.id = pi.service_id;

CREATE VIEW robo_app.icd10_codes AS
SELECT
  id,
  UPPER(REPLACE(code, '.', '')) AS code,
  name_vi,
  name_en,
  category,
  chapter,
  CASE is_active WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_active,
  CASE
    WHEN display_order ~ '^[0-9]+$' THEN display_order::integer
    ELSE NULL
  END AS display_order,
  NULLIF(created_at, '')::timestamptz AS created_at
FROM robo_raw.ref_icd10_codes
WHERE COALESCE(is_active, 't') = 't';

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

CREATE VIEW robo_app.appointment_requests AS
SELECT
  ar.id,
  ar.organization_id,
  ar.clinic_id,
  ar.source,
  ar.source_reference,
  ar.patient_info,
  NULLIF(ar.patient_info, '')::jsonb ->> 'full_name' AS patient_name,
  NULLIF(ar.patient_info, '')::jsonb ->> 'phone' AS patient_phone,
  NULLIF(ar.patient_info, '')::jsonb ->> 'gender' AS patient_gender,
  NULLIF(ar.preferred_date, '')::date AS preferred_date,
  NULLIF(ar.preferred_time_start, '')::time AS preferred_time_start,
  NULLIF(ar.preferred_time_end, '')::time AS preferred_time_end,
  CASE ar.is_flexible_time WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS is_flexible_time,
  ar.department_hint,
  ar.service_hint,
  ar.doctor_preference_id,
  d.full_name AS doctor_preference_name,
  ar.symptom_data,
  NULLIF(ar.symptom_data, '')::jsonb ->> 'chief_complaint' AS chief_complaint,
  NULLIF(ar.symptom_data, '')::jsonb ->> 'additional_notes' AS additional_notes,
  ar.ai_summary,
  ar.status,
  ar.priority,
  ar.reviewed_by,
  NULLIF(ar.reviewed_at, '')::timestamptz AS reviewed_at,
  ar.review_notes,
  ar.rejection_reason,
  ar.converted_appointment_id,
  ar.converted_patient_id,
  NULLIF(ar.converted_at, '')::timestamptz AS converted_at,
  ar.converted_by,
  NULLIF(ar.expires_at, '')::timestamptz AS expires_at,
  NULLIF(ar.created_at, '')::timestamptz AS created_at,
  NULLIF(ar.updated_at, '')::timestamptz AS updated_at,
  ar.created_by
FROM robo_raw.appointment_requests ar
LEFT JOIN robo_app.staff d ON d.id = ar.doctor_preference_id
WHERE COALESCE(ar.is_deleted, 'f') <> 't';

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

CREATE VIEW robo_app.partner_lab_requests AS
SELECT
  plr.id,
  plr.partner_id,
  plr.clinic_id,
  plr.organization_id,
  plr.accession_number,
  plr.barcode,
  matched_patient.id AS patient_id,
  matched_patient.patient_code,
  COALESCE(matched_patient.full_name, NULLIF(plr.patient_name, '')) AS patient_name,
  COALESCE(matched_patient.phone_primary, NULLIF(plr.patient_phone, '')) AS patient_phone,
  NULLIF(plr.patient_dob, '')::date AS patient_dob,
  plr.patient_gender,
  plr.patient_id_number,
  plr.patient_address,
  plr.status,
  plr.priority,
  plr.sample_type,
  plr.collection_method,
  plr.clinical_notes,
  NULLIF(plr.requested_at, '')::timestamptz AS requested_at,
  NULLIF(plr.confirmed_at, '')::timestamptz AS confirmed_at,
  NULLIF(plr.sample_collected_at, '')::timestamptz AS sample_collected_at,
  NULLIF(plr.processing_started_at, '')::timestamptz AS processing_started_at,
  NULLIF(plr.completed_at, '')::timestamptz AS completed_at,
  NULLIF(plr.verified_at, '')::timestamptz AS verified_at,
  NULLIF(plr.delivered_at, '')::timestamptz AS delivered_at,
  NULLIF(plr.cancelled_at, '')::timestamptz AS cancelled_at,
  plr.cancellation_reason,
  NULLIF(plr.estimated_completion_at, '')::timestamptz AS estimated_completion_at,
  CASE WHEN plr.total_amount ~ '^[0-9]+([.][0-9]+)?$' THEN plr.total_amount::numeric ELSE NULL END AS total_amount,
  plr.currency_code,
  NULLIF(plr.created_at, '')::timestamptz AS created_at,
  NULLIF(plr.updated_at, '')::timestamptz AS updated_at
FROM robo_raw.partner_lab_requests plr
LEFT JOIN robo_app.patients matched_patient
  ON matched_patient.clinic_id = plr.clinic_id
  AND (
    NULLIF(matched_patient.phone_primary, '') = NULLIF(plr.patient_phone, '')
    OR NULLIF(matched_patient.phone_secondary, '') = NULLIF(plr.patient_phone, '')
    OR NULLIF(matched_patient.id_number, '') = NULLIF(plr.patient_id_number, '')
  );

CREATE VIEW robo_app.partner_onsite_collections AS
SELECT
  poc.id,
  poc.request_id,
  req.accession_number,
  req.barcode,
  poc.partner_id,
  poc.clinic_id,
  req.patient_id,
  req.patient_code,
  req.patient_name,
  req.patient_phone,
  poc.collection_address,
  poc.collection_city,
  poc.collection_district,
  poc.location_notes,
  poc.contact_person,
  poc.contact_phone,
  NULLIF(poc.preferred_date, '')::date AS preferred_date,
  NULLIF(poc.preferred_time_start, '')::time AS preferred_time_start,
  NULLIF(poc.preferred_time_end, '')::time AS preferred_time_end,
  NULLIF(poc.scheduled_at, '')::timestamptz AS scheduled_at,
  poc.assigned_collector_id,
  collector.full_name AS assigned_collector_name,
  NULLIF(poc.assigned_at, '')::timestamptz AS assigned_at,
  poc.status,
  NULLIF(poc.departed_at, '')::timestamptz AS departed_at,
  NULLIF(poc.arrived_at, '')::timestamptz AS arrived_at,
  NULLIF(poc.collected_at, '')::timestamptz AS collected_at,
  NULLIF(poc.returned_to_lab_at, '')::timestamptz AS returned_to_lab_at,
  poc.collection_notes,
  poc.cancellation_reason,
  NULLIF(poc.created_at, '')::timestamptz AS created_at,
  NULLIF(poc.updated_at, '')::timestamptz AS updated_at
FROM robo_raw.partner_onsite_collections poc
LEFT JOIN robo_app.partner_lab_requests req ON req.id = poc.request_id
LEFT JOIN robo_app.staff collector ON collector.id = poc.assigned_collector_id;

CREATE VIEW robo_app.patient_visit_summaries AS
SELECT
  mr.id AS id,
  mr.id AS medical_record_id,
  mr.visit_id,
  mr.clinic_id,
  mr.patient_id,
  p.patient_code,
  p.full_name AS patient_name,
  p.phone_primary AS patient_phone,
  p.email AS patient_email,
  COALESCE(NULLIF(v.doctor_id, ''), NULLIF(mr.doctor_id, '')) AS doctor_id,
  d.full_name AS doctor_name,
  v.appointment_id,
  v.visit_number,
  NULLIF(v.visit_date, '')::date AS visit_date,
  NULLIF(v.check_in_time, '')::timestamptz AS check_in_time,
  NULLIF(v.check_out_time, '')::timestamptz AS check_out_time,
  v.visit_type,
  mr.status AS record_status,
  mr.chief_complaint,
  mr.present_illness,
  mr.examination_findings,
  mr.confirmed_diagnosis,
  mr.diagnosis_icd_code,
  mr.treatment_plan,
  mr.doctor_notes,
  CASE mr.follow_up_required WHEN 't' THEN true WHEN 'f' THEN false ELSE NULL END AS follow_up_required,
  NULLIF(mr.follow_up_date, '')::date AS follow_up_date,
  mr.follow_up_notes,
  NULLIF(mr.finalized_at, '')::timestamptz AS finalized_at,
  mr.data_classification,
  latest_vital.recorded_at AS latest_vital_recorded_at,
  latest_vital.blood_pressure_systolic,
  latest_vital.blood_pressure_diastolic,
  latest_vital.heart_rate,
  latest_vital.respiratory_rate,
  latest_vital.temperature_celsius,
  latest_vital.oxygen_saturation,
  latest_vital.weight_kg,
  latest_vital.height_cm,
  latest_vital.bmi
FROM robo_raw.medical_records mr
LEFT JOIN robo_raw.visits v
  ON v.id = mr.visit_id
  AND COALESCE(v.is_deleted, 'f') <> 't'
LEFT JOIN robo_app.patients p ON p.id = mr.patient_id
LEFT JOIN robo_app.staff d ON d.id = COALESCE(NULLIF(v.doctor_id, ''), NULLIF(mr.doctor_id, ''))
LEFT JOIN LATERAL (
  SELECT
    NULLIF(vs.recorded_at, '')::timestamptz AS recorded_at,
    CASE WHEN vs.blood_pressure_systolic ~ '^[0-9]+([.][0-9]+)?$' THEN vs.blood_pressure_systolic::numeric ELSE NULL END AS blood_pressure_systolic,
    CASE WHEN vs.blood_pressure_diastolic ~ '^[0-9]+([.][0-9]+)?$' THEN vs.blood_pressure_diastolic::numeric ELSE NULL END AS blood_pressure_diastolic,
    CASE WHEN vs.heart_rate ~ '^[0-9]+([.][0-9]+)?$' THEN vs.heart_rate::numeric ELSE NULL END AS heart_rate,
    CASE WHEN vs.respiratory_rate ~ '^[0-9]+([.][0-9]+)?$' THEN vs.respiratory_rate::numeric ELSE NULL END AS respiratory_rate,
    CASE WHEN vs.temperature_celsius ~ '^[0-9]+([.][0-9]+)?$' THEN vs.temperature_celsius::numeric ELSE NULL END AS temperature_celsius,
    CASE WHEN vs.oxygen_saturation ~ '^[0-9]+([.][0-9]+)?$' THEN vs.oxygen_saturation::numeric ELSE NULL END AS oxygen_saturation,
    CASE WHEN vs.weight_kg ~ '^[0-9]+([.][0-9]+)?$' THEN vs.weight_kg::numeric ELSE NULL END AS weight_kg,
    CASE WHEN vs.height_cm ~ '^[0-9]+([.][0-9]+)?$' THEN vs.height_cm::numeric ELSE NULL END AS height_cm,
    CASE WHEN vs.bmi ~ '^[0-9]+([.][0-9]+)?$' THEN vs.bmi::numeric ELSE NULL END AS bmi
  FROM robo_raw.vital_signs vs
  WHERE COALESCE(vs.is_deleted, 'f') <> 't'
    AND (
      NULLIF(vs.visit_id, '') = NULLIF(mr.visit_id, '')
      OR (
        NULLIF(vs.visit_id, '') IS NULL
        AND vs.patient_id = mr.patient_id
      )
    )
  ORDER BY NULLIF(vs.recorded_at, '')::timestamptz DESC NULLS LAST
  LIMIT 1
) latest_vital ON TRUE
WHERE COALESCE(mr.is_deleted, 'f') <> 't';

CREATE VIEW robo_app.billing_records AS
SELECT
  d.id,
  d.clinic_id,
  d.patient_id,
  COALESCE(p.full_name, NULLIF(d.patient_name, '')) AS patient_name,
  p.patient_code,
  COALESCE(p.phone_primary, NULLIF(d.patient_phone, '')) AS patient_phone,
  p.email AS patient_email,
  d.queue_number,
  d.status,
  NULLIF(d.registered_at, '')::timestamptz AS registered_at,
  d.invoice_number,
  d.payment_status,
  CASE WHEN d.total_amount ~ '^[0-9]+([.][0-9]+)?$' THEN d.total_amount::numeric ELSE NULL END AS total_amount,
  CASE WHEN d.paid_amount ~ '^[0-9]+([.][0-9]+)?$' THEN d.paid_amount::numeric ELSE NULL END AS paid_amount,
  (
    COALESCE(CASE WHEN d.total_amount ~ '^[0-9]+([.][0-9]+)?$' THEN d.total_amount::numeric ELSE NULL END, 0)
    - COALESCE(CASE WHEN d.paid_amount ~ '^[0-9]+([.][0-9]+)?$' THEN d.paid_amount::numeric ELSE NULL END, 0)
  ) AS balance_amount,
  NULLIF(d.paid_at, '')::timestamptz AS paid_at,
  d.payment_method,
  d.currency_code,
  d.order_items
FROM robo_raw.diagnostic_walk_in_patients d
LEFT JOIN robo_app.patients p ON p.id = d.patient_id;

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
