-- Rename chat tables to avoid conflict with existing system
-- We use ide_chat_threads and ide_chat_messages

CREATE TABLE IF NOT EXISTS ide_chat_threads (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES site_orders(id),
    title VARCHAR(200),
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_ide_chat_threads_order_id ON ide_chat_threads(order_id);

CREATE TABLE IF NOT EXISTS ide_chat_messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES ide_chat_threads(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    context_files JSON,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_ide_chat_messages_thread_id ON ide_chat_messages(thread_id);
