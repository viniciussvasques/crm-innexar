-- Migration: Add Site Generation Logs and Chat tables

CREATE TABLE IF NOT EXISTS site_generation_logs (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES site_orders(id),
    step VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'info',
    details JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_site_generation_logs_order_id ON site_generation_logs(order_id);

CREATE TABLE IF NOT EXISTS chat_threads (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES site_orders(id),
    title VARCHAR(200),
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_chat_threads_order_id ON chat_threads(order_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES chat_threads(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    context_files JSON,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_chat_messages_thread_id ON chat_messages(thread_id);
