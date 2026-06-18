-- Productization demo data patch.
--
-- MVP demo data stays in db/app/seed_mvp_demo.sql so the MVP snapshot remains
-- easy to inspect. From the productization phase onward, add demo records for
-- newly opened use cases here.
--
-- Rules:
-- - Keep statements idempotent by using UPDATE ... WHERE or INSERT ... WHERE NOT EXISTS.
-- - Add about 5 coherent records per newly opened table/use case when source data is sparse.
-- - Keep relationship fields consistent: clinic_id, patient_id, doctor_id, service_id, etc.
-- - Do not alter raw import semantics beyond demo patches needed for productization tests.
-- - Update docs/productization/DATA_PLAN.md when a new table/use case is seeded here.

BEGIN;

-- Patient visit summary demo records.
-- These rows give productization tests coherent visit/medical/vital data for
-- patient d7402d44-a12f-420b-93b9-90372a3b2e6e.

INSERT INTO robo_raw.visits (
  _excel_row_number,
  id,
  clinic_id,
  patient_id,
  appointment_id,
  doctor_id,
  visit_number,
  visit_date,
  check_in_time,
  check_out_time,
  visit_type,
  created_at,
  updated_at,
  created_by,
  updated_by,
  is_deleted
)
SELECT *
FROM (
  VALUES
    (-910001, 'prod-visit-0001-0000-0000-000000000001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '955328c2-9322-47d5-97c3-031135a075c6', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'PV-001', '2026-04-28', '2026-04-28 14:30:00+00', '2026-04-28 15:15:00+00', 'walk_in', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-910002, 'prod-visit-0002-0000-0000-000000000002', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'PV-002', '2026-05-05', '2026-05-05 09:00:00+00', '2026-05-05 09:40:00+00', 'follow_up', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-910003, 'prod-visit-0003-0000-0000-000000000003', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'PV-003', '2026-05-12', '2026-05-12 10:00:00+00', '2026-05-12 10:35:00+00', 'follow_up', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-910004, 'prod-visit-0004-0000-0000-000000000004', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'PV-004', '2026-05-19', '2026-05-19 08:30:00+00', '2026-05-19 09:05:00+00', 'follow_up', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-910005, 'prod-visit-0005-0000-0000-000000000005', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'PV-005', '2026-05-26', '2026-05-26 13:00:00+00', '2026-05-26 13:45:00+00', 'follow_up', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f')
) AS seeded(
  _excel_row_number, id, clinic_id, patient_id, appointment_id, doctor_id, visit_number,
  visit_date, check_in_time, check_out_time, visit_type, created_at, updated_at,
  created_by, updated_by, is_deleted
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.visits v WHERE v.id = seeded.id
);

INSERT INTO robo_raw.medical_records (
  _excel_row_number,
  id,
  clinic_id,
  visit_id,
  patient_id,
  doctor_id,
  status,
  chief_complaint,
  present_illness,
  examination_findings,
  confirmed_diagnosis,
  diagnosis_icd_code,
  treatment_plan,
  doctor_notes,
  follow_up_required,
  follow_up_date,
  follow_up_notes,
  finalized_at,
  finalized_by,
  schema_version,
  record_version,
  data_classification,
  created_at,
  updated_at,
  created_by,
  updated_by,
  is_deleted
)
SELECT *
FROM (
  VALUES
    (-920001, 'prod-medrec-0001-0000-0000-000000000001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0001-0000-0000-000000000001', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'completed', 'Đau đầu nhẹ', 'Bệnh nhân báo đau đầu nhẹ trong ngày.', 'Tỉnh táo, sinh hiệu ổn định.', 'Theo dõi đau đầu', 'R51', 'Uống đủ nước, nghỉ ngơi, tái khám nếu đau tăng.', 'Không ghi nhận dấu hiệu cấp cứu trong hồ sơ.', 't', '2026-05-05', 'Tái khám sau 1 tuần.', '2026-04-28 15:10:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '1', '1', 'RESTRICTED', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-920002, 'prod-medrec-0002-0000-0000-000000000002', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0002-0000-0000-000000000002', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'completed', 'Tái khám đau đầu', 'Triệu chứng giảm so với lần trước.', 'Không ghi nhận bất thường mới.', 'Theo dõi sau điều trị', 'Z09', 'Tiếp tục theo dõi, không tự ý dùng thuốc ngoài hướng dẫn.', 'Bệnh nhân đáp ứng tốt.', 't', '2026-05-12', 'Tái khám nếu triệu chứng quay lại.', '2026-05-05 09:35:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '1', '1', 'RESTRICTED', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-920003, 'prod-medrec-0003-0000-0000-000000000003', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0003-0000-0000-000000000003', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'completed', 'Mệt nhẹ', 'Bệnh nhân báo mệt nhẹ sau giờ làm.', 'Sinh hiệu trong giới hạn hồ sơ ghi nhận.', 'Tư vấn sức khỏe tổng quát', 'Z71.9', 'Theo dõi nghỉ ngơi, ăn uống đều.', 'Đã tư vấn theo dõi triệu chứng.', 'f', '', '', '2026-05-12 10:30:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '1', '1', 'RESTRICTED', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-920004, 'prod-medrec-0004-0000-0000-000000000004', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0004-0000-0000-000000000004', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'completed', 'Theo dõi huyết áp', 'Bệnh nhân đến kiểm tra định kỳ.', 'Huyết áp được ghi nhận trong sinh hiệu.', 'Theo dõi huyết áp', 'I10', 'Tiếp tục theo dõi chỉ số tại nhà.', 'Nhắc bệnh nhân ghi lại chỉ số.', 't', '2026-05-26', 'Mang theo sổ theo dõi khi tái khám.', '2026-05-19 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '1', '1', 'RESTRICTED', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-920005, 'prod-medrec-0005-0000-0000-000000000005', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0005-0000-0000-000000000005', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'completed', 'Tái khám tổng quát', 'Bệnh nhân tái khám theo lịch hẹn.', 'Không ghi nhận than phiền mới trong hồ sơ.', 'Theo dõi sau tái khám', 'Z09', 'Duy trì lịch kiểm tra định kỳ.', 'Hồ sơ ổn định theo ghi nhận.', 'f', '', '', '2026-05-26 13:40:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '1', '1', 'RESTRICTED', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f')
) AS seeded(
  _excel_row_number, id, clinic_id, visit_id, patient_id, doctor_id, status,
  chief_complaint, present_illness, examination_findings, confirmed_diagnosis,
  diagnosis_icd_code, treatment_plan, doctor_notes, follow_up_required,
  follow_up_date, follow_up_notes, finalized_at, finalized_by, schema_version,
  record_version, data_classification, created_at, updated_at, created_by,
  updated_by, is_deleted
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.medical_records mr WHERE mr.id = seeded.id
);

INSERT INTO robo_raw.vital_signs (
  _excel_row_number,
  id,
  clinic_id,
  visit_id,
  patient_id,
  recorded_at,
  recorded_by,
  blood_pressure_systolic,
  blood_pressure_diastolic,
  heart_rate,
  respiratory_rate,
  temperature_celsius,
  oxygen_saturation,
  weight_kg,
  height_cm,
  bmi,
  notes,
  ai_anomaly_detected,
  created_at,
  updated_at,
  created_by,
  updated_by,
  is_deleted
)
SELECT *
FROM (
  VALUES
    (-930001, 'prod-vital-0001-0000-0000-000000000001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0001-0000-0000-000000000001', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '2026-04-28 14:35:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '118', '76', '82', '18', '36.7', '98', '52.0', '158.0', '20.8', 'Sinh hiệu lúc check-in.', 'f', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-930002, 'prod-vital-0002-0000-0000-000000000002', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0002-0000-0000-000000000002', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '2026-05-05 09:05:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '116', '74', '78', '18', '36.6', '99', '52.2', '158.0', '20.9', 'Sinh hiệu tái khám.', 'f', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-930003, 'prod-vital-0003-0000-0000-000000000003', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0003-0000-0000-000000000003', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '2026-05-12 10:05:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '120', '78', '80', '18', '36.5', '98', '52.1', '158.0', '20.9', 'Sinh hiệu kiểm tra.', 'f', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-930004, 'prod-vital-0004-0000-0000-000000000004', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0004-0000-0000-000000000004', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '2026-05-19 08:35:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '122', '80', '84', '19', '36.8', '98', '52.3', '158.0', '20.9', 'Sinh hiệu theo dõi huyết áp.', 'f', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f'),
    (-930005, 'prod-vital-0005-0000-0000-000000000005', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'prod-visit-0005-0000-0000-000000000005', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', '2026-05-26 13:05:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '118', '75', '79', '18', '36.6', '99', '52.4', '158.0', '21.0', 'Sinh hiệu tái khám tổng quát.', 'f', '2026-06-02 09:00:00+00', '2026-06-02 09:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', 'f')
) AS seeded(
  _excel_row_number, id, clinic_id, visit_id, patient_id, recorded_at, recorded_by,
  blood_pressure_systolic, blood_pressure_diastolic, heart_rate, respiratory_rate,
  temperature_celsius, oxygen_saturation, weight_kg, height_cm, bmi, notes,
  ai_anomaly_detected, created_at, updated_at, created_by, updated_by, is_deleted
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.vital_signs vs WHERE vs.id = seeded.id
);

-- Patient billing/payment demo records.

INSERT INTO robo_raw.diagnostic_walk_in_patients (
  _excel_row_number,
  id,
  clinic_id,
  queue_number,
  status,
  patient_id,
  patient_name,
  patient_phone,
  arrival_time,
  registered_at,
  consulting_doctor_id,
  order_items,
  total_amount,
  payment_status,
  paid_amount,
  paid_at,
  cashier_id,
  invoice_number,
  payment_method,
  created_at,
  updated_at,
  currency_code
)
SELECT *
FROM (
  VALUES
    (-940001, 'prod-bill-0001-0000-0000-000000000001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'PB-001', 'paid', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'Trần Thị Bình', '+855987654321', '2026-05-01 08:00:00+00', '2026-05-01 08:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '[{"service_code":"LAB001","service_name":"Blood test","subtotal":25}]', '25.00', 'paid', '25.00', '2026-05-01 08:20:00+00', '8ce20e86-3dcf-453f-a903-7b117eff3196', 'HD-PROD-0001', 'cash', '2026-06-03 09:00:00+00', '2026-06-03 09:00:00+00', 'USD'),
    (-940002, 'prod-bill-0002-0000-0000-000000000002', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'PB-002', 'paid', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'Trần Thị Bình', '+855987654321', '2026-05-08 08:00:00+00', '2026-05-08 08:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '[{"service_code":"XR001","service_name":"Chest X-Ray","subtotal":40}]', '40.00', 'paid', '40.00', '2026-05-08 08:25:00+00', '8ce20e86-3dcf-453f-a903-7b117eff3196', 'HD-PROD-0002', 'transfer', '2026-06-03 09:00:00+00', '2026-06-03 09:00:00+00', 'USD'),
    (-940003, 'prod-bill-0003-0000-0000-000000000003', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'PB-003', 'pending_payment', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'Trần Thị Bình', '+855987654321', '2026-05-15 08:00:00+00', '2026-05-15 08:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '[{"service_code":"CT001","service_name":"CT Brain without contrast","subtotal":120000}]', '120000.00', 'unpaid', '0.00', '', '8ce20e86-3dcf-453f-a903-7b117eff3196', 'HD-PROD-0003', '', '2026-06-03 09:00:00+00', '2026-06-03 09:00:00+00', 'USD'),
    (-940004, 'prod-bill-0004-0000-0000-000000000004', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'PB-004', 'pending_payment', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'Trần Thị Bình', '+855987654321', '2026-05-22 08:00:00+00', '2026-05-22 08:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '[{"service_code":"US001","service_name":"Abdominal Ultrasound","subtotal":55000}]', '55000.00', 'partial', '20000.00', '2026-05-22 08:30:00+00', '8ce20e86-3dcf-453f-a903-7b117eff3196', 'HD-PROD-0004', 'cash', '2026-06-03 09:00:00+00', '2026-06-03 09:00:00+00', 'USD'),
    (-940005, 'prod-bill-0005-0000-0000-000000000005', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'PB-005', 'paid', 'd7402d44-a12f-420b-93b9-90372a3b2e6e', 'Trần Thị Bình', '+855987654321', '2026-05-29 08:00:00+00', '2026-05-29 08:00:00+00', 'd1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4', '[{"service_code":"LAB468","service_name":"TIBC","subtotal":6.25}]', '6.25', 'paid', '6.25', '2026-05-29 08:15:00+00', '8ce20e86-3dcf-453f-a903-7b117eff3196', 'HD-PROD-0005', 'cash', '2026-06-03 09:00:00+00', '2026-06-03 09:00:00+00', 'USD')
) AS seeded(
  _excel_row_number, id, clinic_id, queue_number, status, patient_id, patient_name,
  patient_phone, arrival_time, registered_at, consulting_doctor_id, order_items,
  total_amount, payment_status, paid_amount, paid_at, cashier_id, invoice_number,
  payment_method, created_at, updated_at, currency_code
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.diagnostic_walk_in_patients d WHERE d.id = seeded.id
);

-- Partner lab request and onsite collection demo records.
-- These rows connect partner lab workflows to the patient demo so productized
-- auth scopes can be tested without changing the original Excel export rows.

INSERT INTO robo_raw.partner_lab_requests (
  _excel_row_number,
  id,
  partner_id,
  clinic_id,
  organization_id,
  accession_number,
  barcode,
  patient_name,
  patient_phone,
  patient_dob,
  patient_gender,
  patient_id_number,
  patient_address,
  status,
  priority,
  sample_type,
  collection_method,
  clinical_notes,
  requested_at,
  confirmed_at,
  sample_collected_at,
  processing_started_at,
  completed_at,
  verified_at,
  delivered_at,
  cancelled_at,
  cancellation_reason,
  estimated_completion_at,
  total_amount,
  currency_code,
  created_at,
  created_by,
  updated_at,
  updated_by
)
SELECT *
FROM (
  VALUES
    (-950001, 'prod-plr-0001-0000-0000-000000000001', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '', 'PLR-PROD-0001', 'BC-PROD-0001', 'Trần Thị Bình', '+855987654321', '1988-04-12', 'female', '', 'Demo patient address', 'pending', 'routine', 'Máu', 'onsite_collection', 'Demo blood sample request.', '2026-06-10 08:00:00+00', '', '', '', '', '', '', '', '', '2026-06-10 17:00:00+00', '25.00', 'USD', '2026-06-10 08:00:00+00', 'system', '2026-06-10 08:00:00+00', 'system'),
    (-950002, 'prod-plr-0002-0000-0000-000000000002', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '', 'PLR-PROD-0002', 'BC-PROD-0002', 'Trần Thị Bình', '+855987654321', '1988-04-12', 'female', '', 'Demo patient address', 'confirmed', 'urgent', 'Nước tiểu', 'patient_visits', 'Demo urine request confirmed.', '2026-06-11 08:00:00+00', '2026-06-11 08:10:00+00', '', '', '', '', '', '', '', '2026-06-11 14:00:00+00', '12.50', 'USD', '2026-06-11 08:00:00+00', 'system', '2026-06-11 08:10:00+00', 'system'),
    (-950003, 'prod-plr-0003-0000-0000-000000000003', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '', 'PLR-PROD-0003', 'BC-PROD-0003', 'Trần Thị Bình', '+855987654321', '1988-04-12', 'female', '', 'Demo patient address', 'sample_collected', 'routine', 'Máu', 'onsite_collection', 'Demo sample collected.', '2026-06-12 08:00:00+00', '2026-06-12 08:05:00+00', '2026-06-12 09:15:00+00', '', '', '', '', '', '', '2026-06-12 18:00:00+00', '30.00', 'USD', '2026-06-12 08:00:00+00', 'system', '2026-06-12 09:15:00+00', 'system'),
    (-950004, 'prod-plr-0004-0000-0000-000000000004', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '', 'PLR-PROD-0004', 'BC-PROD-0004', 'Trần Thị Bình', '+855987654321', '1988-04-12', 'female', '', 'Demo patient address', 'processing', 'routine', 'Máu', 'patient_visits', 'Demo request processing.', '2026-06-13 08:00:00+00', '2026-06-13 08:05:00+00', '2026-06-13 08:30:00+00', '2026-06-13 09:00:00+00', '', '', '', '', '', '2026-06-13 16:00:00+00', '18.00', 'USD', '2026-06-13 08:00:00+00', 'system', '2026-06-13 09:00:00+00', 'system'),
    (-950005, 'prod-plr-0005-0000-0000-000000000005', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '', 'PLR-PROD-0005', 'BC-PROD-0005', 'Trần Thị Bình', '+855987654321', '1988-04-12', 'female', '', 'Demo patient address', 'completed', 'routine', 'Máu', 'patient_visits', 'Demo completed partner lab request.', '2026-06-14 08:00:00+00', '2026-06-14 08:05:00+00', '2026-06-14 08:30:00+00', '2026-06-14 09:00:00+00', '2026-06-14 11:00:00+00', '2026-06-14 11:15:00+00', '2026-06-14 12:00:00+00', '', '', '2026-06-14 12:00:00+00', '20.00', 'USD', '2026-06-14 08:00:00+00', 'system', '2026-06-14 12:00:00+00', 'system')
) AS seeded(
  _excel_row_number, id, partner_id, clinic_id, organization_id, accession_number,
  barcode, patient_name, patient_phone, patient_dob, patient_gender,
  patient_id_number, patient_address, status, priority, sample_type,
  collection_method, clinical_notes, requested_at, confirmed_at,
  sample_collected_at, processing_started_at, completed_at, verified_at,
  delivered_at, cancelled_at, cancellation_reason, estimated_completion_at,
  total_amount, currency_code, created_at, created_by, updated_at, updated_by
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.partner_lab_requests plr WHERE plr.id = seeded.id
);

INSERT INTO robo_raw.partner_onsite_collections (
  _excel_row_number,
  id,
  request_id,
  partner_id,
  clinic_id,
  collection_address,
  collection_city,
  collection_district,
  location_notes,
  contact_person,
  contact_phone,
  preferred_date,
  preferred_time_start,
  preferred_time_end,
  scheduled_at,
  assigned_collector_id,
  assigned_at,
  status,
  departed_at,
  arrived_at,
  collected_at,
  returned_to_lab_at,
  collection_notes,
  cancellation_reason,
  created_at,
  created_by,
  updated_at,
  updated_by
)
SELECT *
FROM (
  VALUES
    (-960001, 'prod-poc-0001-0000-0000-000000000001', 'prod-plr-0001-0000-0000-000000000001', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '123 Demo Street', 'Phnom Penh', 'Toul Kork', 'Call before arrival.', 'Trần Thị Bình', '+855987654321', '2026-06-10', '09:00:00', '10:00:00', '2026-06-10 09:00:00+00', '87952bb5-34c7-4b88-8bab-39b8925299aa', '2026-06-10 08:30:00+00', 'scheduled', '', '', '', '', 'Scheduled demo onsite collection.', '', '2026-06-10 08:00:00+00', 'system', '2026-06-10 08:30:00+00', 'system'),
    (-960002, 'prod-poc-0002-0000-0000-000000000002', 'prod-plr-0003-0000-0000-000000000003', 'partner-demo-001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', '123 Demo Street', 'Phnom Penh', 'Toul Kork', 'Collected at reception desk.', 'Trần Thị Bình', '+855987654321', '2026-06-12', '09:00:00', '10:00:00', '2026-06-12 09:00:00+00', '87952bb5-34c7-4b88-8bab-39b8925299aa', '2026-06-12 08:30:00+00', 'collected', '2026-06-12 08:45:00+00', '2026-06-12 09:00:00+00', '2026-06-12 09:15:00+00', '2026-06-12 09:45:00+00', 'Sample collected and returned to lab.', '', '2026-06-12 08:00:00+00', 'system', '2026-06-12 09:45:00+00', 'system')
) AS seeded(
  _excel_row_number, id, request_id, partner_id, clinic_id, collection_address,
  collection_city, collection_district, location_notes, contact_person,
  contact_phone, preferred_date, preferred_time_start, preferred_time_end,
  scheduled_at, assigned_collector_id, assigned_at, status, departed_at,
  arrived_at, collected_at, returned_to_lab_at, collection_notes,
  cancellation_reason, created_at, created_by, updated_at, updated_by
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.partner_onsite_collections poc WHERE poc.id = seeded.id
);

-- Corporate account and group examination demo records.
-- These rows make the corporate/group-health contract inspectable without
-- changing individual patient MVP data.

INSERT INTO robo_raw.crm_corporate_accounts (
  _excel_row_number,
  id,
  clinic_id,
  company_name,
  tax_code,
  address,
  city,
  phone,
  email,
  website,
  industry,
  employee_count,
  contract_count,
  total_revenue_vnd,
  notes,
  is_active,
  is_deleted,
  deleted_at,
  deleted_by,
  created_at,
  updated_at,
  created_by,
  updated_by
)
SELECT *
FROM (
  VALUES
    (-970001, 'prod-corp-0001-0000-0000-000000000001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'Mekong Textile Co., Ltd', 'MKT-001', 'No. 10, Industrial Road', 'Phnom Penh', '+85512000111', 'hr@mekong-textile.example', 'https://mekong-textile.example', 'manufacturing', '250', '2', '125000000', 'Annual employee health check demo account.', 't', 'f', '', '', '2026-06-15 08:00:00+00', '2026-06-15 08:00:00+00', 'system', 'system'),
    (-970002, 'prod-corp-0002-0000-0000-000000000002', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'Cambodia Retail Group', 'CRG-002', 'St. 271, Office Tower B', 'Phnom Penh', '+85512000222', 'benefits@crg.example', 'https://crg.example', 'retail', '480', '3', '210000000', 'Multi-branch staff screening demo account.', 't', 'f', '', '', '2026-06-15 08:00:00+00', '2026-06-15 08:00:00+00', 'system', 'system'),
    (-970003, 'prod-corp-0003-0000-0000-000000000003', '99efa33e-8a21-4b1f-a5ac-92f920e69179', 'Indica Logistics JSC', 'ILG-003', '12 Nguyen Trai', 'Ho Chi Minh', '0287000111', 'admin@indica-logistics.example', 'https://indica-logistics.example', 'logistics', '120', '1', '78000000', 'Driver health check demo account.', 't', 'f', '', '', '2026-06-15 08:00:00+00', '2026-06-15 08:00:00+00', 'system', 'system'),
    (-970004, 'prod-corp-0004-0000-0000-000000000004', 'e137130e-ce05-403d-aa63-d4d63e03699d', 'Saigon Software Lab', 'SSL-004', '45 Le Loi', 'Ho Chi Minh', '0287000222', 'people@saigon-software.example', 'https://saigon-software.example', 'technology', '85', '1', '56000000', 'Office worker wellness demo account.', 't', 'f', '', '', '2026-06-15 08:00:00+00', '2026-06-15 08:00:00+00', 'system', 'system'),
    (-970005, 'prod-corp-0005-0000-0000-000000000005', '640f49d1-dcef-4fdf-9fa2-420308e3e776', 'Phnom Penh Food Services', 'PPF-005', 'Street 2004', 'Phnom Penh', '+85512000555', 'ops@pp-food.example', 'https://pp-food.example', 'food_services', '60', '1', '32000000', 'Food handler periodic check demo account.', 't', 'f', '', '', '2026-06-15 08:00:00+00', '2026-06-15 08:00:00+00', 'system', 'system')
) AS seeded(
  _excel_row_number, id, clinic_id, company_name, tax_code, address, city,
  phone, email, website, industry, employee_count, contract_count,
  total_revenue_vnd, notes, is_active, is_deleted, deleted_at, deleted_by,
  created_at, updated_at, created_by, updated_by
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.crm_corporate_accounts ca WHERE ca.id = seeded.id
);

INSERT INTO robo_raw.group_examinations (
  _excel_row_number,
  id,
  clinic_id,
  company_name,
  company_tax_code,
  company_address,
  company_phone,
  company_email,
  contract_number,
  contract_date,
  contract_value,
  session_name,
  session_code,
  exam_date,
  expected_count,
  actual_count,
  service_package_id,
  package_name,
  package_price,
  contact_name,
  contact_phone,
  contact_email,
  payment_status,
  total_amount,
  paid_amount,
  payment_notes,
  status,
  notes,
  created_at,
  created_by,
  updated_at,
  updated_by,
  is_deleted,
  deleted_at,
  deleted_by
)
SELECT *
FROM (
  VALUES
    (-980001, 'prod-ge-0001-0000-0000-000000000001', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'Mekong Textile Co., Ltd', 'MKT-001', 'No. 10, Industrial Road', '+85512000111', 'hr@mekong-textile.example', 'GE-2026-001', '2026-06-01', '12500.00', 'Mekong Textile Annual Check 2026', 'GE-PROD-0001', '2026-07-05', '120', '0', 'd8bcd04f-799b-4391-849a-af3175048c28', 'General Health Check Up', '35.00', 'Sokha HR', '+85512000112', 'sokha.hr@mekong-textile.example', 'deposit_paid', '4200.00', '1200.00', 'Deposit received.', 'scheduled', 'Demo group examination session.', '2026-06-15 08:00:00+00', 'system', '2026-06-15 08:00:00+00', 'system', 'f', '', ''),
    (-980002, 'prod-ge-0002-0000-0000-000000000002', 'd5ac6269-d8cf-4821-ac8b-a6341e68987b', 'Cambodia Retail Group', 'CRG-002', 'St. 271, Office Tower B', '+85512000222', 'benefits@crg.example', 'GE-2026-002', '2026-06-03', '18000.00', 'Retail Group Staff Screening', 'GE-PROD-0002', '2026-07-12', '180', '0', 'a89649ec-9ae9-43da-86a5-3876753ef7e6', 'Check cholesterol levels', '18.00', 'Dara Benefits', '+85512000223', 'dara.benefits@crg.example', 'unpaid', '3240.00', '0.00', 'Awaiting company approval.', 'draft', 'Demo pending contract session.', '2026-06-15 08:00:00+00', 'system', '2026-06-15 08:00:00+00', 'system', 'f', '', ''),
    (-980003, 'prod-ge-0003-0000-0000-000000000003', '99efa33e-8a21-4b1f-a5ac-92f920e69179', 'Indica Logistics JSC', 'ILG-003', '12 Nguyen Trai', '0287000111', 'admin@indica-logistics.example', 'GE-2026-003', '2026-06-05', '6400.00', 'Driver Health Check', 'GE-PROD-0003', '2026-07-18', '80', '12', 'a9766dd9-e721-4d8b-9d37-818df4df4005', 'Fasting Blood Glucose', '8.00', 'Nguyen Admin', '0287000112', 'nguyen.admin@indica-logistics.example', 'partial', '640.00', '240.00', 'Partial payment after first group.', 'in_progress', 'Demo in-progress group examination.', '2026-06-15 08:00:00+00', 'system', '2026-06-15 08:00:00+00', 'system', 'f', '', ''),
    (-980004, 'prod-ge-0004-0000-0000-000000000004', 'e137130e-ce05-403d-aa63-d4d63e03699d', 'Saigon Software Lab', 'SSL-004', '45 Le Loi', '0287000222', 'people@saigon-software.example', 'GE-2026-004', '2026-06-07', '5100.00', 'Office Wellness Check', 'GE-PROD-0004', '2026-07-22', '85', '85', 'abb42ebb-31d2-4b60-8241-33026dcb9b26', 'Check Liver Function', '12.00', 'Tran People', '0287000223', 'tran.people@saigon-software.example', 'paid', '1020.00', '1020.00', 'Paid in full.', 'completed', 'Demo completed group examination.', '2026-06-15 08:00:00+00', 'system', '2026-06-15 08:00:00+00', 'system', 'f', '', ''),
    (-980005, 'prod-ge-0005-0000-0000-000000000005', '640f49d1-dcef-4fdf-9fa2-420308e3e776', 'Phnom Penh Food Services', 'PPF-005', 'Street 2004', '+85512000555', 'ops@pp-food.example', 'GE-2026-005', '2026-06-09', '3000.00', 'Food Handler Periodic Check', 'GE-PROD-0005', '2026-07-28', '60', '0', '0db20c7e-a107-4110-970f-4842c06517eb', 'Check for hepatitis A Virus', '10.00', 'Chan Ops', '+85512000556', 'chan.ops@pp-food.example', 'unpaid', '600.00', '0.00', 'Pending invoice.', 'scheduled', 'Demo scheduled food-service screening.', '2026-06-15 08:00:00+00', 'system', '2026-06-15 08:00:00+00', 'system', 'f', '', '')
) AS seeded(
  _excel_row_number, id, clinic_id, company_name, company_tax_code,
  company_address, company_phone, company_email, contract_number,
  contract_date, contract_value, session_name, session_code, exam_date,
  expected_count, actual_count, service_package_id, package_name,
  package_price, contact_name, contact_phone, contact_email, payment_status,
  total_amount, paid_amount, payment_notes, status, notes, created_at,
  created_by, updated_at, updated_by, is_deleted, deleted_at, deleted_by
)
WHERE NOT EXISTS (
  SELECT 1 FROM robo_raw.group_examinations ge WHERE ge.id = seeded.id
);

COMMIT;
