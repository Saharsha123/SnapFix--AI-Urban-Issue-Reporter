-- ================= CREATE TABLES ================= --

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    user_type VARCHAR(20) NOT NULL DEFAULT 'citizen'
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    userId INTEGER NOT NULL,
    issueType VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    description TEXT,
    photo TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(10),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    proofImageUrl TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    tracking_id VARCHAR(30) UNIQUE,
    telegram_id BIGINT,
    primary_department VARCHAR(150),
    remarks TEXT,
    decision_source VARCHAR(50),
    probability NUMERIC(4,2),
    raw_label VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dept_admins (
    id SERIAL PRIMARY KEY,
    department VARCHAR(150) NOT NULL UNIQUE,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================= ADD NEW COLUMNS TO REPORTS ================= --

ALTER TABLE reports 
    ADD COLUMN IF NOT EXISTS assigned_dept_admin_id INTEGER REFERENCES dept_admins(id),
    ADD COLUMN IF NOT EXISTS dept_status VARCHAR(50) DEFAULT 'Not Assigned',
    ADD COLUMN IF NOT EXISTS dept_remarks TEXT;

-- ================= INSERT DEPT ADMINS ================= --

INSERT INTO dept_admins (department, username, password, email) VALUES
('Public Works Department (PWD)', 'pwd_admin', 'pwd123', 'pwd@snapfix.local'),
('BBMP – Solid Waste Management (SWM)', 'swm_admin', 'swm123', 'swm@snapfix.local'),
('BBMP – Forest / Horticulture Wing', 'forest_admin', 'forest123', 'forest@snapfix.local'),
('BESCOM (Electricity Supply Company)', 'bescom_admin', 'bescom123', 'bescom@snapfix.local'),
('Transport Department (RTO / Traffic Engineering)', 'traffic_admin', 'traffic123', 'traffic@snapfix.local')
ON CONFLICT (department) DO NOTHING;

-- ================= VERIFY ================= --

SELECT * FROM dept_admins;
SELECT COUNT(*) as total_columns FROM information_schema.columns WHERE table_name='reports';
