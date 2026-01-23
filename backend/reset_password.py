#!/usr/bin/env python3
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
new_hash = pwd.hash('Admin2026!')

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://crm:crm@localhost:5432/crm')
engine = create_engine(DATABASE_URL.replace('+asyncpg', ''))

with engine.connect() as conn:
    result = conn.execute(text("UPDATE users SET password_hash = :hash WHERE email = 'admin@innexar.app' RETURNING id, email"))
    conn.commit()
    for row in result:
        print(f"Updated user: {row}")
    print("Password reset to: Admin2026!")
