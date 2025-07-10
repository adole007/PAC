-- Data export for users
-- Generated on 2025-07-09T14:20:40.244179

DELETE FROM users;

INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active, created_at, last_login) VALUES ('8cea3d86-de26-40cd-81bd-ec3975f46e20', 'clinician', 'doctor@hospital.com', 'Dr. Smith', '$2b$12$MdKw8u7f6dpo9oOl6TrJuOX3l0A0lJ3YQoD4aOZaVsu9NqepMj78O', 'clinician', 1, '2025-07-07T09:22:01', '2025-07-09T11:55:08');
INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active, created_at, last_login) VALUES ('b92b475d-f3b1-4a66-81fe-a1953c8015c4', 'admin', 'admin@hospital.com', 'Administrator', '$2b$12$MdKw8u7f6dpo9oOl6TrJuOX3l0A0lJ3YQoD4aOZaVsu9NqepMj78O', 'admin', 1, '2025-07-07T09:21:57', '2025-07-09T11:55:29');

-- 2 records exported from users

