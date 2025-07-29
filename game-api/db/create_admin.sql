-- Create default admin user
-- Username: admin
-- Password: data608

-- First, let's create the admin_users table if it doesn't exist
-- (This should be handled by migrations, but including for safety)
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    login VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL
);

-- Insert default admin user with hashed password for 'data608'
-- Using bcrypt hash for password 'data608' (cost factor 12)
INSERT INTO admin_users (login, password_hash) VALUES (
    'admin',
    '$2b$12$L8gwIfmvPQnfrfJ9if0uSe2FM/uGH.SsTjpNgUG6jhfLMDRhqQZBG'
) ON CONFLICT (login) DO NOTHING;

-- Note: The password hash above is for 'data608'
-- Generated using bcrypt with cost factor 12
-- In production, this should be changed immediately after setup
