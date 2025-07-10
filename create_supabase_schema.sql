-- JAJUWA HEALTHCARE PAC System - PostgreSQL Schema for Supabase
-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS medical_images CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop existing types if they exist
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS patient_gender CASCADE;
DROP TYPE IF EXISTS image_modality CASCADE;
DROP TYPE IF EXISTS audit_action CASCADE;
DROP TYPE IF EXISTS audit_resource CASCADE;

-- Create custom enum types for PostgreSQL
CREATE TYPE user_role AS ENUM ('clinician', 'admin');
CREATE TYPE patient_gender AS ENUM ('Male', 'Female', 'Other');
CREATE TYPE image_modality AS ENUM ('CT', 'MRI', 'X-Ray', 'Ultrasound', 'PET', 'Mammography', 'Nuclear Medicine');
CREATE TYPE audit_action AS ENUM ('CREATE', 'READ', 'UPDATE', 'DELETE', 'UPLOAD', 'LOGIN', 'LOGOUT');
CREATE TYPE audit_resource AS ENUM ('user', 'patient', 'medical_image', 'system');

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE NULL
);

-- Create indexes for users table
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender patient_gender NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address TEXT NOT NULL,
    medical_record_number VARCHAR(50) UNIQUE NOT NULL,
    primary_physician VARCHAR(100) NOT NULL,
    allergies JSONB DEFAULT '[]'::jsonb,
    medications JSONB DEFAULT '[]'::jsonb,
    medical_history JSONB DEFAULT '[]'::jsonb,
    insurance_provider VARCHAR(100) NOT NULL,
    insurance_policy_number VARCHAR(100) NOT NULL,
    insurance_group_number VARCHAR(100),
    consent_given BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE NULL,
    access_log JSONB DEFAULT '[]'::jsonb,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Create indexes for patients table
CREATE INDEX idx_patients_patient_id ON patients(patient_id);
CREATE INDEX idx_patients_mrn ON patients(medical_record_number);
CREATE INDEX idx_patients_name ON patients(last_name, first_name);
CREATE INDEX idx_patients_created_by ON patients(created_by);
CREATE INDEX idx_patients_search ON patients(first_name, last_name, patient_id, medical_record_number);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patients_updated_at 
    BEFORE UPDATE ON patients 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Medical Images table
CREATE TABLE medical_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL,
    study_id VARCHAR(100) NOT NULL,
    series_id VARCHAR(100) NOT NULL,
    instance_id UUID NOT NULL,
    modality image_modality NOT NULL,
    body_part VARCHAR(100) NOT NULL,
    study_date DATE NOT NULL,
    study_time TIME NOT NULL,
    institution_name VARCHAR(200) NOT NULL,
    referring_physician VARCHAR(100) NOT NULL,
    dicom_metadata JSONB DEFAULT '{}'::jsonb,
    image_data TEXT NOT NULL,
    thumbnail_data TEXT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    image_format VARCHAR(50) NOT NULL,
    window_center REAL,
    window_width REAL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by UUID NOT NULL,
    access_log JSONB DEFAULT '[]'::jsonb,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- Create indexes for medical_images table
CREATE INDEX idx_medical_images_patient_id ON medical_images(patient_id);
CREATE INDEX idx_medical_images_study_id ON medical_images(study_id);
CREATE INDEX idx_medical_images_series_id ON medical_images(series_id);
CREATE INDEX idx_medical_images_modality ON medical_images(modality);
CREATE INDEX idx_medical_images_body_part ON medical_images(body_part);
CREATE INDEX idx_medical_images_study_date ON medical_images(study_date);
CREATE INDEX idx_medical_images_uploaded_by ON medical_images(uploaded_by);
CREATE INDEX idx_medical_images_study ON medical_images(patient_id, study_date, modality);

-- Audit Logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    action audit_action NOT NULL,
    resource_type audit_resource NOT NULL,
    resource_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    details JSONB DEFAULT '{}'::jsonb,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for audit_logs table
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, timestamp);

-- Insert initial users (you'll need to update these UUIDs after creation)
INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at) VALUES
('b92b475d-f3b1-4a66-81fe-a1953c8015c4'::uuid, 'admin', 'admin@hospital.com', 'Administrator', '$2b$12$8K0z1yN9z2X1G1t1y0v9qO7qHsXgF8P5wJ4r6v8k3n5m9l2c7b1a9', 'admin', '2025-07-07 09:21:57'),
('8cea3d86-de26-40cd-81bd-ec3975f46e20'::uuid, 'clinician', 'doctor@hospital.com', 'Dr. Smith', '$2b$12$8K0z1yN9z2X1G1t1y0v9qO7qHsXgF8P5wJ4r6v8k3n5m9l2c7b1a9', 'clinician', '2025-07-07 09:22:01');

-- Enable Row Level Security (RLS) for HIPAA compliance
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (basic example - you may need to customize)
-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- Patients access based on role
CREATE POLICY "Clinicians can view patients" ON patients FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);

-- Medical images access based on role
CREATE POLICY "Clinicians can view medical images" ON medical_images FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);

-- Audit logs - only admins can view
CREATE POLICY "Admins can view audit logs" ON audit_logs FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role = 'admin'
        AND users.is_active = true
    )
);
