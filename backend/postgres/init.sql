-- Melody Generator Database Schema

-- Countries
CREATE TABLE IF NOT EXISTS account_address_country (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Australian states
CREATE TABLE IF NOT EXISTS account_address_au_state (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES account_address_country(id) ON DELETE CASCADE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_au_state_country ON account_address_au_state(country_id);

-- Addresses
CREATE TABLE IF NOT EXISTS account_address (
    id SERIAL PRIMARY KEY,
    unit VARCHAR(50),
    street VARCHAR(255) NOT NULL,
    suburb_city VARCHAR(100) NOT NULL,
    postcode INTEGER NOT NULL,
    state_id INTEGER NOT NULL REFERENCES account_address_au_state(id) ON DELETE CASCADE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_address_state ON account_address(state_id);

-- User roles
CREATE TABLE IF NOT EXISTS account_user_role (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts
CREATE TABLE IF NOT EXISTS account (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    business_name VARCHAR(255),
    business_abn INTEGER,
    phone VARCHAR(20),
    email VARCHAR(255) NOT NULL UNIQUE,
    account_address_id INTEGER REFERENCES account_address(id) ON DELETE SET NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_account_email ON account(email);

-- Account users
CREATE TABLE IF NOT EXISTS account_user (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    role INTEGER NOT NULL REFERENCES account_user_role(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_account_user_account ON account_user(account_id);

-- Admin users
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_users(email);

-- Seed data: default roles
INSERT INTO account_user_role (slug, name) VALUES
    ('admin', 'Administrator'),
    ('user', 'Standard User')
ON CONFLICT (slug) DO NOTHING;

-- Seed data: default country
INSERT INTO account_address_country (name, active) VALUES
    ('Australia', TRUE)
ON CONFLICT DO NOTHING;

-- Generated melodies (public gallery)
CREATE TABLE IF NOT EXISTS generated_melody (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    instrument_id INTEGER NOT NULL DEFAULT 0,
    instrument_name VARCHAR(100),
    midi_file VARCHAR(255) NOT NULL,
    wav_file VARCHAR(255),
    temperature FLOAT,
    num_notes INTEGER,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_melody_created ON generated_melody(created DESC);
