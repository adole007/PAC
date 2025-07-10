-- Data export for patients
-- Generated on 2025-07-09T14:20:40.251699

DELETE FROM patients;

INSERT INTO patients (id, patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, medical_record_number, primary_physician, allergies, medications, medical_history, insurance_provider, insurance_policy_number, insurance_group_number, consent_given, created_at, updated_at, created_by, last_accessed, access_log) VALUES ('7b6c0dca-c15a-4b60-bb52-12b6d8d9a70c', 'd53ba822-7cb4-4cd1-9d8b-67e7aca32ab8', 'anthony', 'Adole', '1999-11-10', 'Male', '07443069363', 'tonisworld007@outlook.com', '56 Westhaven Drive', 'MED12', 'DR TEST', '[]', '[]', '[]', 'INVS123', 'INV2', 'GROP', 1, '2025-07-08T14:21:52', '2025-07-08T14:21:52', '8cea3d86-de26-40cd-81bd-ec3975f46e20', NULL, '[]');
INSERT INTO patients (id, patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, medical_record_number, primary_physician, allergies, medications, medical_history, insurance_provider, insurance_policy_number, insurance_group_number, consent_given, created_at, updated_at, created_by, last_accessed, access_log) VALUES ('ba5bfcac-12ed-4758-b721-e581b5aaec45', 'ac4a07e0-35e1-42cd-9842-ecf667921f12', 'TEST', 'TEST1', '2010-01-07', 'Female', '07443069363', 'tonisworld007@outlook.com', '40 Leopold Street
Leopold Street', 'MED123', 'MED ', '[]', '[]', '[]', 'MEDINV', 'INV123', 'INVD', 1, '2025-07-08T14:06:53', '2025-07-08T14:06:53', 'b92b475d-f3b1-4a66-81fe-a1953c8015c4', NULL, NULL);
INSERT INTO patients (id, patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, medical_record_number, primary_physician, allergies, medications, medical_history, insurance_provider, insurance_policy_number, insurance_group_number, consent_given, created_at, updated_at, created_by, last_accessed, access_log) VALUES ('cb4acc52-7725-4aa5-b716-b1cc9b7b5927', 'f15ff5e8-2d4f-442e-be00-88582d1e04d3', 'anthony', 'Adole', '1999-01-08', 'Male', '07443069363', 'tonisworld007@outlook.com', '56 Westhaven Drive', 'PAT1', 'ads', '[]', '[]', '[]', 'ADS', 'inv', 'INVS', 1, '2025-07-08T14:15:13', '2025-07-08T14:15:13', '8cea3d86-de26-40cd-81bd-ec3975f46e20', NULL, NULL);

-- 3 records exported from patients

