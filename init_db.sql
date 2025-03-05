-- Elimina tabelle obsolete (se esistono)
DROP TABLE IF EXISTS chat_history;

-- Crea nuove tabelle
CREATE TABLE IF NOT EXISTS chat_sessions (
    user_id BIGINT PRIMARY KEY,
    history JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS message_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per ottimizzazione
CREATE INDEX idx_user_id ON message_history(user_id);