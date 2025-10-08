-- FITREP Database Schema Initialization

-- Officers table - Basic officer information
CREATE TABLE officers (
    id SERIAL PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_initial VARCHAR(1),
    service_number VARCHAR(20) UNIQUE NOT NULL,
    current_rank VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FITREP reports table - Individual fitness reports
CREATE TABLE fitreports (
    id SERIAL PRIMARY KEY,
    officer_id INTEGER REFERENCES officers(id) ON DELETE CASCADE,
    fitrep_id VARCHAR(50) NOT NULL, -- FITREP ID from form
    report_date DATE NOT NULL,
    period_from DATE,  -- Made nullable as extractor may not always provide this
    period_to DATE NOT NULL,
    rank_at_time VARCHAR(20) NOT NULL,
    organization VARCHAR(200),
    reporting_senior_name VARCHAR(100),
    reporting_senior_rank VARCHAR(20),
    reviewing_officer_name VARCHAR(100),
    reviewing_officer_rank VARCHAR(20),
    occasion_type VARCHAR(10) NOT NULL, -- AN, OCC, etc
    fra_score DECIMAL(3,2), -- Calculated FITREP Average
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trait scores table - Individual A-H scores for each trait
CREATE TABLE trait_scores (
    id SERIAL PRIMARY KEY,
    fitrep_id INTEGER REFERENCES fitreports(id) ON DELETE CASCADE,
    trait_name VARCHAR(50) NOT NULL,
    trait_order INTEGER NOT NULL, -- 1-14 for the 14 traits
    score_letter VARCHAR(1), -- A, B, C, D, E, F, G, H
    score_numeric INTEGER, -- 1-7, NULL for H (non-observed)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relative values table - RV calculations with historical tracking
CREATE TABLE relative_values (
    id SERIAL PRIMARY KEY,
    fitrep_id INTEGER REFERENCES fitreports(id) ON DELETE CASCADE,
    rank VARCHAR(20) NOT NULL,
    reporting_senior VARCHAR(100) NOT NULL,
    relative_value INTEGER, -- 80-100 RV score
    total_reports_for_rank INTEGER NOT NULL, -- How many reports RS has written for this rank
    highest_fra_for_rank DECIMAL(3,2), -- RV 100 score
    average_fra_for_rank DECIMAL(3,2), -- RV 90 score
    minimum_fra_for_rank DECIMAL(3,2), -- RV 80 score
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Profiles table - Aggregated data by reporting senior and rank for quick analysis
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    reporting_senior_id INTEGER REFERENCES officers(id) ON DELETE CASCADE,
    reporting_senior_name VARCHAR(100) NOT NULL,
    rank VARCHAR(20) NOT NULL,
    total_reports INTEGER NOT NULL,
    average_fra DECIMAL(3,2),
    highest_fra DECIMAL(3,2),
    lowest_fra DECIMAL(3,2),
    average_rv DECIMAL(3,2),
    highest_rv INTEGER,
    lowest_rv INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reporting_senior_id, rank)
);

-- Scoring sessions table - Track "what-if" scenarios
CREATE TABLE scoring_sessions (
    id SERIAL PRIMARY KEY,
    officer_id INTEGER REFERENCES officers(id) ON DELETE CASCADE,
    session_name VARCHAR(200),
    scenario_data JSONB, -- Store proposed reports and their scores
    predicted_impact JSONB, -- Store calculated impact on profile
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_fitreports_officer_id ON fitreports(officer_id);
CREATE INDEX idx_fitreports_rank_date ON fitreports(rank_at_time, report_date);
CREATE INDEX idx_trait_scores_fitrep_id ON trait_scores(fitrep_id);
CREATE INDEX idx_relative_values_rank_rs ON relative_values(rank, reporting_senior);
CREATE INDEX idx_profiles_rs_rank ON profiles(reporting_senior_id, rank);

-- Insert sample data for testing
-- Removed default DOE officer insert - officers are created during FITREP upload

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update timestamps
CREATE TRIGGER update_officers_updated_at BEFORE UPDATE ON officers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fitreports_updated_at BEFORE UPDATE ON fitreports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();