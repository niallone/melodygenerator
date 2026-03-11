-- Melody Generator Database Schema

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
