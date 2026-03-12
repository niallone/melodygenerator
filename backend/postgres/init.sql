-- Melody Generator Database Schema

-- Generated melodies (public gallery)
CREATE TABLE IF NOT EXISTS generated_melody (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    instrument_id INTEGER NOT NULL DEFAULT 0,
    instrument_name VARCHAR(100),
    midi_file VARCHAR(500) NOT NULL,
    wav_file VARCHAR(500),
    temperature FLOAT CHECK (temperature > 0.0 AND temperature <= 2.0),
    num_notes INTEGER CHECK (num_notes >= 50 AND num_notes <= 2000),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_melody_created ON generated_melody(created DESC);
