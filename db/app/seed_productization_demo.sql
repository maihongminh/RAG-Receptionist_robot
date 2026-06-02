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

COMMIT;
