-- Optional: insert initial data or create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- Create default admin user (admin/data608)
-- This will only run after the migrations have created the admin_users table
INSERT INTO admin_users (login, password_hash) VALUES (
    'admin',
    '$2b$12$L8gwIfmvPQnfrfJ9if0uSe2FM/uGH.SsTjpNgUG6jhfLMDRhqQZBG'
) ON CONFLICT (login) DO NOTHING;
