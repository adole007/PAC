-- JAJUWA HEALTHCARE PAC System - MySQL Schema
-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS medical_images;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('clinician', 'admin') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Patients table
CREATE TABLE patients (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address TEXT NOT NULL,
    medical_record_number VARCHAR(50) UNIQUE NOT NULL,
    primary_physician VARCHAR(100) NOT NULL,
    allergies JSON,
    medications JSON,
    medical_history JSON,
    insurance_provider VARCHAR(100) NOT NULL,
    insurance_policy_number VARCHAR(100) NOT NULL,
    insurance_group_number VARCHAR(100),
    consent_given BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(36) NOT NULL,
    last_accessed TIMESTAMP NULL,
    access_log JSON,
    INDEX idx_patient_id (patient_id),
    INDEX idx_mrn (medical_record_number),
    INDEX idx_name (last_name, first_name),
    INDEX idx_created_by (created_by),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Medical Images table
CREATE TABLE medical_images (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    study_id VARCHAR(100) NOT NULL,
    series_id VARCHAR(100) NOT NULL,
    instance_id VARCHAR(36) NOT NULL,
    modality ENUM('CT', 'MRI', 'X-Ray', 'Ultrasound', 'PET', 'Mammography', 'Nuclear Medicine') NOT NULL,
    body_part VARCHAR(100) NOT NULL,
    study_date DATE NOT NULL,
    study_time TIME NOT NULL,
    institution_name VARCHAR(200) NOT NULL,
    referring_physician VARCHAR(100) NOT NULL,
    dicom_metadata JSON,
    image_data LONGTEXT NOT NULL,
    thumbnail_data TEXT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    image_format VARCHAR(50) NOT NULL,
    window_center FLOAT,
    window_width FLOAT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(36) NOT NULL,
    access_log JSON,
    INDEX idx_patient_id (patient_id),
    INDEX idx_study_id (study_id),
    INDEX idx_series_id (series_id),
    INDEX idx_modality (modality),
    INDEX idx_body_part (body_part),
    INDEX idx_study_date (study_date),
    INDEX idx_uploaded_by (uploaded_by),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- Audit Logs table
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    action ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'UPLOAD', 'LOGIN', 'LOGOUT') NOT NULL,
    resource_type ENUM('user', 'patient', 'medical_image', 'system') NOT NULL,
    resource_id VARCHAR(36),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    details JSON,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource_type (resource_type),
    INDEX idx_resource_id (resource_id),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX idx_patients_search ON patients(first_name, last_name, patient_id, medical_record_number);
CREATE INDEX idx_images_study ON medical_images(patient_id, study_date, modality);
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, timestamp);

-- Insert initial admin user (same password hash as before)
INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at) VALUES
('b92b475d-f3b1-4a66-81fe-a1953c8015c4', 'admin', 'admin@hospital.com', 'Administrator', '$2b$12$8K0z1yN9z2X1G1t1y0v9qO7qHsXgF8P5wJ4r6v8k3n5m9l2c7b1a9', 'admin', '2025-07-07 09:21:57'),
('8cea3d86-de26-40cd-81bd-ec3975f46e20', 'clinician', 'doctor@hospital.com', 'Dr. Smith', '$2b$12$8K0z1yN9z2X1G1t1y0v9qO7qHsXgF8P5wJ4r6v8k3n5m9l2c7b1a9', 'clinician', '2025-07-07 09:22:01');