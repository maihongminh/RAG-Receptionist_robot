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

-- Reserved for productization demo records.
-- Current productization expansion (patient_profile_summary) uses existing
-- robo_raw.patients data, so no additional rows are required yet.

COMMIT;
