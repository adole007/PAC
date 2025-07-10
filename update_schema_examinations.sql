-- JAJUWA HEALTHCARE PAC System - Examination Management Schema Update
-- Add new tables for examination management

-- Create additional enum types
CREATE TYPE device_status AS ENUM ('active', 'maintenance', 'inactive');
CREATE TYPE examination_status AS ENUM ('pending', 'in_progress', 'completed', 'reported', 'archived');
CREATE TYPE examination_priority AS ENUM ('urgent', 'high', 'normal', 'low');
CREATE TYPE report_type AS ENUM ('preliminary', 'final', 'addendum');
CREATE TYPE report_status AS ENUM ('draft', 'pending', 'approved', 'signed');
CREATE TYPE technical_quality AS ENUM ('excellent', 'good', 'adequate', 'poor');

-- Devices table
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    model VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200) NOT NULL,
    device_type VARCHAR(100) NOT NULL, -- 'CT', 'MRI', 'X-Ray', 'Ultrasound', 'PET', 'SPECT', etc.
    serial_number VARCHAR(100),
    installation_date DATE,
    last_calibration DATE,
    status device_status DEFAULT 'active',
    location VARCHAR(200) NOT NULL, -- Department or room location
    specifications JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for devices table
CREATE INDEX idx_devices_name ON devices(name);
CREATE INDEX idx_devices_type ON devices(device_type);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_location ON devices(location);

-- Examinations table
CREATE TABLE examinations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL,
    examination_type VARCHAR(200) NOT NULL, -- 'CT Scan', 'MRI', 'X-Ray', 'Ultrasound', etc.
    examination_date DATE NOT NULL,
    examination_time TIME NOT NULL,
    device_id UUID NOT NULL, -- Reference to the device used
    device_name VARCHAR(200) NOT NULL, -- Device name for quick access
    referring_physician VARCHAR(200) NOT NULL,
    performing_physician VARCHAR(200) NOT NULL,
    body_part_examined VARCHAR(200) NOT NULL,
    clinical_indication TEXT NOT NULL, -- Reason for examination
    examination_protocol TEXT NOT NULL, -- Protocol used
    contrast_agent VARCHAR(200),
    contrast_amount VARCHAR(100),
    patient_position VARCHAR(100),
    radiation_dose VARCHAR(100), -- For X-ray, CT
    image_count INTEGER DEFAULT 0, -- Number of images in this examination
    status examination_status DEFAULT 'completed',
    priority examination_priority DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    access_log JSONB DEFAULT '[]'::jsonb,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Create indexes for examinations table
CREATE INDEX idx_examinations_patient_id ON examinations(patient_id);
CREATE INDEX idx_examinations_device_id ON examinations(device_id);
CREATE INDEX idx_examinations_examination_date ON examinations(examination_date);
CREATE INDEX idx_examinations_examination_type ON examinations(examination_type);
CREATE INDEX idx_examinations_body_part ON examinations(body_part_examined);
CREATE INDEX idx_examinations_status ON examinations(status);
CREATE INDEX idx_examinations_priority ON examinations(priority);
CREATE INDEX idx_examinations_created_by ON examinations(created_by);
CREATE INDEX idx_examinations_patient_date ON examinations(patient_id, examination_date DESC);

-- Examination Reports table
CREATE TABLE examination_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    examination_id UUID NOT NULL,
    report_type report_type DEFAULT 'final',
    report_status report_status DEFAULT 'draft',
    findings TEXT NOT NULL, -- Main findings
    impression TEXT NOT NULL, -- Clinical impression
    recommendations TEXT NOT NULL, -- Recommendations
    report_date DATE NOT NULL,
    report_time TIME NOT NULL,
    reporting_physician VARCHAR(200) NOT NULL,
    dictated_by VARCHAR(200),
    transcribed_by VARCHAR(200),
    verified_by VARCHAR(200),
    signed_by VARCHAR(200),
    signed_at TIMESTAMP WITH TIME ZONE,
    technical_quality technical_quality DEFAULT 'adequate',
    limitations TEXT,
    comparison_studies TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    access_log JSONB DEFAULT '[]'::jsonb,
    FOREIGN KEY (examination_id) REFERENCES examinations(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Create indexes for examination_reports table
CREATE INDEX idx_examination_reports_examination_id ON examination_reports(examination_id);
CREATE INDEX idx_examination_reports_report_type ON examination_reports(report_type);
CREATE INDEX idx_examination_reports_report_status ON examination_reports(report_status);
CREATE INDEX idx_examination_reports_report_date ON examination_reports(report_date);
CREATE INDEX idx_examination_reports_reporting_physician ON examination_reports(reporting_physician);
CREATE INDEX idx_examination_reports_created_by ON examination_reports(created_by);

-- Create trigger for updated_at timestamp on new tables
CREATE TRIGGER update_devices_updated_at 
    BEFORE UPDATE ON devices 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_examinations_updated_at 
    BEFORE UPDATE ON examinations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_examination_reports_updated_at 
    BEFORE UPDATE ON examination_reports 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample devices
INSERT INTO devices (id, name, model, manufacturer, device_type, location, specifications) VALUES
('f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid, 'CT Scanner 1', 'Revolution CT', 'GE Healthcare', 'CT', 'Radiology Department - Room 1', 
 '{"slice_thickness": "0.5mm", "max_kv": "140", "reconstruction_algorithms": ["ASIR-V", "Deep Learning"]}'::jsonb),
('6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid, 'MRI Scanner 1', 'MAGNETOM Skyra', 'Siemens Healthineers', 'MRI', 'Radiology Department - Room 2',
 '{"field_strength": "3T", "bore_diameter": "70cm", "gradients": "45 mT/m"}'::jsonb),
('6ba7b811-9dad-11d1-80b4-00c04fd430c8'::uuid, 'X-Ray Machine 1', 'DigitalDiagnost C90', 'Philips', 'X-Ray', 'Emergency Department',
 '{"detector_type": "Flat Panel", "max_kv": "150", "dose_reduction": "up to 80%"}'::jsonb),
('6ba7b812-9dad-11d1-80b4-00c04fd430c8'::uuid, 'Ultrasound 1', 'EPIQ Elite', 'Philips', 'Ultrasound', 'Cardiology Department',
 '{"probes": ["Linear", "Curved", "Phased Array"], "imaging_modes": ["2D", "3D", "4D", "Doppler"]}'::jsonb);

-- Enable Row Level Security for new tables
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE examinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE examination_reports ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for new tables
-- Devices access based on role
CREATE POLICY "Clinicians can view devices" ON devices FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);

CREATE POLICY "Admins can manage devices" ON devices FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role = 'admin'
        AND users.is_active = true
    )
);

-- Examinations access based on role
CREATE POLICY "Clinicians can view examinations" ON examinations FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);

CREATE POLICY "Clinicians can create examinations" ON examinations FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);

-- Examination reports access based on role
CREATE POLICY "Clinicians can view examination reports" ON examination_reports FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);

CREATE POLICY "Clinicians can create examination reports" ON examination_reports FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM users 
        WHERE users.id = auth.uid() 
        AND users.role IN ('clinician', 'admin')
        AND users.is_active = true
    )
);